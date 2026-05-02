#!/usr/bin/env python3
"""Auto-memory trigger detector.

Reads UserPromptSubmit hook JSON. If user prompt contains explicit save/remember
trigger phrases ("ingat ini", "remember this", "from now on", "always X",
"don't ever Y", etc.) — emit a reminder for Claude to save a memory file
*before* answering, so the auto-reflect rule from CLAUDE.md actually fires.

CLAUDE.md already tells Claude to do this proactively, but in practice it
gets skipped. This hook makes it explicit by surfacing the trigger.
"""

from __future__ import annotations

import json
import re
import sys

# Trigger phrases (lowercase). Indonesian + English.
TRIGGERS = [
    # Direct save commands
    r"\bingat (ini|kalau|bahwa|aku)\b",
    r"\bsave (this|that|to memory)\b",
    r"\bremember (this|that|next time)\b",
    r"\bnote (this|that|down)\b",
    r"\btolong simpan\b",
    r"\bsimpan (ini|sebagai memory|sebagai catatan)\b",

    # Behavioral directives
    r"\bfrom now on\b",
    r"\bmulai sekarang\b",
    r"\bgo forward\b",
    r"\b(always|jangan pernah|jangan lagi|never)\b.{0,40}(don'?t|do|use|pakai|hindari)",
    r"\bdon'?t (ever|forget)\b",
    r"\bjangan (lupa|pernah)\b",
    r"\bbiar (ga|gak|tidak) (lupa|terulang)\b",

    # Correction signals worth saving
    r"\bnext time\b",
    r"\blain kali\b",
    r"\bbukan (begitu|gitu)\b.{0,40}(tapi|seharus)",
    r"\bdo not (do|say|make)\b",
]

COMPILED = [re.compile(p, re.IGNORECASE) for p in TRIGGERS]


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    prompt = payload.get("prompt") or ""
    if len(prompt) < 8:
        return 0

    matches: list[str] = []
    for rx in COMPILED:
        m = rx.search(prompt)
        if m:
            matches.append(m.group(0))
        if len(matches) >= 3:
            break

    if not matches:
        return 0

    phrases = ", ".join(f'"{m}"' for m in matches)
    print(f"[memory-trigger] save-phrase detected ({phrases}) — evaluate auto-reflect rule (CLAUDE.md). "
          f"Save to ~/.claude/memory/ if cross-repo, project memory dir if scoped, skip if ephemeral.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
