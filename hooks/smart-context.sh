#!/usr/bin/env bash
# HOOK: smart-context
# EVENT: UserPromptSubmit
# MATCHER: all
# PURPOSE: Rank memory files by relevance to prompt; inject top matches as context
# EXIT: 0=allow (always), output to stdout = appended to prompt context

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

set -e

# Read full hook stdin
INPUT=$(cat)

# Delegate scoring to python (handles JSON parse + TF-IDF-ish rank)
python3 "$SCRIPT_DIR/smart-context.py" <<<"$INPUT" || true

exit 0
