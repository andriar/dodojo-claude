#!/usr/bin/env python3
"""Migrate memories to v2 (categorized + metadata).

Moves existing ~/.claude/memory/*.md into category subdirs.
Adds ID + metadata to all memories.

Dry-run by default: pass --commit to actually move files.
"""

import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from memory_categorizer import (
    auto_detect_category,
    parse_frontmatter,
    ensure_memory_has_metadata,
    DEFAULT_CATEGORIES,
)

HOME = Path.home()
MEMORY_DIR = HOME / ".claude" / "memory"


def migrate_memories(dry_run: bool = True) -> None:
    """Migrate memory files to categorized structure."""
    if not MEMORY_DIR.exists():
        print(f"No memory directory at {MEMORY_DIR}")
        return

    # Collect existing memories
    memory_files = [f for f in MEMORY_DIR.glob("*.md") if f.name != "INDEX.md"]
    if not memory_files:
        print("No memories to migrate")
        return

    print(f"Found {len(memory_files)} memories to migrate\n")

    moves = []
    for mf in memory_files:
        # Ensure metadata
        metadata = ensure_memory_has_metadata(mf)

        category = metadata.get("category", "general")

        # Validate category exists
        if category not in DEFAULT_CATEGORIES and category not in ["general", "patterns", "setup"]:
            category = "general"

        category_dir = MEMORY_DIR / category
        dest = category_dir / mf.name

        if dest == mf:
            print(f"  {mf.name:40} → {category}/ (already in place)")
        else:
            moves.append((mf, dest, category))
            print(f"  {mf.name:40} → {category}/")

    if not moves:
        print("\n✓ All memories already organized")
        return

    if dry_run:
        print(f"\n(dry-run: use --commit to actually move {len(moves)} files)")
        return

    print(f"\nMoving {len(moves)} memories...")
    for src, dest, cat in moves:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        print(f"  ✓ {src.name} → {cat}/")

    print("\n✓ Migration complete")
    print(f"  Categories: {', '.join(sorted(set(c for _, _, c in moves)))}")


if __name__ == "__main__":
    dry = "--commit" not in sys.argv
    migrate_memories(dry_run=dry)
