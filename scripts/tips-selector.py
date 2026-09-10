#!/usr/bin/env python3
"""
Tips Selector - Smart tip system with context awareness + Sensei integration
"""

import json
import os
import random
from pathlib import Path
from datetime import datetime
from hashlib import md5

USER_DATA = Path(os.environ.get("DODOJO_DATA") or str(Path.home() / ".claude"))


def _resolve_tips_file() -> Path:
    """First existing candidate wins.

    The script is installed to ~/.claude/scripts/ but tips.json ships with the
    plugin, so a `__file__`-relative path only works from a repo/plugin
    checkout. Every candidate is listed explicitly instead of assuming one
    layout — a wrong guess here fails silently as "no tips at all".
    """
    env = os.environ.get("DODOJO_TIPS_FILE")
    if env:
        return Path(env)

    candidates = [
        # repo / plugin checkout: <root>/scripts/ + <root>/data/
        Path(__file__).resolve().parent.parent / "data" / "tips.json",
    ]
    # installed plugin cache: ~/.claude/plugins/cache/<mkt>/<plug>/<ver>/data/tips.json
    candidates.extend(sorted(
        (USER_DATA / "plugins" / "cache").glob("*/*/*/data/tips.json"), reverse=True))
    # legacy dev checkout
    candidates.append(Path.home() / "Development/Labs/DoDojo-claude/data/tips.json")

    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


TIPS_FILE = _resolve_tips_file()
FEEDBACK_FILE = USER_DATA / "dodojo" / "tips-feedback.jsonl"
SENSEI_ANALYSIS = USER_DATA / "sensei" / "analysis.json"

class TipsSelector:
    def __init__(self):
        self.tips = self._load_tips()
        self.feedback = self._load_feedback()
        self.sensei_pattern = self._load_sensei_pattern()

    def _load_tips(self):
        """Load tips from tips.json"""
        try:
            with open(TIPS_FILE) as f:
                data = json.load(f)
                return data.get('tips', [])
        except:
            return []

    def _load_feedback(self):
        """Load user feedback ratings"""
        feedback = {}
        FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

        if FEEDBACK_FILE.exists():
            with open(FEEDBACK_FILE) as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        tip_id = record['tip_id']
                        if tip_id not in feedback:
                            feedback[tip_id] = {'helpful': 0, 'unhelpful': 0}

                        if record.get('rating') == '👍':
                            feedback[tip_id]['helpful'] += 1
                        elif record.get('rating') == '👎':
                            feedback[tip_id]['unhelpful'] += 1
                    except:
                        continue

        return feedback

    def _load_sensei_pattern(self):
        """Load latest Sensei pattern"""
        try:
            with open(SENSEI_ANALYSIS) as f:
                analysis = json.load(f)
                patterns = analysis.get('patterns', [])
                return patterns[0] if patterns else None
        except:
            return None

    def _detect_context(self, cwd=None):
        """Detect context from environment/activity"""
        # This would be called with session context
        # For now, return 'general' - greeter will pass context
        return 'general'

    def _get_sensei_tip(self):
        """Generate tip from Sensei pattern"""
        if not self.sensei_pattern:
            return None

        ptype = self.sensei_pattern.get('type', '')

        # Map patterns to tip suggestions
        if ptype == 'repeated-file-reads':
            file = self.sensei_pattern.get('file', 'file')
            reads = self.sensei_pattern.get('reads_count', 0)
            return {
                'id': 'sensei_tip',
                'text': f"🔴 SENSEI: {file} read {reads}× this week. Try /dodojo:recall instead.",
                'link': '/dodojo:recall',
                'category': 'sensei',
                'helpfulness': 0.7  # Boost Sensei tips
            }
        elif ptype == 'follow-up-chain':
            avg = self.sensei_pattern.get('avg_chain_length', 0)
            return {
                'id': 'sensei_tip',
                'text': f"🔴 SENSEI: {avg:.1f} clarifications per task. Use better prompt structure.",
                'link': 'prompting',
                'category': 'sensei',
                'helpfulness': 0.7
            }
        elif ptype == 'tool-misuse':
            tool = self.sensei_pattern.get('tool_used', '')
            alt = self.sensei_pattern.get('alternative', '')
            return {
                'id': 'sensei_tip',
                'text': f"🔴 SENSEI: Use {alt} instead of {tool}. Cheaper.",
                'link': alt.lower(),
                'category': 'sensei',
                'helpfulness': 0.7
            }

        return None

    def _weight_tip(self, tip):
        """Calculate selection weight for tip"""
        weight = 1.0

        # Weight by helpfulness score
        tip_id = tip.get('id', '')
        if tip_id in self.feedback:
            fb = self.feedback[tip_id]
            total = fb['helpful'] + fb['unhelpful']
            if total > 0:
                rate = fb['helpful'] / total
                if rate > 0.7:
                    weight *= 1.5  # Boost helpful tips
                elif rate < 0.3:
                    weight *= 0.5  # Reduce unhelpful tips

        return weight

    def select_tip(self, category='general', context_cwd=None, exclude_recent=None):
        """Select a tip based on category + feedback weighting"""

        # If Sensei detected a pattern, show that first
        sensei_tip = self._get_sensei_tip()
        if sensei_tip:
            return sensei_tip

        # Filter by category
        candidates = [t for t in self.tips if t.get('category') == category]

        # Fallback to general if no candidates
        if not candidates:
            candidates = [t for t in self.tips if t.get('category') == 'general']

        if not candidates:
            return None

        # Weight by helpfulness + randomize selection
        weights = [self._weight_tip(t) for t in candidates]
        total_weight = sum(weights)

        if total_weight == 0:
            return random.choice(candidates)

        # Weighted random selection
        pick = random.choices(candidates, weights=weights, k=1)[0]
        return pick

    def format_tip(self, tip):
        """Format tip for display"""
        if not tip:
            return None

        text = tip.get('text', '')
        link = tip.get('link', '')

        # Add feedback prompt
        output = f"💡 {text}"
        if link:
            output += f" ({link})"
        output += "\n   [👍 helpful] [👎 not helpful]"

        return output

    def log_tip_shown(self, tip):
        """Log that a tip was shown"""
        FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

        record = {
            'timestamp': datetime.now().isoformat() + 'Z',
            'tip_id': tip.get('id', ''),
            'text': tip.get('text', ''),
            'category': tip.get('category', ''),
            'shown': True,
            'rating': None
        }

        with open(FEEDBACK_FILE, 'a') as f:
            f.write(json.dumps(record) + '\n')

    def log_rating(self, tip_id, rating):
        """Log user rating (👍 or 👎)"""
        FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)

        record = {
            'timestamp': datetime.now().isoformat() + 'Z',
            'tip_id': tip_id,
            'rating': rating  # '👍' or '👎'
        }

        with open(FEEDBACK_FILE, 'a') as f:
            f.write(json.dumps(record) + '\n')


def show_daily_tip(category='general'):
    """Show daily tip (deterministic by user + date)"""
    selector = TipsSelector()

    # Seed by user + date (deterministic but changes daily)
    import os
    user_id = os.getenv('USER', 'user')
    today = datetime.now().strftime('%Y-%m-%d')
    seed = int(md5(f"{user_id}:{today}".encode()).hexdigest(), 16)
    random.seed(seed)

    tip = selector.select_tip(category=category)
    if tip:
        selector.log_tip_shown(tip)
        formatted = selector.format_tip(tip)
        if formatted:
            print(formatted)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--feedback":
        # Log feedback: python3 tips-selector.py --feedback tip_id rating
        if len(sys.argv) > 3:
            selector = TipsSelector()
            selector.log_rating(sys.argv[2], sys.argv[3])
            print(f"✅ Rated {sys.argv[2]} as {sys.argv[3]}")
    else:
        # Show daily tip
        category = sys.argv[1] if len(sys.argv) > 1 else 'general'
        show_daily_tip(category=category)
