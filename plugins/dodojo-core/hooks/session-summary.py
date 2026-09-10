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

# Import categorizer for metadata updates
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
try:
    from memory_categorizer import update_memory_metadata
    CATEGORIZER_AVAILABLE = True
except ImportError:
    CATEGORIZER_AVAILABLE = False


def _prompt_category(text: str) -> str:
    """Domain of the prompt, via the shared categorizer. Empty when unavailable
    so a missing lib degrades the record rather than the whole hook."""
    if not CATEGORIZER_AVAILABLE or not text.strip():
        return ""
    try:
        from memory_categorizer import auto_detect_category
        category, _confidence = auto_detect_category("", "", text)
        return category or ""
    except Exception:
        return ""


def update_memory_usage(memory_files: list[str]) -> None:
    """Update reuse count + last_used timestamp for injected memories."""
    if not CATEGORIZER_AVAILABLE or not memory_files:
        return

    now = time.strftime("%Y-%m-%d")
    for mem_file in memory_files:
        # Expand ~ to home
        if mem_file.startswith("~"):
            mem_path = Path(mem_file.replace("~", str(HOME)))
        else:
            mem_path = Path(mem_file)

        if not mem_path.is_file():
            continue

        try:
            # Increment reuses, update last_used
            from memory_categorizer import parse_frontmatter
            content = mem_path.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(content)

            reuses = int(fm.get("reuses", "0"))
            fm["reuses"] = str(reuses + 1)
            fm["last_used"] = now

            update_memory_metadata(mem_path, fm)
        except (OSError, ValueError, AttributeError):
            # Silently skip errors (not critical)
            pass


def _resolve_buddy_dir() -> Path | None:
    """Discover where pokemon-buddy plugin stores state.

    Opt-in contract: this bridge only fires when pokemon-buddy is actually
    installed. Detection cascade:

    1. `DODOJO_POKEMON_XP_QUEUE` — explicit path to the XP queue file.
       If set, returns its parent. Most explicit, recommended.
    2. `POKEMON_BUDDY_HOME` env var — points at the buddy data dir.
       Used when buddy is at a non-standard location.
    3. Sentinel probe — look for `buddy-pokemon.md` in known candidates.
       This is the marker buddy itself writes; absence means buddy is not
       installed and the bridge stays silent.

    Returns None when buddy isn't detected — caller must skip the write.
    Previously this fell back to `~/.claude/` which created a ghost file
    even when buddy was uninstalled.
    """
    explicit = os.environ.get("DODOJO_POKEMON_XP_QUEUE")
    if explicit:
        return Path(explicit).expanduser().parent

    if env := os.environ.get("POKEMON_BUDDY_HOME"):
        p = Path(env).expanduser()
        if p.is_dir() and (p / "buddy-pokemon.md").is_file():
            return p

    for cand in (HOME / ".claude", DODOJO_DATA, HOME / ".pokemon-buddy"):
        if (cand / "buddy-pokemon.md").is_file():
            return cand

    return None


BUDDY_HOME = _resolve_buddy_dir()
# Canonical telemetry location lives under plugins/data/dodojo-dodojo/ (see
# lib/paths.py). lib/ is already on sys.path from the memory_categorizer
# import above. Fall back to the historical DODOJO_DATA/sessions/ if the
# helper is missing (older install).
try:
    from paths import sessions_dir_write as _sessions_dir_write  # type: ignore
    SESSIONS_DIR = _sessions_dir_write()
except ImportError:
    SESSIONS_DIR = DODOJO_DATA / "sessions"
TOUCH_TOOLS = {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit"}

# Sensei keys its heuristics off what a prompt was ASKING FOR, not its wording.
# Storing the matched buckets instead of the prompt text keeps the telemetry
# free of raw user input while still feeding pattern analysis.
PROMPT_INTENTS = {
    "search": ("find", "search", "grep", "where", "which", "location"),
    "clarify": ("what do you mean", "can you explain", "like this", "like that",
                "more specifically", "can you clarify", "what is", "how do", "why"),
    "create": ("create", "write", "add", "new", "build", "implement"),
    "fix": ("fix", "bug", "error", "broken", "fail", "debug"),
}


def classify_prompt(text: str) -> list[str]:
    low = text.lower()
    return [name for name, needles in PROMPT_INTENTS.items()
            if any(n in low for n in needles)]


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
    file_reads: Counter[str] = Counter()
    tokens = Counter({"input": 0, "output": 0, "cache_read": 0, "cache_write": 0})
    prompt_text = ""
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
                prompt_text += " " + content
            elif role == "user" and isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        text = c.get("text") or ""
                        user_chars += len(text)
                        prompt_text += " " + text

            if role == "assistant":
                usage = msg.get("usage") or {}
                tokens["input"] += usage.get("input_tokens", 0) or 0
                tokens["output"] += usage.get("output_tokens", 0) or 0
                tokens["cache_read"] += usage.get("cache_read_input_tokens", 0) or 0
                tokens["cache_write"] += usage.get("cache_creation_input_tokens", 0) or 0

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
                                    if name == "Read":
                                        file_reads[v] += 1
    except OSError:
        return 0

    if not tool_counts and user_chars == 0 and assistant_chars == 0:
        # Empty turn — skip
        return 0

    # Track which memories were injected this session.
    # Prefer session_id match (v2 smart-context records); fall back to ±600s
    # wall-clock window for legacy v1 records that lack session_id.
    injected_memories = []
    sc_log = DODOJO_DATA / "hooks" / "smart-context.log"
    if sc_log.is_file():
        now_ts = int(time.time())
        try:
            for line in sc_log.read_text(errors="replace").splitlines()[-50:]:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                entry_sid = entry.get("session_id") or ""
                if entry_sid:
                    if entry_sid != session_id:
                        continue
                else:
                    if abs(entry.get("ts", 0) - now_ts) >= 600:
                        continue
                for match in entry.get("matches", []):
                    file = match.get("file", "")
                    if file and file not in injected_memories:
                        injected_memories.append(file)
        except OSError:
            pass

    record = {
        "v": 2,
        "ts": int(time.time()),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "session_id": session_id,
        "cwd": cwd,
        "tool_counts": dict(tool_counts),
        "tool_total": sum(tool_counts.values()),
        "files_touched": sorted(files_touched)[:50],  # cap
        "files_touched_count": len(files_touched),
        "file_reads": dict(file_reads),
        "tokens": dict(tokens),
        "prompt_intents": classify_prompt(prompt_text),
        "prompt_category": _prompt_category(prompt_text),
        "user_chars": user_chars,
        "assistant_chars": assistant_chars,
        "memories_injected": injected_memories,
        "memory_inject_count": len(injected_memories),
    }

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = SESSIONS_DIR / (time.strftime("%Y-%m-%d") + ".jsonl")
    try:
        with out_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass

    # Phase 5b: Auto-update memory metadata (reuse count + last_used)
    update_memory_usage(record.get("memories_injected", []))

    # Optional bridge to pokemon-buddy XP system. Only fires when buddy is
    # actually installed (BUDDY_HOME != None) — see _resolve_buddy_dir.
    # Bypass via DODOJO_SKIP_BUDDY_XP=1.
    if (
        BUDDY_HOME is not None
        and os.environ.get("DODOJO_SKIP_BUDDY_XP", "0") != "1"
        and record["tool_total"] >= 5
        and record["files_touched_count"] >= 1
    ):
        explicit = os.environ.get("DODOJO_POKEMON_XP_QUEUE")
        xp_log = Path(explicit).expanduser() if explicit else BUDDY_HOME / "buddy-xp-pending.jsonl"
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
            xp_log.parent.mkdir(parents=True, exist_ok=True)
            with xp_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(xp_record) + "\n")
        except OSError:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
