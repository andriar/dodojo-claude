#!/usr/bin/env bash
# DoDojo statusline segment. Pure read, zero tokens, <50ms.
# Outputs one line. Composable with other statusline scripts.
#
# Reads: ~/.claude/dodojo/state/audit-stack.json (written by `dj audit`)
# Output: "dj 8.6K · 4 prunes"  or  "dj 8.6K ✓"  or empty if no state
#
# ENV:
#   DJ_STATUSLINE_NOCOLOR=1   disable ANSI colors
#   DJ_STATUSLINE_PREFIX=...   override "dj" prefix (e.g. "🥷")

set -u

STATE="$HOME/.claude/dodojo/state/audit-stack.json"
PREFIX="${DJ_STATUSLINE_PREFIX:-dj}"

# Drain Claude Code's JSON payload from stdin (we don't currently use it)
[[ -t 0 ]] || cat >/dev/null

if [[ ! -f "$STATE" ]]; then
  exit 0
fi

# Parse state file
read -r TOTAL PRUNES SESS_TOKENS < <(
  python3 - <<'PY' "$STATE" "$HOME/.claude/dodojo/telemetry/session-summary.jsonl"
import json, sys, os
state_path = sys.argv[1]
summary_path = sys.argv[2]
try:
    s = json.load(open(state_path))
    total = s.get('total_passive_tokens', 0)
    prunes = s.get('prune_candidates', 0)
except Exception:
    total, prunes = 0, 0

# Latest session token cost
sess_total = 0
try:
    if os.path.exists(summary_path):
        last_line = None
        with open(summary_path) as f:
            for line in f:
                if line.strip():
                    last_line = line
        if last_line:
            d = json.loads(last_line)
            t = d.get('tokens', {})
            sess_total = (t.get('input', 0) + t.get('output', 0)
                          + t.get('cache_read', 0) + t.get('cache_write', 0))
except Exception:
    pass

print(total, prunes, sess_total)
PY
)

# Format token count compactly: 8600 → 8.6K, 12000 → 12K, 1500000 → 1.5M
fmt() {
  local n="$1"
  if (( n >= 1000000 )); then
    LC_NUMERIC=C awk -v n="$n" 'BEGIN{printf "%.1fM", n/1000000}'
  elif (( n >= 1000 )); then
    LC_NUMERIC=C awk -v n="$n" 'BEGIN{printf "%.1fK", n/1000}'
  else
    printf "%d" "$n"
  fi
}

# Color thresholds for passive load
color_for() {
  local t="$1"
  if [[ "${DJ_STATUSLINE_NOCOLOR:-0}" == "1" ]]; then echo ""; return; fi
  if   (( t < 8000 ));  then echo $'\033[32m'   # green
  elif (( t < 12000 )); then echo $'\033[33m'   # yellow
  else                       echo $'\033[31m'   # red
  fi
}
RESET=$'\033[0m'
DIM=$'\033[2m'

C=$(color_for "$TOTAL")
PASSIVE_FMT=$(fmt "$TOTAL")

# Build segment
SEG="${PREFIX} ${C}${PASSIVE_FMT}${RESET}"

# Add session-cost if available (cumulative this conversation)
if (( SESS_TOKENS > 0 )); then
  SESS_FMT=$(fmt "$SESS_TOKENS")
  SEG="${SEG} ${DIM}↑${SESS_FMT}${RESET}"
fi

# Alert if prunes available
if (( PRUNES > 0 )); then
  SEG="${SEG} ${DIM}·${RESET} ${PRUNES}🪓"
else
  SEG="${SEG} ✓"
fi

printf "%s" "$SEG"
