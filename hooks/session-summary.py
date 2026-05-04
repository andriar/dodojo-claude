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


def _resolve_buddy_dir() -> Path:
    """Discover where pokemon-buddy plugin stores state.

    Plugin hardcodes ~/.claude/ but user may relocate. Cascade:
    1. POKEMON_BUDDY_HOME env override
    2. Probe known candidates for sentinel file
    3. Fallback to plugin default ~/.claude/
    """
    if env := os.environ.get("POKEMON_BUDDY_HOME"):
        p = Path(env).expanduser()
        if p.is_dir():
            return p
    for cand in (HOME / ".claude", DODOJO_DATA, HOME / ".pokemon-buddy"):
        if (cand / "buddy-pokemon.md").is_file():
            return cand
    return HOME / ".claude"


BUDDY_HOME = _resolve_buddy_dir()
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

        # Find last user message — only summarize the current turn.
        # Skip tool_result blocks: they have role=user but aren't real prompts.
        for i, r in enumerate(records):
            msg = r.get("message") or {}
            role = msg.get("role") or r.get("type")
            if role != "user":
                continue
            content = msg.get("content")
            is_real_prompt = False
            if isinstance(content, str):
                is_real_prompt = bool(content.strip())
            elif isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text" and (c.get("text") or "").strip():
                        is_real_prompt = True
                        break
            if is_real_prompt:
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

    # Track which memories were injected this session
    injected_memories = []
    sc_log = DODOJO_DATA / "hooks" / "smart-context.log"
    if sc_log.is_file():
        try:
            for line in sc_log.read_text(errors="replace").splitlines()[-50:]:  # last 50 entries
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Only count entries from this session (roughly, by timestamp)
                    if abs(entry.get("ts", 0) - int(time.time())) < 600:  # within 10 min
                        for match in entry.get("matches", []):
                            file = match.get("file", "")
                            if file and file not in injected_memories:
                                injected_memories.append(file)
                except json.JSONDecodeError:
                    continue
        except OSError:
            pass

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
        "memories_injected": injected_memories,  # ← NEW
        "memory_inject_count": len(injected_memories),  # ← NEW
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
        xp_log = BUDDY_HOME / "buddy-xp-pending.jsonl"
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
