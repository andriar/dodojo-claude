#!/usr/bin/env bash
# HOOK: sensei-greet
# EVENT: SessionStart
# MATCHER: all
# PURPOSE: Surface pending Sensei recommendations at session start.
# EXIT: 0=allow (always), stdout = injected context

set -u

# Honor env vars set in ~/.claude/settings.json (SENSEI_*).
STATE_DIR="${SENSEI_STATE:-$HOME/.claude/dodojo/sensei}"
VAULT="${SENSEI_VAULT:-$HOME/sensei-reports}"
DRAFTS="$HOME/.claude/skills/_drafts"

# Resolve sensei skill home — prefer plugin root, then env, then version-glob fallback.
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -d "$CLAUDE_PLUGIN_ROOT/skills/sensei" ]; then
    HOME_DIR="$CLAUDE_PLUGIN_ROOT/skills/sensei"
elif [ -n "${SENSEI_HOME:-}" ] && [ -d "$SENSEI_HOME" ]; then
    HOME_DIR="$SENSEI_HOME"
else
    HOME_DIR=$(ls -1d "$HOME"/.claude/plugins/cache/dodojo/dodojo/*/skills/sensei 2>/dev/null | sort -V | tail -1)
fi

FEEDBACK="$STATE_DIR/feedback.jsonl"
LAST_SCORED="$STATE_DIR/last_scored.json"

# Bail silently if Sensei state never initialized
[ -d "$STATE_DIR" ] || exit 0

# 1. Newest weekly report
latest_report=$(ls -t "$VAULT"/weekly-*.md 2>/dev/null | head -1)
report_age_days=999
if [ -n "$latest_report" ]; then
    report_age_days=$(( ( $(date +%s) - $(stat -c %Y "$latest_report") ) / 86400 ))
fi

# 2. Count pending recs (top patterns not in feedback yet)
pending_count=0
top_recs=""
if [ -f "$LAST_SCORED" ] && command -v python3 >/dev/null; then
    pending_count=$(python3 -c "
import json
from pathlib import Path
ls = json.loads(Path('$LAST_SCORED').read_text())
fb_path = Path('$FEEDBACK')
decided = set()
if fb_path.exists():
    for line in fb_path.read_text().splitlines():
        if line.strip():
            decided.add(json.loads(line).get('pattern_id'))
acts = [p for p in ls.get('patterns', []) if not p.get('informational') and p['id'] not in decided]
print(len(acts))
" 2>/dev/null)

    top_recs=$(python3 -c "
import json
from pathlib import Path
ls = json.loads(Path('$LAST_SCORED').read_text())
fb_path = Path('$FEEDBACK')
decided = set()
if fb_path.exists():
    for line in fb_path.read_text().splitlines():
        if line.strip():
            decided.add(json.loads(line).get('pattern_id'))
acts = [p for p in ls.get('patterns', []) if not p.get('informational') and p['id'] not in decided][:3]
for p in acts:
    print(f\"  {p['score']:>5} | {p['id']:30s} | {p['suggestion'][:70]}\")
" 2>/dev/null)
fi

# 3. Drafts pending graduation
draft_count=0
draft_list=""
if [ -d "$DRAFTS" ]; then
    draft_count=$(ls -1 "$DRAFTS" 2>/dev/null | wc -l)
    draft_list=$(ls -1 "$DRAFTS" 2>/dev/null | head -3 | sed 's/^/  - /')
fi

# 4. Stale outcomes (accepts >14d old, no skill graduated)
stale_count=0
if [ -n "$HOME_DIR" ] && [ -f "$HOME_DIR/scripts/outcome.py" ]; then
    stale_count=$(python3 "$HOME_DIR/scripts/outcome.py" 2>/dev/null | grep -cE "^(✗|△)" 2>/dev/null || true)
    stale_count=${stale_count:-0}
fi

# Skip greeting if nothing actionable
[ "$pending_count" -eq 0 ] && [ "$draft_count" -eq 0 ] && [ "$stale_count" -eq 0 ] && exit 0

cat <<EOF
[sensei-greet] State summary at session start:
- Latest weekly report: ${latest_report:-(none yet)} (age: ${report_age_days}d)
- Pending recommendations awaiting decision: ${pending_count}
- Drafts in _drafts/ awaiting graduation: ${draft_count}
- Stale/abandoned acceptances flagged: ${stale_count}

EOF

if [ "$pending_count" -gt 0 ] && [ -n "$top_recs" ]; then
    cat <<EOF
Top pending recs (score | id | suggestion):
$top_recs

EOF
fi

if [ "$draft_count" -gt 0 ]; then
    cat <<EOF
Drafts pending graduation:
$draft_list

EOF
fi

cat <<EOF
ACTION: Surface this to user at start of conversation. Ask which they want to handle:
  (a) review pending recs → show table, accept/reject via decide.py
  (b) graduate a draft skill → review _drafts/<name>/SKILL.md, implement, move to skills/
  (c) check stale outcomes → run outcome.py + take action
  (d) skip — proceed with user's actual request
Be concise — one short line per option.
EOF
