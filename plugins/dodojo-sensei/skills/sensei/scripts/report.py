#!/usr/bin/env python3
"""Sensei report writer — render scored patterns to Obsidian markdown.

Usage:
  report.py            # write to vault
  report.py --dry      # print to stdout
  report.py --top N    # limit to top N (default 10)
"""
import json, sys, os, argparse, subprocess, time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import HOME, SCRIPTS, VAULT, seed_state_from_home

seed_state_from_home()

TEMPLATE = """# Sensei Weekly — {date}

Generated: {generated}
Patterns analyzed: {n_patterns}
Window: last 7 days

## Decision template

For each rec below: respond with `/sensei accept <id>` or `/sensei reject <id> <reason>`.

---

{body}

## Stats

- Total events scored: **{n_events}**
- Detectors fired: **{detectors}**
- Top score: **{top_score}**
- Weights version: **{w_version}** (last_updated: {w_updated})

## Pair with Kagami

Accepted recommendations should be saved to memory by auto-reflect:
- Cross-repo automation → `~/.claude/memory/`
- Project-specific → `~/.claude/projects/<project>/memory/`
"""

REC_TPL = """### {rank}. {suggestion}

- **id**: `{id}`
- **kind**: {kind}
- **score**: {score}
- **freq**: {freq}
- **last seen**: {last_human}
- **est_time/run**: {time}s
- **est_effort**: {effort}h
- **samples**:
{samples_block}

**Decision**: [ ] accept  [ ] reject  [ ] later
"""


def fmt_samples(samples):
    return "\n".join(f"  - `{s}`" for s in samples) if samples else "  - (none)"


def human_ts(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def run_pipeline():
    """Run collect.sh + score.py and return parsed JSON."""
    subprocess.run([str(SCRIPTS / "collect.sh"), "7"], check=True, stderr=subprocess.DEVNULL)
    out = subprocess.check_output(["python3", str(SCRIPTS / "score.py")], text=True)
    return json.loads(out)


def render(data, top_n=10):
    patterns = data.get("patterns", [])
    actionable = [p for p in patterns if not p.get("informational")][:top_n]
    informational = [p for p in patterns if p.get("informational")]

    body_parts = []
    body_parts.append("## Top recommendations\n")
    for i, p in enumerate(actionable, 1):
        body_parts.append(REC_TPL.format(
            rank=i,
            suggestion=p["suggestion"],
            id=p["id"],
            kind=p["kind"],
            score=p["score"],
            freq=p["freq"],
            last_human=human_ts(p["last_ts"]),
            time=p["est_time_sec"],
            effort=p["est_effort_hours"],
            samples_block=fmt_samples(p.get("samples", [])),
        ))

    if informational:
        body_parts.append("\n## Focus areas (informational)\n")
        for p in informational:
            body_parts.append(f"- **{p['suggestion']}** (score: {p['score']})")

    detector_kinds = sorted(set(p["kind"] for p in patterns))
    weights = data.get("weights", {})
    w_meta = weights.get("_meta", {})

    return TEMPLATE.format(
        date=datetime.now().strftime("%Y-%m-%d"),
        generated=human_ts(data.get("generated_at", time.time())),
        n_patterns=len(patterns),
        n_events="(see raw.tsv)",
        detectors=", ".join(detector_kinds),
        top_score=actionable[0]["score"] if actionable else "n/a",
        w_version=w_meta.get("version", "?"),
        w_updated=w_meta.get("last_updated", "?"),
        body="\n".join(body_parts),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true", help="print to stdout instead of writing to vault")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--no-collect", action="store_true", help="skip collect+score, use existing JSON from stdin")
    args = ap.parse_args()

    if args.no_collect:
        data = json.load(sys.stdin)
    else:
        data = run_pipeline()

    md = render(data, top_n=args.top)

    if args.dry:
        print(md)
        return

    VAULT.mkdir(parents=True, exist_ok=True)
    out = VAULT / f"weekly-{datetime.now().strftime('%Y-%m-%d')}.md"
    out.write_text(md)
    print(f"Wrote {out}", file=sys.stderr)
    print(out)


if __name__ == "__main__":
    main()
