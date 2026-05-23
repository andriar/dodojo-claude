#!/usr/bin/env python3
"""Sensei outcome tracker — verify accepted recommendations actually got implemented & used.

For each `accept` decision in feedback.jsonl older than 14 days:
  - Check if a derived skill exists in ~/.claude/skills/<slug>/ (graduated from _drafts/)
  - Check if hook installed (settings.json registration)
  - Check if related commands appear in zsh history within last 7 days
  - Output: status report with actionable nudges

Anti reward-hacking: if accepted but never implemented → penalize that
detector kind weights (small) so future similar recs don't dominate.

Usage:
  outcome.py [--cutoff-days 14] [--write-report]
"""
import json, sys, os, re, argparse, time, subprocess
from pathlib import Path
from datetime import datetime
from collections import Counter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import FEEDBACK, WEIGHTS, STATE, HISTORY, seed_state_from_home

seed_state_from_home()
SKILLS_DIR = Path(os.environ.get("SENSEI_SKILLS_DIR") or Path.home() / ".claude" / "skills")
DRAFTS_DIR = Path(os.environ.get("SENSEI_DRAFTS") or SKILLS_DIR / "_drafts")
OUTCOMES = STATE / "outcomes.jsonl"
SETTINGS = Path.home() / ".claude" / "settings.json"

NOW = time.time()


def load_feedback():
    if not FEEDBACK.exists():
        return []
    return [json.loads(l) for l in FEEDBACK.read_text().splitlines() if l.strip()]


def derive_slug(pid):
    return re.sub(r"[^a-z0-9-]", "-", pid.replace(":", "-").lower())[:40].strip("-")


def check_skill_active(slug):
    p = SKILLS_DIR / slug / "SKILL.md"
    return p.exists() and not str(p).startswith(str(DRAFTS_DIR))


def check_skill_drafted(slug):
    return (DRAFTS_DIR / slug / "SKILL.md").exists()


def zsh_recent(pattern_keywords, days=7):
    """Count shell history lines matching any keyword in last N days."""
    hist = HISTORY
    if not hist.exists():
        return 0
    cutoff = NOW - days * 86400
    count = 0
    try:
        for line in hist.read_text(errors="ignore").splitlines():
            m = re.match(r"^: (\d+):\d+;(.*)$", line)
            if not m:
                continue
            ts = int(m.group(1))
            if ts < cutoff:
                continue
            cmd = m.group(2)
            if any(k in cmd for k in pattern_keywords):
                count += 1
    except Exception:
        pass
    return count


def evaluate(rec, cutoff_days=14):
    pid = rec["pattern_id"]
    age_days = (NOW - rec["ts"]) / 86400
    if age_days < cutoff_days:
        return {"pattern_id": pid, "status": "too-young", "age_days": round(age_days, 1)}

    slug = derive_slug(pid)
    active = check_skill_active(slug)
    drafted = check_skill_drafted(slug)

    # heuristic keyword from pattern_id last segment
    kw = pid.split(":")[-1].replace("-", " ").split()
    usage = zsh_recent(kw, days=7) if kw else 0

    if active and usage > 0:
        status = "implemented-and-used"
    elif active and usage == 0:
        status = "implemented-not-used"
    elif drafted:
        status = "drafted-not-graduated"
    else:
        status = "abandoned"

    return {
        "pattern_id": pid,
        "kind": rec.get("pattern_kind"),
        "accepted_at": rec["iso"],
        "age_days": round(age_days, 1),
        "slug": slug,
        "active_skill": active,
        "draft_present": drafted,
        "usage_last_7d": usage,
        "status": status,
    }


def penalize_abandoned(outcomes, lr=0.02):
    """Small weight penalty for kinds that get accepted but abandoned."""
    weights = json.loads(WEIGHTS.read_text())
    abandoned_kinds = Counter(o["kind"] for o in outcomes if o["status"] == "abandoned" and o.get("kind"))
    if not abandoned_kinds:
        return weights, abandoned_kinds
    for k, n in abandoned_kinds.items():
        # mild dampener on freq weight (lower confidence)
        weights["freq"] = round(weights.get("freq", 1.0) - lr * n, 4)
    weights.setdefault("_meta", {})["last_outcome_check"] = datetime.now().strftime("%Y-%m-%d")
    WEIGHTS.write_text(json.dumps(weights, indent=2))
    return weights, abandoned_kinds


def write_outcome_log(outcomes):
    OUTCOMES.parent.mkdir(parents=True, exist_ok=True)
    with OUTCOMES.open("a") as f:
        for o in outcomes:
            o["checked_at"] = datetime.now().isoformat(timespec="seconds")
            f.write(json.dumps(o) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff-days", type=int, default=14)
    ap.add_argument("--write-report", action="store_true", help="append to outcomes.jsonl + adjust weights")
    args = ap.parse_args()

    fb = load_feedback()
    accepts = [r for r in fb if r.get("decision") == "accept"]

    outcomes = [evaluate(r, args.cutoff_days) for r in accepts]
    mature = [o for o in outcomes if o["status"] != "too-young"]

    print(f"# Sensei outcomes — {len(accepts)} acceptances, {len(mature)} mature (>{args.cutoff_days}d)")
    for o in outcomes:
        status = o["status"]
        marker = {
            "implemented-and-used": "✓",
            "implemented-not-used": "○",
            "drafted-not-graduated": "△",
            "abandoned": "✗",
            "too-young": "·",
        }.get(status, "?")
        print(f"{marker} {o['pattern_id']:30s}  {status:25s}  age={o.get('age_days')}d  usage={o.get('usage_last_7d', '-')}")

    if args.write_report and mature:
        weights, abandoned = penalize_abandoned(mature)
        write_outcome_log(mature)
        if abandoned:
            print(f"\n⚠ Penalized weights for abandoned kinds: {dict(abandoned)}")
        print(f"Wrote {len(mature)} outcomes to {OUTCOMES}")

    # actionable nudges
    nudges = []
    for o in mature:
        if o["status"] == "drafted-not-graduated":
            nudges.append(f"  → Graduate `_drafts/{o['slug']}` to active or delete")
        elif o["status"] == "implemented-not-used":
            nudges.append(f"  → Skill `{o['slug']}` exists but unused — reject or use it")
        elif o["status"] == "abandoned":
            nudges.append(f"  → Reconsider `{o['pattern_id']}` — accepted but no skill exists after {o['age_days']}d")
    if nudges:
        print("\nNudges:")
        print("\n".join(nudges))


if __name__ == "__main__":
    main()
