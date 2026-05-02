#!/usr/bin/env bash
# HOOK: dodojo-greet
# EVENT: SessionStart
# MATCHER: .*
# PURPOSE: Consolidated visual greeter — emits systemMessage JSON for user-visible greeting
# EXIT: 0=allow
#
# Env vars:
#   KAGAMI_COLOR=1   force ANSI color in output (default on for SessionStart)
#   KAGAMI_SILENT=1  skip additionalContext payload (keep systemMessage); cuts ~400 tokens/session

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export KAGAMI_COLOR=1
OUTPUT="$(python3 "$SCRIPT_DIR/dodojo-greet.py" 2>/dev/null || true)"

if [ -z "$OUTPUT" ]; then
  exit 0
fi

ADDITIONAL=""
if [ "${KAGAMI_SILENT:-0}" != "1" ]; then
  ADDITIONAL="$OUTPUT"
fi

python3 - "$OUTPUT" "$ADDITIONAL" <<'PY'
import json, sys
out = {"systemMessage": sys.argv[1]}
if sys.argv[2]:
    out["hookSpecificOutput"] = {
        "hookEventName": "SessionStart",
        "additionalContext": sys.argv[2],
    }
print(json.dumps(out))
PY

exit 0
