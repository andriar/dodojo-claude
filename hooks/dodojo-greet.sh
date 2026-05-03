#!/usr/bin/env bash
# HOOK: dodojo-greet
# EVENT: SessionStart
# MATCHER: .*
# PURPOSE: Consolidated visual greeter — prints ANSI banner directly to stdout
# EXIT: 0=allow
#
# Env vars:
#   KAGAMI_COLOR=1   force ANSI color in output (default on for SessionStart)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Mode gate (set by /dodojo:init wizard, stored in settings.json env block):
#   terminal — greeter rendered pre-launch via shell wrapper; hook is a no-op
#   inline   — greeter injected into Claude's context via stdout (~30 lines/session)
#   off      — greeter disabled everywhere
# Default = terminal (zero token cost). User opts into inline explicitly.
mode="${DODOJO_GREETER_MODE:-terminal}"
case "$mode" in
  inline) ;;
  *) exit 0 ;;
esac

# Color disabled: stdout goes to Claude as additionalContext, ANSI shows literal.
export KAGAMI_COLOR=0
exec python3 "$SCRIPT_DIR/dodojo-greet.py"
