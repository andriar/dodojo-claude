#!/usr/bin/env python3
"""List memory archival candidates for Sensei weekly report.

Output: human-readable list of memories eligible for archival.
Exit: 0 (always; failure to read any memory doesn't break report).
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from memory_categorizer import parse_frontmatter

HOME = Path.home()
MEMORY_DIR = HOME / ".claude" / "memory"
STALE_MONTHS = 6
NEVER_REUSED_DAYS = 30


def format_age(days: int) -> str:
    if days < 30:
        return f"{days}d"
    elif days < 365:
        return f"{days // 30}mo"
    else:
        return f"{days // 365}y"


def main() -> int:
    if not MEMORY_DIR.exists():
        return 0

    candidates = []

    for cat_dir in MEMORY_DIR.iterdir():
        if not cat_dir.is_dir() or cat_dir.name.startswith("_"):
            continue
        for mf in cat_dir.glob("*.md"):
            if mf.name in ("INDEX.md", "MEMORY.md"):
                continue

            try:
                content = mf.read_text(encoding="utf-8", errors="replace")
                fm, _ = parse_frontmatter(content)
            except OSError:
                continue

            reuses = int(fm.get("reuses", "0"))
            created = fm.get("created", "")
            last_used = fm.get("last_used")

            # Compute age
            file_age_days = 0
            if created:
                try:
                    dt = datetime.strptime(created, "%Y-%m-%d")
                    file_age_days = (datetime.now() - dt).days
                except ValueError:
                    pass

            # Compute days since last use
            days_unused = None
            if last_used and last_used != "null":
                try:
                    dt = datetime.strptime(last_used, "%Y-%m-%d")
                    days_unused = (datetime.now() - dt).days
                except ValueError:
                    pass

            # Check stale conditions
            reason = None
            if days_unused is not None and days_unused >= STALE_MONTHS * 30:
                reason = f"unused {format_age(days_unused)}"
            elif reuses == 0 and file_age_days >= NEVER_REUSED_DAYS:
                reason = f"never used, {format_age(file_age_days)} old"

            if reason:
                name = fm.get("name", mf.stem)
                desc = fm.get("description", "")[:60]
                candidates.append({
                    "name": name,
                    "file": mf.name,
                    "category": cat_dir.name,
                    "reason": reason,
                    "description": desc,
                    "reuses": reuses,
                })

    if not candidates:
        print("No archival candidates found. Memory system healthy.")
        return 0

    print(f"**{len(candidates)} memory archival candidates:**")
    print()

    by_category = {}
    for c in candidates:
        cat = c["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(c)

    for cat in sorted(by_category.keys()):
        items = by_category[cat]
        print(f"- **{cat}/** ({len(items)} files)")
        for item in items:
            reuse_str = f", {item['reuses']} reuses" if item['reuses'] > 0 else ""
            print(f"  - `{item['file']}` — {item['reason']}{reuse_str}")
            if item['description']:
                print(f"    _{item['description']}_")

    print()
    print("**To archive:** `python3 ~/.claude/scripts/archive-stale-memories.py --commit`")
    print()
    print(f"**To restore:** entries logged in `~/.claude/memory/_archive/manifest.jsonl`")

    return 0


if __name__ == "__main__":
    sys.exit(main())
