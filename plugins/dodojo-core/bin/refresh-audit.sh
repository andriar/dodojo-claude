#!/usr/bin/env bash
# HOOK: dodojo-refresh-audit
# EVENT: SessionStart
# MATCHER: all
# PURPOSE: Refresh ~/.claude/dodojo/state/audit-stack.json so statusline stays current.
# EXIT: 0 always; runs audit in background, never blocks session start, never injects context.
set -u

# Resolve script dir — works whether plugin uses $CLAUDE_PLUGIN_ROOT or symlinked
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Detach completely — no stdout, no stderr, no waiting
nohup python3 "$SCRIPT_DIR/audit-stack.py" \
  >/dev/null 2>&1 </dev/null &
disown 2>/dev/null || true

exit 0
