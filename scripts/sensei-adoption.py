#!/usr/bin/env python3
"""
Sensei Adoption Tracking - tracks if user has implemented recommendations
"""

import json
from pathlib import Path
from datetime import datetime

SENSEI_DIR = Path.home() / ".claude" / "sensei"

def load_adoption():
    """Load adoption tracking data"""
    adoption_file = SENSEI_DIR / "adoption.json"
    if adoption_file.exists():
        with open(adoption_file) as f:
            return json.load(f)
    return {'recommendations': []}

def log_recommendation(pattern_type, suggestion, tokens_saved=None):
    """Log a recommendation shown to user"""
    adoption = load_adoption()

    recommendation = {
        'timestamp': datetime.now().isoformat() + 'Z',
        'type': pattern_type,
        'suggestion': suggestion,
        'tokens_saved': tokens_saved,
        'adopted': False,
        'adoption_date': None
    }

    adoption['recommendations'].append(recommendation)

    adoption_file = SENSEI_DIR / "adoption.json"
    with open(adoption_file, 'w') as f:
        json.dump(adoption, f, indent=2)

def mark_adopted(pattern_type):
    """Mark recommendation as adopted"""
    adoption = load_adoption()

    # Find last matching pattern and mark as adopted
    for rec in reversed(adoption.get('recommendations', [])):
        if rec['type'] == pattern_type and not rec['adopted']:
            rec['adopted'] = True
            rec['adoption_date'] = datetime.now().isoformat() + 'Z'
            break

    adoption_file = SENSEI_DIR / "adoption.json"
    with open(adoption_file, 'w') as f:
        json.dump(adoption, f, indent=2)

def show_adoption_status():
    """Show adoption tracking status"""
    adoption = load_adoption()
    recs = adoption.get('recommendations', [])

    if not recs:
        print("No recommendation history yet\n")
        return

    adopted = sum(1 for r in recs if r['adopted'])
    total = len(recs)

    print(f"\n{'='*50}")
    print(f"ADOPTION TRACKING")
    print(f"{'='*50}\n")

    print(f"✅ Adopted: {adopted}/{total}\n")

    # Group by type
    by_type = {}
    for r in recs:
        ptype = r['type']
        if ptype not in by_type:
            by_type[ptype] = {'total': 0, 'adopted': 0}
        by_type[ptype]['total'] += 1
        if r['adopted']:
            by_type[ptype]['adopted'] += 1

    for ptype, stats in sorted(by_type.items()):
        icon = '✓' if stats['adopted'] > 0 else ' '
        print(f"{icon} {ptype.replace('-', ' ').title()}: {stats['adopted']}/{stats['total']}")

    print()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--mark":
        if len(sys.argv) > 2:
            mark_adopted(sys.argv[2])
            print(f"✅ Marked {sys.argv[2]} as adopted\n")
    else:
        show_adoption_status()
