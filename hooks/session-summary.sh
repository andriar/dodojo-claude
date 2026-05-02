#!/usr/bin/env bash
# HOOK: session-summary
# EVENT: Stop
# MATCHER: all
# PURPOSE: Record per-turn metrics (tool counts, files touched, char counts) to ~/.claude/sessions/YYYY-MM-DD.jsonl
# EXIT: 0=allow (always; failure-tolerant)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

set -e
INPUT=$(cat)
python3 "$SCRIPT_DIR/session-summary.py" <<<"$INPUT" || true
exit 0
