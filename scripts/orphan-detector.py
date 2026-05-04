#!/usr/bin/env python3
"""
Q4: Smart Orphan Detection + Auto-Archive
Scores DoDojo memories, categorizes (active/dormant/orphan), archives stale ones
"""

import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

MEMORY_DIR = Path.home() / ".claude" / "memory"
ARCHIVE_DIR = MEMORY_DIR / "_archive"
MANIFEST_FILE = ARCHIVE_DIR / "manifest.json"

class OrphanDetector:
    def __init__(self):
        self.memories = {}
        self.orphans = []
        self.candidates = []
        self.active = []

    def load_memories(self):
        """Load all memory files with metadata"""
        if not MEMORY_DIR.exists():
            return

        for mfile in MEMORY_DIR.rglob("*.md"):
            if mfile.parent.name == "_archive":
                continue

            try:
                metadata = self._extract_metadata(mfile)
                self.memories[str(mfile)] = metadata
            except:
                continue

    def _extract_metadata(self, fpath):
        """Extract metadata from memory file frontmatter"""
        with open(fpath) as f:
            content = f.read()

        # Parse YAML frontmatter
        metadata = {
            'path': str(fpath),
            'name': fpath.stem,
            'size_kb': fpath.stat().st_size / 1024,
            'created': datetime.fromtimestamp(fpath.stat().st_ctime),
            'reuses': 0,
            'last_used': None,
            'category': 'general'
        }

        # Extract from frontmatter if present
        if content.startswith('---'):
            try:
                front_end = content[3:].index('---')
                front_matter = content[3:3+front_end]
                for line in front_matter.split('\n'):
                    if 'reuses:' in line:
                        metadata['reuses'] = int(line.split(':')[1].strip())
                    elif 'last_used:' in line:
                        date_str = line.split(':', 1)[1].strip()
                        metadata['last_used'] = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    elif 'category:' in line:
                        metadata['category'] = line.split(':')[1].strip()
            except:
                pass

        return metadata

    def calculate_score(self, metadata):
        """A: Calculate orphan score (0.0=orphan, 1.0=active)"""
        # Reuses weight (0.4)
        reuses = min(metadata['reuses'] / 5.0, 1.0)

        # Recency weight (0.4)
        last_used = metadata['last_used'] or metadata['created']
        days_old = (datetime.now() - last_used).days
        recency = max(1.0 - (days_old / 365.0), 0.0)

        # Size penalty (0.2)
        size_penalty = 0.8 if metadata['size_kb'] > 50 else 1.0

        score = (reuses * 0.4) + (recency * 0.4) + (size_penalty * 0.2)
        return min(max(score, 0.0), 1.0)

    def categorize(self, score):
        """B: Categorize by score"""
        if score > 0.7:
            return 'active'
        elif score > 0.3:
            return 'dormant'
        else:
            return 'orphan'

    def analyze_all(self):
        """Analyze all memories, categorize, detect orphans"""
        self.load_memories()

        for path, metadata in self.memories.items():
            score = self.calculate_score(metadata)
            category = self.categorize(score)

            result = {
                'path': path,
                'name': metadata['name'],
                'score': round(score, 2),
                'category': category,
                'reuses': metadata['reuses'],
                'last_used': metadata['last_used'].isoformat() if metadata['last_used'] else 'never',
                'size_kb': round(metadata['size_kb'], 1),
                'days_old': (datetime.now() - (metadata['last_used'] or metadata['created'])).days
            }

            if category == 'orphan':
                self.orphans.append(result)
            elif category == 'dormant':
                self.candidates.append(result)
            else:
                self.active.append(result)

        # Sort by score (lowest = most orphaned)
        self.orphans.sort(key=lambda x: x['score'])
        self.candidates.sort(key=lambda x: x['score'])
        self.active.sort(key=lambda x: -x['score'])

    def detect_high_confidence_orphans(self):
        """D: Find high-confidence orphans to auto-archive"""
        candidates_for_archive = []

        for orphan in self.orphans:
            # High confidence: never used + old
            if orphan['reuses'] == 0 and orphan['days_old'] > 60:
                confidence = 0.95
                reason = f"{orphan['days_old']}d old, 0 reuses"
            # Medium-high: very old + unused long time
            elif orphan['reuses'] == 0 and orphan['days_old'] > 90:
                confidence = 0.90
                reason = f"{orphan['days_old']}d old, 0 reuses"
            # Medium: old + low usage
            elif orphan['reuses'] <= 1 and orphan['days_old'] > 120:
                confidence = 0.70
                reason = f"{orphan['days_old']}d old, {orphan['reuses']} reuses"
            else:
                confidence = 0.0

            if confidence >= 0.90:
                candidates_for_archive.append({
                    **orphan,
                    'confidence': confidence,
                    'reason': reason,
                    'action': 'auto-archive'
                })

        return candidates_for_archive

    def show_report(self):
        """Display health report"""
        total = len(self.memories)
        active_pct = int(100 * len(self.active) / total) if total > 0 else 0
        dormant_pct = int(100 * len(self.candidates) / total) if total > 0 else 0
        orphan_pct = int(100 * len(self.orphans) / total) if total > 0 else 0

        print(f"\n{'='*60}")
        print(f"📊 MEMORY HEALTH REPORT")
        print(f"{'='*60}\n")

        print(f"Total files:        {total}")
        print(f"Active (>0.7):      {len(self.active)} ({active_pct}%)")
        print(f"Dormant (0.3-0.7):  {len(self.candidates)} ({dormant_pct}%)")
        print(f"Orphan (≤0.3):      {len(self.orphans)} ({orphan_pct}%)\n")

        # Show high-confidence candidates
        high_conf = self.detect_high_confidence_orphans()
        if high_conf:
            print(f"AUTO-ARCHIVE CANDIDATES (95%+ confidence): {len(high_conf)} files")
            for mem in high_conf[:5]:
                print(f"  • {mem['name']}.md ({mem['reason']}, {mem['size_kb']}KB)")
            if len(high_conf) > 5:
                print(f"  ... and {len(high_conf) - 5} more")

        # Show review candidates
        review = [m for m in self.candidates if m['score'] < 0.5]
        if review:
            print(f"\nREVIEW CANDIDATES (50-80% confidence): {len(review)} files")
            for mem in review[:5]:
                print(f"  • {mem['name']}.md ({mem['days_old']}d old, {mem['reuses']} reuses)")
            if len(review) > 5:
                print(f"  ... and {len(review) - 5} more")

        print(f"\n{'='*60}\n")

    def archive_memory(self, memory_path, dry_run=False):
        """D: Archive a memory file"""
        src = Path(memory_path)
        if not src.exists():
            return False

        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        dst = ARCHIVE_DIR / src.name

        if not dry_run:
            shutil.move(str(src), str(dst))
            self._update_manifest(src.name, 'archived')

        return True

    def _update_manifest(self, filename, action):
        """Track archive/restore in manifest"""
        manifest = {}
        if MANIFEST_FILE.exists():
            with open(MANIFEST_FILE) as f:
                manifest = json.load(f)

        if 'history' not in manifest:
            manifest['history'] = []

        manifest['history'].append({
            'timestamp': datetime.now().isoformat() + 'Z',
            'file': filename,
            'action': action
        })

        with open(MANIFEST_FILE, 'w') as f:
            json.dump(manifest, f, indent=2)

    def auto_archive(self, dry_run=True):
        """Auto-archive high-confidence orphans"""
        candidates = self.detect_high_confidence_orphans()

        if not candidates:
            print("No orphans to archive.")
            return 0

        print(f"\n{'='*60}")
        print(f"AUTO-ARCHIVE (dry-run: {dry_run})")
        print(f"{'='*60}\n")

        archived = 0
        for mem in candidates:
            action = "would archive" if dry_run else "archived"
            print(f"  {action}: {mem['name']}.md ({mem['reason']})")
            if not dry_run:
                self.archive_memory(mem['path'])
                archived += 1

        print(f"\n{archived} files archived.\n")
        return archived


def main():
    import sys

    detector = OrphanDetector()
    detector.analyze_all()

    if len(sys.argv) > 1 and sys.argv[1] == '--archive':
        dry_run = not ('--commit' in sys.argv)
        detector.show_report()
        detector.auto_archive(dry_run=dry_run)
    else:
        detector.show_report()


if __name__ == "__main__":
    main()
