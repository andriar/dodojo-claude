#!/usr/bin/env python3
"""Smart memory categorization + metadata handling.

Provides:
- Auto-detect categories from memory content
- Parse/write metadata to memory files
- Rank memories by reuse + recency + cwd
- Generate unique memory IDs
"""

import json
import os
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple

# Domain keyword mappings (auto-detect categories)
DOMAIN_KEYWORDS = {
    "frontend": [
        "react", "vue", "angular", "css", "html", "component", "ui", "button",
        "form", "state", "hooks", "tailwind", "styled", "jsx", "tsx"
    ],
    "backend": [
        "api", "auth", "database", "sql", "orm", "model", "endpoint", "rest",
        "graphql", "schema", "migration", "query", "jwt", "session", "token"
    ],
    "devops": [
        "docker", "kubernetes", "k8s", "docker-compose", "ci", "cd", "jenkins",
        "github", "gitlab", "deploy", "terraform", "ansible", "nginx"
    ],
    "infra": [
        "aws", "gcp", "azure", "terraform", "cloudformation", "networking",
        "vpc", "security", "firewall", "dns", "load-balancer", "cdn"
    ],
}

DEFAULT_CATEGORIES = set(DOMAIN_KEYWORDS.keys())


def generate_memory_id(timestamp: Optional[int] = None) -> str:
    """Generate unique memory ID (mem_YYYYMMDD_NNNN)."""
    if timestamp is None:
        timestamp = int(time.time())
    dt = datetime.fromtimestamp(timestamp)
    # Counter: use lower 16 bits of timestamp as uniqueness suffix
    suffix = (timestamp & 0xFFFF) % 10000
    return f"mem_{dt.strftime('%Y%m%d')}_{suffix:04d}"


def parse_frontmatter(content: str) -> Tuple[Dict, str]:
    """Extract YAML frontmatter + body from memory file.

    Returns: (metadata_dict, body_text)
    """
    if not content.startswith("---\n"):
        return {}, content

    end = content.find("\n---\n", 4)
    if end == -1:
        return {}, content

    fm_block = content[4:end]
    body = content[end + 5:]

    metadata = {}
    for line in fm_block.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip().lower()
        val = val.strip().strip('"').strip("'")
        metadata[key] = val

    return metadata, body


def write_frontmatter(metadata: Dict, body: str) -> str:
    """Write metadata + body to markdown with frontmatter."""
    lines = ["---"]
    for key in sorted(metadata.keys()):
        val = metadata[key]
        if val is None:
            lines.append(f"{key}: null")
        elif isinstance(val, (list, dict)):
            lines.append(f"{key}: {json.dumps(val)}")
        else:
            lines.append(f"{key}: {val}")
    lines.append("---")
    lines.append("")
    lines.append(body.strip())
    return "\n".join(lines) + "\n"


def auto_detect_category(name: str, description: str, body: str) -> Tuple[str, float]:
    """Detect memory category from content.

    Returns: (category, confidence)
    Confidence: 0.0 (guess) to 1.0 (certain)
    """
    text = f"{name} {description} {body}".lower()
    words = set(re.findall(r"\b[a-z]+\b", text))

    scores = {}
    for cat, keywords in DOMAIN_KEYWORDS.items():
        match_count = len(words & set(keywords))
        if match_count > 0:
            scores[cat] = match_count

    if scores:
        best_cat = max(scores, key=scores.get)
        best_score = scores[best_cat]
        confidence = min(best_score / 5.0, 1.0)  # 5+ matches = high confidence
        return best_cat, confidence

    # Fallback: detect by content type
    if "decision" in text or "pattern" in text or "lesson" in text:
        return "patterns", 0.6
    if "setup" in text or "config" in text or "install" in text:
        return "setup", 0.6

    return "general", 0.3


def rank_memories(
    memories: list[Dict],
    prompt: str,
    cwd: str = "",
) -> list[Dict]:
    """Rank memories by relevance + freshness + reuse + cwd.

    Each memory should have: {'score': int, 'reuses': int, 'created': str, ...}
    """
    prompt_words = set(re.findall(r"\b[a-z]+\b", prompt.lower()))

    for mem in memories:
        score = mem.get("score", 0)

        # Factor: reuse frequency (popular = good)
        reuses = mem.get("reuses", 0)
        score += reuses * 0.1

        # Factor: recency (recent > stale)
        created = mem.get("created", "")
        if created:
            try:
                created_ts = datetime.strptime(created, "%Y-%m-%d").timestamp()
                age_days = (time.time() - created_ts) / 86400
                recency_boost = max(0, 5 - age_days * 0.1)  # decay over time
                score += recency_boost
            except (ValueError, AttributeError):
                pass

        # Factor: cwd match (current project = highly relevant)
        if cwd:
            # If memory is in ~/.claude/projects/<cwd-slug>/memory/, boost it 2x
            cwd_slug = cwd.strip("/").replace("/", "-")
            mem_file = mem.get("file", "")
            if cwd_slug in mem_file:
                score *= 2.0

        # Factor: category confidence (low confidence = reduce score)
        category_confidence = mem.get("category_confidence", 0.7)
        if category_confidence < 0.6:
            score *= 0.8

        mem["final_score"] = score

    return sorted(memories, key=lambda m: m.get("final_score", 0), reverse=True)


def update_memory_metadata(filepath: Path, updates: Dict) -> None:
    """Update metadata fields in an existing memory file.

    Atomic write: serialize to a sibling tmp file, then os.replace into place.
    Prevents truncation/corruption on crash, and is safe against concurrent
    Stop hooks racing to update the same file.
    """
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return

    metadata, body = parse_frontmatter(content)
    metadata.update(updates)

    new_content = write_frontmatter(metadata, body)
    if new_content == content:
        return

    tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
    try:
        tmp_path.write_text(new_content, encoding="utf-8")
        os.replace(tmp_path, filepath)
    except OSError:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass


def ensure_memory_has_metadata(filepath: Path) -> Dict:
    """Ensure memory has ID + metadata. Create if missing."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except OSError:
        return {}

    metadata, body = parse_frontmatter(content)

    # Ensure required fields
    if "id" not in metadata:
        metadata["id"] = generate_memory_id()

    if "name" not in metadata:
        metadata["name"] = filepath.stem

    if "created" not in metadata:
        metadata["created"] = datetime.now().strftime("%Y-%m-%d")

    if "category" not in metadata:
        # Auto-detect
        desc = metadata.get("description", "")
        cat, conf = auto_detect_category(metadata.get("name", ""), desc, body)
        metadata["category"] = cat
        metadata["category_confidence"] = f"{conf:.2f}"

    # Write back if anything changed
    new_content = write_frontmatter(metadata, body)
    if new_content != content:
        filepath.write_text(new_content, encoding="utf-8")

    return metadata


if __name__ == "__main__":
    # Test
    print("✓ Memory categorizer loaded")
    print(f"  Domains: {', '.join(sorted(DEFAULT_CATEGORIES))}")

    # Test auto-detect
    cat, conf = auto_detect_category(
        "React Hook Pattern",
        "useEffect cleanup for memory leaks",
        "When setting up event listeners in useEffect, always return cleanup..."
    )
    print(f"  Auto-detect: {cat} (confidence: {conf:.2f})")
