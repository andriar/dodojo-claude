#!/usr/bin/env bash
# HOOK: tips-display
# EVENT: SessionStart
# MATCHER: all
# PURPOSE: Display daily smart tip (context-aware + Sensei-driven)
# EXIT: 0=allow (additive only)

set -e

PYTHON_BIN="python3"
SELECTOR="${HOME}/.claude/scripts/tips-selector.py"

# Show daily tip
if [ -x "${SELECTOR}" ]; then
    "${PYTHON_BIN}" "${SELECTOR}" general 2>/dev/null || true
fi

exit 0
