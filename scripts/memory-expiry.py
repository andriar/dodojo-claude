#!/usr/bin/env python3
"""
Scan memory files for `expires:` frontmatter. Report expired + expiring-soon.
Optionally archive expired to _archive/<YYYY-MM>/ and prune INDEX/MEMORY entries.

Usage:
  memory-expiry.py                    # report only
  memory-expiry.py --archive          # archive expired
  memory-expiry.py --warn-days 14     # widen soon-window (default 7)
"""
import argparse, datetime, pathlib, re, shutil, sys

HOME = pathlib.Path.home()
SCAN_DIRS = [
    HOME / ".claude" / "memory",
    *(HOME / ".claude" / "projects").glob("*/memory"),
]
INDEX_NAMES = {"INDEX.md", "MEMORY.md"}
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
EXPIRES_RE = re.compile(r"^expires:\s*(\d{4}-\d{2}-\d{2})\s*$", re.MULTILINE)


def parse_expires(path: pathlib.Path):
    try:
        text = path.read_text()
    except Exception:
        return None
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    em = EXPIRES_RE.search(m.group(1))
    if not em:
        return None
    try:
        return datetime.date.fromisoformat(em.group(1))
    except ValueError:
        return None


def find_index(memory_file: pathlib.Path) -> pathlib.Path | None:
    for name in INDEX_NAMES:
        candidate = memory_file.parent / name
        if candidate.exists():
            return candidate
    return None


def prune_index(index: pathlib.Path, filename: str) -> bool:
    text = index.read_text()
    pattern = re.compile(rf"^.*\]\({re.escape(filename)}\).*\n?", re.MULTILINE)
    new = pattern.sub("", text)
    if new != text:
        index.write_text(new)
        return True
    return False


def archive(path: pathlib.Path) -> pathlib.Path:
    bucket = path.parent / "_archive" / datetime.date.today().strftime("%Y-%m")
    bucket.mkdir(parents=True, exist_ok=True)
    dest = bucket / path.name
    shutil.move(str(path), str(dest))
    return dest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", action="store_true", help="move expired files to _archive/")
    ap.add_argument("--warn-days", type=int, default=7, help="flag files expiring within N days")
    args = ap.parse_args()

    today = datetime.date.today()
    soon_cutoff = today + datetime.timedelta(days=args.warn_days)

    expired, soon, dated = [], [], []
    for d in SCAN_DIRS:
        if not d.is_dir():
            continue
        for path in d.glob("*.md"):
            if path.name in INDEX_NAMES:
                continue
            exp = parse_expires(path)
            if exp is None:
                continue
            dated.append((path, exp))
            if exp < today:
                expired.append((path, exp))
            elif exp <= soon_cutoff:
                soon.append((path, exp))

    print(f"Memory expiry scan — {today.isoformat()}")
    print(f"  Files with expires:  {len(dated)}")
    print(f"  Expired:             {len(expired)}")
    print(f"  Expiring ≤{args.warn_days}d:        {len(soon)}")
    print()

    if soon:
        print("=== Expiring soon ===")
        for p, e in sorted(soon, key=lambda x: x[1]):
            days = (e - today).days
            print(f"  {e.isoformat()}  (+{days}d)  {p}")
        print()

    if expired:
        print("=== Expired ===")
        for p, e in sorted(expired, key=lambda x: x[1]):
            days = (today - e).days
            print(f"  {e.isoformat()}  (-{days}d)  {p}")
        print()

        if args.archive:
            print("=== Archiving ===")
            for p, _ in expired:
                idx = find_index(p)
                dest = archive(p)
                pruned = prune_index(idx, p.name) if idx else False
                idx_note = f" + pruned {idx.name}" if pruned else ""
                print(f"  → {dest}{idx_note}")
        else:
            print("Run with --archive to move + prune INDEX entries.")

    return 0 if not expired or args.archive else 0


if __name__ == "__main__":
    sys.exit(main())
