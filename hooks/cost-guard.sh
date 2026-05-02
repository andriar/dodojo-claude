#!/usr/bin/env bash
# HOOK: cost-guard
# EVENT: PreToolUse
# MATCHER: Bash|Read
# PURPOSE: Block obvious unbounded/runaway operations (find /, rm -rf /, grep -r /, Read /var/log without limit)
# EXIT: 0=allow, 2=block-with-message

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INPUT=$(cat)
python3 "$SCRIPT_DIR/cost-guard.py" <<<"$INPUT"
exit $?
