#!/usr/bin/env python3
"""Smart context loader.

Reads Claude Code UserPromptSubmit hook JSON from stdin.
Tokenizes prompt, scores all memory files by keyword overlap,
emits top matches to stdout as additionalContext.

Memory roots scanned:
  ~/.claude/memory/*.md
  ~/.claude/projects/*/memory/*.md
Excludes: INDEX.md, MEMORY.md (those are pointers, not bodies).

Token saving: skips full INDEX load, surfaces only relevant bodies.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
DODOJO_DATA = Path(os.environ.get("DODOJO_DATA") or str(HOME / ".claude"))
ROOTS = [
    DODOJO_DATA / "memory",
    DODOJO_DATA / "projects",
]
INDEX_NAMES = {"INDEX.md", "MEMORY.md"}

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


def parse_frontmatter(body: str) -> tuple[dict, str]:
    if not body.startswith("---\n"):
        return {}, body
    end = body.find("\n---\n", 4)
    if end == -1:
        return {}, body
    fm_block = body[4:end]
    rest = body[end + 5:]
    fm: dict = {}
    for line in fm_block.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, rest


def collect_memory_files() -> list[Path]:
    files: list[Path] = []
    direct = ROOTS[0]
    if direct.is_dir():
        for f in direct.glob("*.md"):
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

    files = collect_memory_files()
    if not files:
        return 0

    # cwd-aware boost: project memories matching current cwd get 2x score.
    # Hook payload includes cwd; map to ~/.claude/projects/<slug>/memory/ path.
    cwd = payload.get("cwd") or ""
    cwd_project_dir = ""
    if cwd:
        slug = "-" + cwd.strip("/").replace("/", "-")
        cwd_project_dir = str((DODOJO_DATA / "projects" / slug / "memory").resolve())

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
