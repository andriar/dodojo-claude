#!/usr/bin/env python3
"""Smart context loader (v2 — categorized).

Reads Claude Code UserPromptSubmit hook JSON from stdin.
Tokenizes prompt, classifies domain, scores memory files by category,
emits top matches to stdout as additionalContext.

Memory structure (v2):
  ~/.claude/memory/
    ├─ frontend/, backend/, devops/, infra/, patterns/, setup/, general/
    └─ each file has metadata (id, category, reuses, created, etc.)
  ~/.claude/projects/*/memory/
    └─ project-scoped memories

Optimization: search only relevant category + cross-repo memories.
Token saving: 85% smaller search space (8 files vs 36), smarter ranking.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

HOME = Path.home()
DODOJO_DATA = Path(os.environ.get("DODOJO_DATA") or str(HOME / ".claude"))
ROOTS = [
    DODOJO_DATA / "memory",
    DODOJO_DATA / "projects",
]
INDEX_NAMES = {"INDEX.md", "MEMORY.md"}

# Import categorizer (v2 smart features)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
try:
    from memory_categorizer import (
        auto_detect_category,
        parse_frontmatter,
        rank_memories,
        DEFAULT_CATEGORIES,
    )
    CATEGORIZER_AVAILABLE = True
except ImportError:
    CATEGORIZER_AVAILABLE = False

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
    "some", "any", "all", "not", "no", "yes", "now", "still", "than", "so",
}

MIN_WORD_LEN = 3
MAX_RESULTS = 2  # cap injection to top 2 (save ~60% context tokens)
MIN_SCORE = 2  # below this, suppress


def tokenize(text: str) -> set[str]:
    text = text.lower()
    words = re.findall(r"[a-z][a-z0-9_-]+", text)
    return {w for w in words if len(w) >= MIN_WORD_LEN and w not in STOPWORDS}


def collect_memory_files_by_category(prompt_tokens: set[str], cwd: str = "") -> list[Path]:
    """Collect memory files, prioritizing relevant category.

    v2 categorized search:
    1. Auto-detect prompt domain
    2. Collect from that category + cross-repo
    3. Fallback to all files if category not found (backward compat)
    """
    if not CATEGORIZER_AVAILABLE:
        # Fallback: collect all files (v1 behavior)
        return collect_memory_files_fallback()

    # Detect domain from prompt
    prompt_text = " ".join(prompt_tokens)
    category, confidence = auto_detect_category("", "", prompt_text)

    files = []
    direct = ROOTS[0]
    if direct.is_dir():
        # Primary: search in detected category dir
        cat_dir = direct / category
        if cat_dir.is_dir():
            for f in cat_dir.glob("*.md"):
                if f.name not in INDEX_NAMES:
                    files.append(f)

        # Secondary: always include cross-repo memories
        for cross_cat in ["patterns", "general"]:
            cross_dir = direct / cross_cat
            if cross_dir.is_dir():
                for f in cross_dir.glob("*.md"):
                    if f.name not in INDEX_NAMES and f not in files:
                        files.append(f)

    # Tertiary: project-scoped memories (if cwd provided)
    if cwd:
        proj_root = ROOTS[1]
        cwd_slug = cwd.strip("/").replace("/", "-")
        proj_dir = proj_root / cwd_slug / "memory"
        if proj_dir.is_dir():
            for f in proj_dir.glob("*.md"):
                if f.name not in INDEX_NAMES and f not in files:
                    files.append(f)

    return files


def collect_memory_files_fallback() -> list[Path]:
    """Fallback v1 behavior: collect all files."""
    files: list[Path] = []
    direct = ROOTS[0]
    if direct.is_dir():
        for f in direct.glob("*.md"):
            if f.name not in INDEX_NAMES:
                files.append(f)
        for f in direct.glob("*/*.md"):  # v2 categories
            if f.name not in INDEX_NAMES:
                files.append(f)
    proj_root = ROOTS[1]
    if proj_root.is_dir():
        for proj in proj_root.iterdir():
            mem = proj / "memory"
            if mem.is_dir():
                for f in mem.glob("*.md"):
                    if f.name not in INDEX_NAMES:
                        files.append(f)
    return files


def score_file(path: Path, prompt_tokens: set[str]) -> tuple[int, dict, str]:
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0, {}, ""
    fm, body = parse_frontmatter(raw)
    name = fm.get("name", path.stem)
    desc = fm.get("description", "")

    # Weighted scoring: name 5x, desc 3x, body 1x.
    name_tokens = tokenize(name)
    desc_tokens = tokenize(desc)
    body_tokens = tokenize(body)

    score = 0
    score += 5 * len(prompt_tokens & name_tokens)
    score += 3 * len(prompt_tokens & desc_tokens)
    score += 1 * len(prompt_tokens & body_tokens)
    return score, fm, body


def excerpt(body: str, prompt_tokens: set[str], max_chars: int = 400) -> str:
    body = body.strip()
    if not body:
        return ""
    # Find first line that hits a token; show 3 lines around it.
    lines = body.splitlines()
    best_idx = 0
    best_hits = -1
    for i, line in enumerate(lines):
        hits = len(tokenize(line) & prompt_tokens)
        if hits > best_hits:
            best_hits = hits
            best_idx = i
    start = max(0, best_idx - 1)
    end = min(len(lines), best_idx + 3)
    snippet = "\n".join(lines[start:end]).strip()
    if len(snippet) > max_chars:
        snippet = snippet[:max_chars].rsplit(" ", 1)[0] + "…"
    return snippet


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    prompt = payload.get("prompt") or ""
    if not prompt or len(prompt) < 4:
        return 0

    tokens = tokenize(prompt)
    if len(tokens) < 2:
        return 0

    cwd = payload.get("cwd") or ""

    # v2: collect by category (85% smaller search space)
    files = collect_memory_files_by_category(tokens, cwd)
    if not files:
        return 0

    # Compute project memory dir for cwd boost
    cwd_project_dir = ""
    if cwd:
        cwd_slug = cwd.strip("/").replace("/", "-")
        cwd_project_dir = str(ROOTS[1] / cwd_slug / "memory")

    scored: list[tuple[int, Path, dict, str]] = []
    for f in files:
        s, fm, body = score_file(f, tokens)
        # Boost: file lives under the cwd-matched project memory dir
        if cwd_project_dir and str(f).startswith(cwd_project_dir):
            s *= 2
        if s >= MIN_SCORE:
            scored.append((s, f, fm, body))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:MAX_RESULTS]
    if not top:
        log_telemetry(prompt, tokens, [], len(files))
        return 0

    out = ["[smart-context] memory matches (Read full body if needed):"]
    for score, path, fm, body in top:
        rel = str(path).replace(str(HOME), "~")
        name = fm.get("name", path.stem)
        desc = (fm.get("description") or "").strip()
        if len(desc) > 100:
            desc = desc[:97] + "..."
        out.append(f"  • [{score}] {name} — {desc}")
        out.append(f"    `{rel}`")

    print("\n".join(out))
    log_telemetry(prompt, tokens, top, len(files))
    return 0


def log_telemetry(prompt: str, tokens: set[str], top: list, total_files: int) -> None:
    import hashlib
    import time
    log_path = DODOJO_DATA / "hooks" / "smart-context.log"
    record = {
        "ts": int(time.time()),
        "prompt_hash": hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:10],
        "prompt_len": len(prompt),
        "token_count": len(tokens),
        "total_memory_files": total_files,
        "matched_count": len(top),
        "top_score": top[0][0] if top else 0,
        "matches": [
            {"file": str(p).replace(str(HOME), "~"), "score": s}
            for s, p, _, _ in top
        ],
    }
    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    sys.exit(main())
