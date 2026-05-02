#!/usr/bin/env python3
"""Session summary recorder.

Stop hook: fires when Claude finishes its response. Reads the transcript
(JSONL) path provided in the hook payload, extracts a lightweight summary
of the just-completed turn, appends one record to:

    ~/.claude/sessions/YYYY-MM-DD.jsonl

Captured per turn:
  - timestamp + session_id + cwd
  - tool invocation counts by name
  - files touched (Read/Write/Edit paths, dedup'd)
  - approximate user-prompt length + assistant-output length

Failure-tolerant: malformed transcript / missing fields → log nothing,
exit 0. Never blocks Stop.
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

HOME = Path.home()
DODOJO_DATA = Path(os.environ.get("DODOJO_DATA") or str(HOME / ".claude"))
SESSIONS_DIR = DODOJO_DATA / "sessions"
TOUCH_TOOLS = {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit"}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    transcript_path = payload.get("transcript_path") or ""
    session_id = payload.get("session_id") or "unknown"
    cwd = payload.get("cwd") or os.getcwd()

    if not transcript_path or not Path(transcript_path).is_file():
        return 0

    tool_counts: Counter[str] = Counter()
    files_touched: set[str] = set()
    user_chars = 0
    assistant_chars = 0
    last_user_idx = -1

    try:
        records: list[dict] = []
        with open(transcript_path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        # Find last user message — only summarize the current turn
        for i, r in enumerate(records):
            if r.get("type") == "user" or (r.get("message") or {}).get("role") == "user":
                last_user_idx = i

        scan = records[last_user_idx:] if last_user_idx >= 0 else records

        for r in scan:
            msg = r.get("message") or {}
            role = msg.get("role") or r.get("type")
            content = msg.get("content")

            if role == "user" and isinstance(content, str):
                user_chars += len(content)
            elif role == "user" and isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        user_chars += len(c.get("text") or "")

            if role == "assistant" and isinstance(content, list):
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    ctype = c.get("type")
                    if ctype == "text":
                        assistant_chars += len(c.get("text") or "")
                    elif ctype == "tool_use":
                        name = c.get("name") or "unknown"
                        tool_counts[name] += 1
                        ti = c.get("input") or {}
                        if name in TOUCH_TOOLS:
                            for key in ("file_path", "path", "notebook_path"):
                                v = ti.get(key)
                                if isinstance(v, str):
                                    files_touched.add(v)
    except OSError:
        return 0

    if not tool_counts and user_chars == 0 and assistant_chars == 0:
        # Empty turn — skip
        return 0

    record = {
        "ts": int(time.time()),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "session_id": session_id,
        "cwd": cwd,
        "tool_counts": dict(tool_counts),
        "tool_total": sum(tool_counts.values()),
        "files_touched": sorted(files_touched)[:50],  # cap
        "files_touched_count": len(files_touched),
        "user_chars": user_chars,
        "assistant_chars": assistant_chars,
    }

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = SESSIONS_DIR / (time.strftime("%Y-%m-%d") + ".jsonl")
    try:
        with out_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass

    # Bridge to Pokémon buddy XP system: queue an XP grant if turn is "meaningful"
    # (>= 5 tool invocations AND touched at least one file). Pokemon Coach skill /
    # SessionStart greeter can surface this for /poke:xp claim.
    if record["tool_total"] >= 5 and record["files_touched_count"] >= 1:
        xp_log = DODOJO_DATA / "buddy-xp-pending.jsonl"
        xp_record = {
            "ts": record["ts"],
            "iso": record["iso"],
            "session_id": record["session_id"],
            "tool_total": record["tool_total"],
            "files_touched_count": record["files_touched_count"],
            "top_files": record["files_touched"][:3],
            "claimed": False,
        }
        try:
            with xp_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(xp_record) + "\n")
        except OSError:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
