#!/usr/bin/env bash
# HOOK: skill-suggest
# EVENT: UserPromptSubmit
# MATCHER: all
# PURPOSE: Score custom skills (~/.claude/skills/*/SKILL.md) against prompt; hint top match
# EXIT: 0=allow (always), output to stdout = appended to prompt context

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

set -e
INPUT=$(cat)
python3 "$SCRIPT_DIR/skill-suggest.py" <<<"$INPUT" || true
exit 0
