#!/usr/bin/env bash
# HOOK: sensei-greeter
# EVENT: SessionStart
# MATCHER: all
# PURPOSE: Run Sensei analyzer and display optimization recommendations
# EXIT: 0=allow (additive only)

set -e

PYTHON_BIN="python3"
ANALYZER="${HOME}/.claude/scripts/sensei-analyzer.py"
SUMMARY="${HOME}/.claude/scripts/sensei-summary.py"

# Run analyzer (updates analysis.json)
if [ -x "${ANALYZER}" ]; then
    "${PYTHON_BIN}" "${ANALYZER}" 2>/dev/null || true
fi

# Display summary (1 pattern for greeter)
if [ -x "${SUMMARY}" ]; then
    "${PYTHON_BIN}" "${SUMMARY}" 2>/dev/null || true
fi

exit 0
