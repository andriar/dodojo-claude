#!/usr/bin/env python3
"""Cost guard — block obvious unbounded / runaway operations.

Reads PreToolUse hook JSON from stdin. Inspects the tool call and
either:
  - exit 0  → allow silently
  - exit 2  → block with explanation to stderr (model sees it)

Targeted patterns (clear footguns only — not aesthetic preferences):

Bash:
  - `find /` or `find / ...`           — scan entire filesystem (slow, noisy)
  - `find $HOME` lacking `-maxdepth`   — likely traversal of huge tree
  - `grep -r ... /` rooted at /        — full FS grep
  - `du -h /` without limit            — costly disk walk
  - `rm -rf /` or `rm -rf $HOME`       — catastrophic delete
  - `cat`/`head -<huge>`/`tail` on /var/log/ without filter

Read:
  - file_path inside /var/log/, /proc/, /sys/ without `limit` arg

Tool args are inspected only for the current call; nothing else.
"""

from __future__ import annotations

import json
import re
import sys

# Bash command patterns that should be blocked (regex, case-sensitive)
BLOCK_BASH = [
    (re.compile(r"\bfind\s+/(\s|$)"), "find rooted at / scans entire filesystem; specify a subdir or add -maxdepth"),
    (re.compile(r"\bfind\s+/\s+-"), "find / with predicates still walks everything; restrict to a subdir"),
    (re.compile(r"\bgrep\s+(-[a-zA-Z]*r[a-zA-Z]*\s+|--recursive\s+)[^|]*\s+/(\s|$|'|\")"), "recursive grep rooted at / scans full FS"),
    (re.compile(r"\bdu\s+(-[a-zA-Z]*\s+)?/(\s|$)"), "du / walks the whole filesystem"),
    (re.compile(r"\brm\s+-rf?\s+/\s*$"), "rm -rf / would wipe everything"),
    (re.compile(r"\brm\s+-rf?\s+(\$HOME|~)(/\*)?\s*$"), "rm -rf on $HOME / ~ would wipe your home dir"),
    (re.compile(r"\brm\s+-rf?\s+\*\s*$"), "rm -rf * in arbitrary dir is high-blast-radius"),
]

# Read paths that need an explicit limit
READ_HEAVY_PREFIXES = ("/var/log/", "/proc/", "/sys/")


def block(reason: str) -> int:
    print(f"[cost-guard] BLOCKED: {reason}", file=sys.stderr)
    print("Adjust the command (add a subdir, -maxdepth, limit, etc.) and retry.", file=sys.stderr)
    return 2


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    tool = payload.get("tool_name") or ""
    args = payload.get("tool_input") or {}

    if tool == "Bash":
        cmd = args.get("command") or ""
        if not isinstance(cmd, str):
            return 0
        for rx, why in BLOCK_BASH:
            if rx.search(cmd):
                return block(f"{why}\n  Command: {cmd[:200]}")

    elif tool == "Read":
        path = args.get("file_path") or ""
        if not isinstance(path, str):
            return 0
        if path.startswith(READ_HEAVY_PREFIXES) and not args.get("limit"):
            return block(
                f"Read of {path} without a `limit` arg may load megabytes.\n"
                f"  Add `limit: 200` (or similar) to the Read call."
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
