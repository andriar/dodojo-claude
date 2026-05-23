#!/usr/bin/env python3
"""Sensei scorer — detect repetitive patterns from raw.tsv, rank by ROI.

Input: ~/.claude/skills/sensei/state/raw.tsv (TSV: ts, source, data...)
Output: stdout JSON {patterns: [...]} sorted by score desc.

ROI = w_freq*log(freq+1) + w_time*est_time + w_recency*recency_factor - w_effort*est_effort
Weights from state/weights.json. Tunable via feedback loop.
"""
import json, re, sys, os, time, math
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import RAW, WEIGHTS, PATTERNS_SEEN, LAST_SCORED, RULES, ensure_state_dir, seed_state_from_home

seed_state_from_home()

NOW = time.time()


def load_weights():
    return json.loads(WEIGHTS.read_text())


def load_seen():
    if PATTERNS_SEEN.exists():
        return json.loads(PATTERNS_SEEN.read_text())
    return {}


def parse_raw():
    """Yield (ts, source, payload_dict)."""
    if not RAW.exists():
        return
    with RAW.open() as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            ts = int(parts[0])
            source = parts[1]
            if source == "zsh":
                yield ts, "zsh", {"cmd": parts[2]}
            elif source == "git":
                yield ts, "git", {"repo": parts[2], "msg": parts[3] if len(parts) > 3 else ""}
            elif source == "mem":
                yield ts, "mem", {"file": parts[2]}


# ---- detectors ----
# Each detector returns dict: pattern_id -> {freq, samples[], est_time_sec, est_effort_hours, domain, suggestion}

def detect_zsh_command_freq(events):
    """Cluster commands by first 2 tokens."""
    out = defaultdict(lambda: {"freq": 0, "samples": [], "last_ts": 0})
    for ts, src, p in events:
        if src != "zsh":
            continue
        cmd = p["cmd"].strip()
        tokens = cmd.split()
        if len(tokens) < 2:
            key = tokens[0] if tokens else "(empty)"
        else:
            key = " ".join(tokens[:2])
        # skip noise
        if key in ("ls", "cd", "rtk", "cat", "vim", "nvim", "code", "exit", "clear"):
            continue
        out[key]["freq"] += 1
        out[key]["last_ts"] = max(out[key]["last_ts"], ts)
        if len(out[key]["samples"]) < 3:
            out[key]["samples"].append(cmd)
    return [
        {
            "id": f"zsh:{k}",
            "kind": "shell-command",
            "freq": v["freq"],
            "samples": v["samples"],
            "last_ts": v["last_ts"],
            "est_time_sec": 30,
            "est_effort_hours": 0.5,
            "domain": "general",
            "suggestion": f"Alias or skill for `{k} ...` (used {v['freq']}x)",
        }
        for k, v in out.items()
        if v["freq"] >= 3
    ]


def detect_commit_pattern(events):
    """Find commit message prefix repetition."""
    out = defaultdict(lambda: {"freq": 0, "samples": [], "last_ts": 0, "repos": set()})
    for ts, src, p in events:
        if src != "git":
            continue
        msg = p["msg"]
        m = re.match(r"^(\w+)(?:\(([^)]+)\))?:", msg)
        if not m:
            continue
        prefix = m.group(0)
        out[prefix]["freq"] += 1
        out[prefix]["last_ts"] = max(out[prefix]["last_ts"], ts)
        out[prefix]["repos"].add(p["repo"].rsplit("/", 1)[-1])
        if len(out[prefix]["samples"]) < 3:
            out[prefix]["samples"].append(msg[:80])
    return [
        {
            "id": f"git:prefix:{k}",
            "kind": "commit-prefix",
            "freq": v["freq"],
            "samples": v["samples"],
            "last_ts": v["last_ts"],
            "repos": list(v["repos"]),
            "est_time_sec": 60,
            "est_effort_hours": 1.0,
            "domain": "general",
            "suggestion": f"Auto-draft commit msg for `{k}` (used {v['freq']}x across {len(v['repos'])} repos) — extend caveman:caveman-commit",
        }
        for k, v in out.items()
        if v["freq"] >= 5
    ]


def detect_repo_focus(events):
    """Most-touched repos this week → domain inference for Sensei."""
    out = Counter()
    last_ts = defaultdict(int)
    for ts, src, p in events:
        if src != "git":
            continue
        repo = p["repo"].rsplit("/", 1)[-1]
        out[repo] += 1
        last_ts[repo] = max(last_ts[repo], ts)
    return [
        {
            "id": f"focus:{repo}",
            "kind": "repo-focus",
            "freq": cnt,
            "samples": [repo],
            "last_ts": last_ts[repo],
            "est_time_sec": 0,
            "est_effort_hours": 0,
            "domain": "general",
            "suggestion": f"Repo `{repo}`: {cnt} commits this period — focus area",
            "informational": True,
        }
        for repo, cnt in out.most_common(5)
    ]


def detect_branch_to_pr_gap(events):
    """Heuristic: many commits, no `gh pr` invocation → opportunity for pr-describe automation."""
    git_count = sum(1 for ts, src, p in events if src == "git")
    pr_invocations = sum(1 for ts, src, p in events if src == "zsh" and "gh pr" in p["cmd"])
    if git_count > 20 and pr_invocations < 3:
        return [{
            "id": "gap:pr-describe",
            "kind": "automation-gap",
            "freq": git_count,
            "samples": [f"{git_count} commits, only {pr_invocations} `gh pr` invocations"],
            "last_ts": int(NOW),
            "est_time_sec": 300,
            "est_effort_hours": 0.5,
            "domain": "general",
            "suggestion": "Use pr-describe skill more — high commit volume with low PR creation. Consider auto-PR on push.",
        }]
    return []


def score_pattern(p, w):
    if p.get("informational"):
        return 0.0
    freq = p["freq"]
    days_ago = max(1, (NOW - p["last_ts"]) / 86400)
    recency = 1.0 / days_ago
    s = (
        w["freq"] * math.log1p(freq)
        + w["time_per_run_sec"] * math.log1p(p["est_time_sec"])
        + w["recency_days"] * recency
        + w["effort_to_automate_hours"] * p["est_effort_hours"]
    )
    return round(s, 2)


def load_disabled_kinds():
    if RULES.exists():
        try:
            return set(json.loads(RULES.read_text()).get("disabled", []))
        except Exception:
            return set()
    return set()


def main():
    weights = load_weights()
    disabled = load_disabled_kinds()
    events = list(parse_raw())
    print(f"# loaded {len(events)} events; disabled kinds: {sorted(disabled) or '(none)'}", file=sys.stderr)

    detectors = [
        detect_zsh_command_freq,
        detect_commit_pattern,
        detect_repo_focus,
        detect_branch_to_pr_gap,
    ]
    patterns = []
    for d in detectors:
        try:
            patterns.extend(d(events))
        except Exception as e:
            print(f"# detector {d.__name__} failed: {e}", file=sys.stderr)

    # filter disabled kinds (L2 auto-disable)
    patterns = [p for p in patterns if p.get("kind") not in disabled]

    for p in patterns:
        p["score"] = score_pattern(p, weights)

    patterns.sort(key=lambda x: x["score"], reverse=True)
    out = {"generated_at": int(NOW), "weights": weights, "disabled_kinds": sorted(disabled), "patterns": patterns}

    # persist for decide.py to look up by id
    LAST_SCORED.parent.mkdir(parents=True, exist_ok=True)
    LAST_SCORED.write_text(json.dumps(out, indent=2, default=str))

    json.dump(out, sys.stdout, indent=2, default=str)


if __name__ == "__main__":
    main()
