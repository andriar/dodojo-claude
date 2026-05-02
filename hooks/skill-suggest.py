#!/usr/bin/env python3
"""Skill auto-suggester.

Reads UserPromptSubmit hook JSON from stdin.
Scores custom skills (~/.claude/skills/*/SKILL.md) by keyword overlap with prompt.
Emits a one-liner hint when top score crosses threshold.

Plugin skills are deliberately excluded — they already surface via the
system-reminder skill list. This hook only prods user about *custom* skills
which are easier to forget when 12+ exist.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
DODOJO_DATA = Path(os.environ.get("DODOJO_DATA") or str(HOME / ".claude"))
SKILLS_ROOT = DODOJO_DATA / "skills"

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "at", "by", "for", "with", "and", "or", "but",
    "if", "then", "else", "this", "that", "these", "those", "it", "its",
    "as", "from", "into", "out", "up", "down", "do", "does", "did", "done",
    "have", "has", "had", "i", "you", "he", "she", "we", "they", "me",
    "my", "your", "our", "their", "yang", "untuk", "dengan", "dari", "ke",
    "di", "dan", "atau", "ini", "itu", "saya", "kamu", "kita", "kami",
    "apa", "kenapa", "kalau", "bisa", "ada", "kok", "sih", "aja", "juga",
    "tp", "tapi", "no", "yes", "ok", "ya", "what", "how", "why", "when",
    "where", "which", "who", "can", "could", "should", "would", "may",
    "make", "made", "use", "used", "using", "get", "got", "set", "way",
    "want", "need", "like", "just", "also", "only", "very", "more", "most",
    "some", "any", "all", "not", "now", "still", "than", "so",
    "skill", "skills", "tool", "tools", "claude", "code", "agent",
}

MIN_WORD_LEN = 3
MIN_TOP_SCORE = 3  # lower threshold; weighted matches still ensure relevance
MAX_HINTS = 2

# 2-letter dev acronyms worth keeping (would be filtered by MIN_WORD_LEN otherwise)
ACRONYMS = {"pr", "ui", "ux", "ai", "ci", "cd", "qa", "db", "js", "ts", "go", "rs"}
LOG_PATH = DODOJO_DATA / "hooks" / "skill-suggest.log"


def tokenize(text: str) -> set[str]:
    text = text.lower()
    words = re.findall(r"[a-z][a-z0-9_-]*", text)
    out: set[str] = set()
    for w in words:
        if w in STOPWORDS:
            continue
        if len(w) >= MIN_WORD_LEN or w in ACRONYMS:
            out.add(w)
    return out


def parse_frontmatter(body: str) -> dict:
    if not body.startswith("---\n"):
        return {}
    end = body.find("\n---\n", 4)
    if end == -1:
        return {}
    fm: dict = {}
    for line in body[4:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def collect_skills() -> list[tuple[str, str]]:
    if not SKILLS_ROOT.is_dir():
        return []
    out: list[tuple[str, str]] = []
    for child in SKILLS_ROOT.iterdir():
        # Skip drafts + archives
        if not child.is_dir() or child.name.startswith("_"):
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            continue
        try:
            raw = skill_md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        fm = parse_frontmatter(raw)
        name = fm.get("name", child.name)
        desc = fm.get("description", "")
        if name and desc:
            out.append((name, desc))
    return out


def score(prompt_tokens: set[str], name: str, desc: str) -> int:
    name_tokens = tokenize(name.replace("-", " "))
    desc_tokens = tokenize(desc)
    return 4 * len(prompt_tokens & name_tokens) + len(prompt_tokens & desc_tokens)


def log(record: dict) -> None:
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    prompt = payload.get("prompt") or ""
    if not prompt or len(prompt) < 6:
        return 0

    tokens = tokenize(prompt)
    if len(tokens) < 2:
        return 0

    skills = collect_skills()
    if not skills:
        return 0

    scored = [(score(tokens, n, d), n, d) for n, d in skills]
    scored = [s for s in scored if s[0] >= MIN_TOP_SCORE]
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:MAX_HINTS]

    import hashlib
    import time
    log({
        "ts": int(time.time()),
        "prompt_hash": hashlib.sha1(prompt.encode()).hexdigest()[:10],
        "hint_count": len(top),
        "hints": [{"name": n, "score": s} for s, n, _ in top],
    })

    if not top:
        return 0

    print("[skill-suggest]")
    for s, n, d in top:
        first = re.split(r"[.!?]\s", d, maxsplit=1)[0]
        if len(first) > 100:
            first = first[:97] + "..."
        print(f"  → /{n} [{s}] {first}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
