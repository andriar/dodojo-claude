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
export KAGAMI_COLOR=1
exec python3 "$SCRIPT_DIR/dodojo-greet.py"
