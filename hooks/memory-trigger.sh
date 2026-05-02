#!/usr/bin/env bash
# HOOK: memory-trigger
# EVENT: UserPromptSubmit
# MATCHER: all
# PURPOSE: Detect save/remember/directive phrases in prompt; nudge Claude to invoke auto-reflect rule
# EXIT: 0=allow (always), output to stdout = appended to prompt context

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

set -e
INPUT=$(cat)
python3 "$SCRIPT_DIR/memory-trigger.py" <<<"$INPUT" || true
exit 0
