#!/usr/bin/env bash
# Profile each registered hook by invoking it with a synthetic payload and
# measuring wall-clock duration. Prints a ranked table.
#
# Reads ${CLAUDE_PLUGIN_ROOT}/hooks.json (falls back to live plugin install).
# Does NOT modify any state — hooks may still write logs/alerts during the
# profile run, which is fine.
#
# Usage:
#   bin/profile-hooks.sh                 # profile all events
#   bin/profile-hooks.sh SessionStart    # only one event
set -euo pipefail

ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
HOOKS_FILE="$ROOT/hooks.json"

if [[ ! -f "$HOOKS_FILE" ]]; then
  echo "hooks.json not found at $HOOKS_FILE" >&2
  exit 1
fi

EVENTS=("$@")
if [[ ${#EVENTS[@]} -eq 0 ]]; then
  EVENTS=(SessionStart UserPromptSubmit PreToolUse Stop)
fi

synthetic_payload() {
  local event="$1"
  case "$event" in
    UserPromptSubmit)
      printf '{"prompt":"hello world test","session_id":"profile-test","cwd":"%s"}' "$PWD"
      ;;
    PreToolUse)
      printf '{"tool_name":"Bash","tool_input":{"command":"echo profile-test"},"session_id":"profile-test","cwd":"%s"}' "$PWD"
      ;;
    Stop)
      printf '{"session_id":"profile-test","cwd":"%s","transcript_path":""}' "$PWD"
      ;;
    SessionStart|*)
      printf '{"source":"startup","session_id":"profile-test","cwd":"%s"}' "$PWD"
      ;;
  esac
}

printf "%-18s %-40s %8s\n" "EVENT" "HOOK" "MS"
printf "%-18s %-40s %8s\n" "------" "----" "--"

for event in "${EVENTS[@]}"; do
  mapfile -t commands < <(python3 -c "
import json, os, sys
with open('$HOOKS_FILE') as f:
    data = json.load(f)
for group in data.get('hooks', {}).get('$event', []):
    for h in group.get('hooks', []):
        cmd = h.get('command', '')
        cmd = cmd.replace('\${CLAUDE_PLUGIN_ROOT}', '$ROOT')
        if cmd:
            print(cmd)
")
  payload="$(synthetic_payload "$event")"
  for cmd in "${commands[@]}"; do
    name="$(basename "$cmd")"
    if [[ ! -x "$cmd" ]]; then
      printf "%-18s %-40s %8s\n" "$event" "$name" "MISSING"
      continue
    fi
    # nanoseconds via date +%s%N
    start=$(date +%s%N)
    printf '%s' "$payload" | timeout 10 "$cmd" >/dev/null 2>&1 || true
    end=$(date +%s%N)
    ms=$(( (end - start) / 1000000 ))
    printf "%-18s %-40s %8d\n" "$event" "$name" "$ms"
  done
done
