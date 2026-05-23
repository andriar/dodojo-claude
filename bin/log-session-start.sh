#!/usr/bin/env bash
# HOOK: dodojo-log-session-start
# EVENT: SessionStart
# MATCHER: all
# PURPOSE: Log each session start to ~/.claude/dodojo/telemetry/sessions.jsonl for ROI denominator
# EXIT: 0=allow (always; this hook never blocks)

set -u

if [[ "${DODOJO_TELEMETRY_DISABLED:-0}" == "1" ]]; then
  exit 0
fi

TELEMETRY_FILE="$HOME/.claude/dodojo/telemetry/sessions.jsonl"
mkdir -p "$(dirname "$TELEMETRY_FILE")" 2>/dev/null

PAYLOAD="$(cat || true)"

if command -v jq >/dev/null 2>&1; then
  SESSION_ID=$(printf '%s' "$PAYLOAD" | jq -r '.session_id // .sessionId // empty' 2>/dev/null)
  CWD=$(printf '%s' "$PAYLOAD" | jq -r '.cwd // empty' 2>/dev/null)
  SOURCE=$(printf '%s' "$PAYLOAD" | jq -r '.source // empty' 2>/dev/null)
else
  SESSION_ID=$(printf '%s' "$PAYLOAD" | grep -oE '"sessionId"\s*:\s*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
  CWD=""
  SOURCE=""
fi

TS="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"
REPO="${CWD:+$(basename "$CWD")}"

printf '{"ts":"%s","session_id":"%s","cwd":"%s","repo":"%s","source":"%s"}\n' \
  "$TS" "$SESSION_ID" "$CWD" "$REPO" "$SOURCE" \
  >> "$TELEMETRY_FILE" 2>/dev/null || true

exit 0
