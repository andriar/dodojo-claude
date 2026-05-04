#!/usr/bin/env python3
"""Archive stale memories based on reuse + recency metrics.

Stale = unused 6+ months OR never reused after 30 days old.
Moves files to ~/.claude/memory/_archive/<category>/ with a manifest.
Reversible: manifest.jsonl lets users restore if archived too aggressively.
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from memory_categorizer import parse_frontmatter, write_frontmatter

HOME = Path.home()
MEMORY_DIR = HOME / ".claude" / "memory"
ARCHIVE_DIR = MEMORY_DIR / "_archive"
MANIFEST = ARCHIVE_DIR / "manifest.jsonl"

# Thresholds
STALE_MONTHS = 6
NEVER_REUSED_DAYS = 30


def get_file_age_days(file_path: Path) -> int:
    """Days since file was created."""
    fm, _ = parse_frontmatter(file_path.read_text(encoding="utf-8", errors="replace"))
    created = fm.get("created", "")
    if not created:
        return 0
    try:
        dt = datetime.strptime(created, "%Y-%m-%d")
        return (datetime.now() - dt).days
    except ValueError:
        return 0


def get_days_since_used(file_path: Path) -> int | None:
    """Days since last used. None = never used."""
    fm, _ = parse_frontmatter(file_path.read_text(encoding="utf-8", errors="replace"))
    last_used = fm.get("last_used")
    if not last_used or last_used == "null":
        return None
    try:
        dt = datetime.strptime(last_used, "%Y-%m-%d")
        return (datetime.now() - dt).days
    except ValueError:
        return None


def is_stale(file_path: Path) -> tuple[bool, str]:
    """Return (is_stale, reason)."""
    fm, _ = parse_frontmatter(file_path.read_text(encoding="utf-8", errors="replace"))
    reuses = int(fm.get("reuses", "0"))
    days_unused = get_days_since_used(file_path)
    file_age = get_file_age_days(file_path)

    # Stale: unused 6+ months
    if days_unused is not None and days_unused >= STALE_MONTHS * 30:
        return True, f"unused {days_unused} days"

    # Stale: never reused after 30 days
    if reuses == 0 and file_age >= NEVER_REUSED_DAYS:
        return True, f"never reused, {file_age} days old"

    return False, ""


def archive_memories(dry_run: bool = True) -> None:
    """Find stale memories and archive them."""
    if not MEMORY_DIR.exists():
        print(f"No memory directory at {MEMORY_DIR}")
        return

    # Collect all memories from category dirs
    stale_files = []
    for cat_dir in MEMORY_DIR.iterdir():
        if not cat_dir.is_dir() or cat_dir.name.startswith("_"):
            continue
        for mf in cat_dir.glob("*.md"):
            if mf.name in ("INDEX.md", "MEMORY.md"):
                continue
            is_s, reason = is_stale(mf)
            if is_s:
                stale_files.append((mf, reason))

    if not stale_files:
        print("✓ No stale memories found")
        return

    print(f"Found {len(stale_files)} stale memories:\n")
    for mf, reason in stale_files:
        cat = mf.parent.name
        print(f"  {mf.name:40} ({cat:8}) — {reason}")

    if dry_run:
        print(f"\n(dry-run: use --commit to archive {len(stale_files)} memories)")
        return

    # Create archive structure
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    archived = []
    for src, reason in stale_files:
        cat = src.parent.name
        arc_cat_dir = ARCHIVE_DIR / cat
        arc_cat_dir.mkdir(parents=True, exist_ok=True)
        dest = arc_cat_dir / src.name

        # Move file
        src.rename(dest)
        archived.append({
            "ts": int(time.time()),
            "iso": datetime.now().isoformat(),
            "file": str(dest).replace(str(HOME), "~"),
            "reason": reason,
            "category": cat,
        })
        print(f"  → {cat}/_archive/{src.name}")

    # Log manifest
    try:
        with MANIFEST.open("a", encoding="utf-8") as f:
            for record in archived:
                f.write(json.dumps(record) + "\n")
    except OSError:
        pass

    print(f"\n✓ Archived {len(archived)} memories")
    print(f"  Manifest: {MANIFEST}")
    print(f"  Restore: grep '<filename>' {MANIFEST} | xargs mv ~/archive/...")


if __name__ == "__main__":
    dry = "--commit" not in sys.argv
    archive_memories(dry_run=dry)
