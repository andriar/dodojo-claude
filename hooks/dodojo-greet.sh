#!/usr/bin/env bash
# HOOK: dodojo-greet
# EVENT: SessionStart
# PURPOSE: Consolidated visual greeter — plain stdout for visible system message
# EXIT: 0=allow

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/dodojo-greet.py" || true
exit 0
