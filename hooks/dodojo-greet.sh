#!/usr/bin/env bash
# HOOK: dodojo-greet
# EVENT: SessionStart
# PURPOSE: Consolidated visual greeter — emits systemMessage JSON for user-visible greeting
# EXIT: 0=allow

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT="$(python3 "$SCRIPT_DIR/dodojo-greet.py" 2>/dev/null || true)"

if [ -z "$OUTPUT" ]; then
  exit 0
fi

python3 - "$OUTPUT" <<'PY'
import json, sys
print(json.dumps({
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": sys.argv[1]
  },
  "systemMessage": sys.argv[1]
}))
PY

exit 0
