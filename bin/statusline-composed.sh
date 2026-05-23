#!/usr/bin/env bash
# Compose multiple statusline segments: dodojo + (optional) poke.
# Each segment runs independently. Failures degrade silently.
#
# Used as the Claude Code statusline command. Drains stdin once,
# replays JSON to each segment that wants it.
set -u

PAYLOAD=""
if [[ ! -t 0 ]]; then
  PAYLOAD="$(cat)"
fi

run_segment() {
  local cmd="$1"
  if [[ -z "$cmd" || ! -x "${cmd%% *}" ]]; then return; fi
  printf '%s' "$PAYLOAD" | eval "$cmd" 2>/dev/null || true
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DJ_OUT=$(run_segment "$SCRIPT_DIR/statusline.sh")

# Find latest poke install (version-agnostic)
POKE_BIN=$(ls -t "$HOME"/.claude/plugins/cache/pokemon-buddy-claude/poke/*/buddy-update.py 2>/dev/null | head -1)
POKE_OUT=""
if [[ -n "$POKE_BIN" && -f "$POKE_BIN" ]]; then
  POKE_OUT=$(printf '%s' "$PAYLOAD" | python3 "$POKE_BIN" statusline --plugin 2>/dev/null || true)
fi

# Join non-empty segments with " │ "
SEP=$'\033[2m │ \033[0m'
OUT=""
for seg in "$DJ_OUT" "$POKE_OUT"; do
  if [[ -n "$seg" ]]; then
    if [[ -n "$OUT" ]]; then
      OUT="${OUT}${SEP}${seg}"
    else
      OUT="$seg"
    fi
  fi
done
printf '%s' "$OUT"
