#!/usr/bin/env python3
"""Sensei decision logger + weight tuner.

Usage:
  decide.py accept <pattern_id> [--note "..."]
  decide.py reject <pattern_id> --reason "..."
  decide.py later  <pattern_id>
  decide.py weights              # show current
  decide.py rules                # show detector rule status (enabled/disabled)
  decide.py history [--limit N]  # tail feedback log

On accept/reject:
  1. Append JSON line to state/feedback.jsonl
  2. Reload latest scored pattern (state/last_scored.json) to know features
  3. Gradient nudge weights toward (accept) or away (reject) from dominant features
  4. Detector rule auto-disable: if same `kind` rejected 3+ times, disable in state/rules.json
  5. On accept: write skeleton to ~/.claude/skills/_drafts/<derived-name>/SKILL.md (L3)
"""
import json, sys, os, time, argparse, re
from pathlib import Path
from datetime import datetime
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import WEIGHTS, FEEDBACK, LAST_SCORED, RULES, seed_state_from_home

seed_state_from_home()
DRAFTS = Path(os.environ.get("SENSEI_DRAFTS") or Path.home() / ".claude" / "skills" / "_drafts")

LR = 0.05  # learning rate for weight nudge
REJECT_DISABLE_THRESHOLD = 3


def load_json(p, default):
    return json.loads(p.read_text()) if p.exists() else default


def save_json(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def find_pattern(pid):
    data = load_json(LAST_SCORED, {"patterns": []})
    for p in data["patterns"]:
        if p["id"] == pid:
            return p
    return None


def append_feedback(decision, pid, pattern, **extra):
    rec = {
        "ts": int(time.time()),
        "iso": datetime.now().isoformat(timespec="seconds"),
        "decision": decision,
        "pattern_id": pid,
        "pattern_kind": pattern.get("kind") if pattern else None,
        "pattern_score": pattern.get("score") if pattern else None,
        **extra,
    }
    FEEDBACK.parent.mkdir(parents=True, exist_ok=True)
    with FEEDBACK.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def nudge_weights(pattern, sign):
    """sign=+1 on accept, -1 on reject. Boost dimensions where pattern scored high."""
    w = load_json(WEIGHTS, {})
    feats = {
        "freq": pattern.get("freq", 0),
        "time_per_run_sec": pattern.get("est_time_sec", 0),
        "recency_days": 1.0,
        "effort_to_automate_hours": pattern.get("est_effort_hours", 0),
    }
    # normalize feature magnitudes for stable nudge
    norm = max(feats.values()) or 1
    for k, v in feats.items():
        if k in w:
            delta = sign * LR * (v / norm)
            w[k] = round(w[k] + delta, 4)
    w.setdefault("_meta", {})["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    save_json(WEIGHTS, w)
    return w


def check_rule_disable(kind):
    """If same kind rejected REJECT_DISABLE_THRESHOLD times → disable."""
    if not FEEDBACK.exists():
        return None
    rejects = [json.loads(l) for l in FEEDBACK.read_text().splitlines()
               if l.strip() and json.loads(l).get("decision") == "reject"]
    same_kind = [r for r in rejects if r.get("pattern_kind") == kind]
    if len(same_kind) < REJECT_DISABLE_THRESHOLD:
        return None
    rules = load_json(RULES, {"disabled": []})
    if kind in rules["disabled"]:
        return None
    rules["disabled"].append(kind)
    rules.setdefault("_log", []).append({
        "kind": kind, "disabled_at": datetime.now().isoformat(timespec="seconds"),
        "reason": f"{len(same_kind)} rejections"
    })
    save_json(RULES, rules)
    return kind


def derive_skill_name(pattern):
    """Generate slug from pattern id."""
    raw = pattern["id"].replace(":", "-")
    slug = re.sub(r"[^a-z0-9-]", "-", raw.lower())[:40].strip("-")
    return slug or "sensei-proposed"


def draft_skill(pattern):
    """L3: write SKILL.md skeleton to _drafts/."""
    name = derive_skill_name(pattern)
    target = DRAFTS / name
    target.mkdir(parents=True, exist_ok=True)
    skill_md = target / "SKILL.md"
    if skill_md.exists():
        return None  # don't clobber
    content = f"""---
name: {name}
description: (DRAFT — proposed by Sensei) {pattern['suggestion']}
domain: general
category: generate
sensei_origin:
  pattern_id: {pattern['id']}
  proposed_at: {datetime.now().strftime('%Y-%m-%d')}
  score: {pattern.get('score')}
---

# {name}

**Status**: DRAFT — proposed automatically by Sensei. Review and move to `~/.claude/skills/{name}/` to activate.

## Why proposed
- Pattern ID: `{pattern['id']}`
- Kind: {pattern.get('kind')}
- Frequency: {pattern.get('freq')} occurrences
- Est. time per run: {pattern.get('est_time_sec')}s
- Est. automation effort: {pattern.get('est_effort_hours')}h

## Samples
{chr(10).join(f'- `{s}`' for s in pattern.get('samples', []))}

## Proposed implementation

TODO: human writes the actual logic. Sensei provides scaffold only.

## Activation checklist

- [ ] Replace this TODO with implementation
- [ ] Verify `domain` + `category` frontmatter accurate
- [ ] Move dir from `_drafts/` to `~/.claude/skills/`
- [ ] Add row to `~/.claude/skills/README.md`
"""
    skill_md.write_text(content)
    return skill_md


def cmd_accept(args):
    p = find_pattern(args.pattern_id)
    if not p:
        print(f"Unknown pattern_id: {args.pattern_id}. Run report.py first or check state/last_scored.json.", file=sys.stderr)
        sys.exit(1)
    rec = append_feedback("accept", args.pattern_id, p, note=args.note)
    w = nudge_weights(p, +1)
    draft_path = draft_skill(p)
    print(f"✓ Accepted {args.pattern_id}")
    print(f"  weights nudged (+) — saved to {WEIGHTS}")
    if draft_path:
        print(f"  skill skeleton drafted: {draft_path}")
        print(f"  → review, implement, move to ~/.claude/skills/")
    else:
        print(f"  skill skeleton already exists or could not be drafted")


def cmd_reject(args):
    p = find_pattern(args.pattern_id)
    if not p:
        print(f"Unknown pattern_id: {args.pattern_id}", file=sys.stderr)
        sys.exit(1)
    rec = append_feedback("reject", args.pattern_id, p, reason=args.reason)
    w = nudge_weights(p, -1)
    disabled = check_rule_disable(p.get("kind"))
    print(f"✗ Rejected {args.pattern_id} — {args.reason}")
    print(f"  weights nudged (−)")
    if disabled:
        print(f"  ⚠ detector kind `{disabled}` auto-disabled (rejected 3+ times)")


def cmd_later(args):
    p = find_pattern(args.pattern_id)
    if not p:
        print(f"Unknown pattern_id: {args.pattern_id}", file=sys.stderr)
        sys.exit(1)
    append_feedback("later", args.pattern_id, p)
    print(f"⏳ Deferred {args.pattern_id}")


def cmd_weights(args):
    print(json.dumps(load_json(WEIGHTS, {}), indent=2))


def cmd_rules(args):
    rules = load_json(RULES, {"disabled": []})
    print(json.dumps(rules, indent=2))


def cmd_history(args):
    if not FEEDBACK.exists():
        print("(no feedback yet)")
        return
    lines = FEEDBACK.read_text().splitlines()[-args.limit:]
    for l in lines:
        if l.strip():
            r = json.loads(l)
            print(f"{r['iso']}  {r['decision']:7s}  {r['pattern_id']}  ({r.get('reason') or r.get('note') or ''})")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("accept"); pa.add_argument("pattern_id"); pa.add_argument("--note", default="")
    pa.set_defaults(func=cmd_accept)

    pr = sub.add_parser("reject"); pr.add_argument("pattern_id"); pr.add_argument("--reason", required=True)
    pr.set_defaults(func=cmd_reject)

    pl = sub.add_parser("later"); pl.add_argument("pattern_id")
    pl.set_defaults(func=cmd_later)

    sub.add_parser("weights").set_defaults(func=cmd_weights)
    sub.add_parser("rules").set_defaults(func=cmd_rules)
    ph = sub.add_parser("history"); ph.add_argument("--limit", type=int, default=20)
    ph.set_defaults(func=cmd_history)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
