#!/usr/bin/env bash
# DoDojo statusline segment. Pure read, zero tokens, <50ms.
# Outputs one line. Composable with other statusline scripts.
#
# Reads:  ~/.claude/dodojo/state/audit-stack.json (written by `dj audit`)
#         ~/.claude/dodojo/telemetry/session-summary.jsonl (latest session tokens)
#
# Output (default "clear" mode):
#   🪙 7.5K passive · ↑64K session · 2🪓 to prune
#   🪙 7.5K passive · ✓ clean
#
# Compact mode (DJ_STATUSLINE_MODE=compact):
#   dj 7.5K ↑64K · 2🪓
#   dj 7.5K ✓
#
# ENV:
#   DJ_STATUSLINE_MODE=clear|compact   default: clear
#   DJ_STATUSLINE_NOCOLOR=1            disable ANSI colors
#   DJ_STATUSLINE_NOICONS=1            plain text fallbacks

set -u

STATE="$HOME/.claude/dodojo/state/audit-stack.json"
MODE="${DJ_STATUSLINE_MODE:-clear}"
NOCOLOR="${DJ_STATUSLINE_NOCOLOR:-0}"
NOICONS="${DJ_STATUSLINE_NOICONS:-0}"

# Drain Claude Code's JSON payload (unused for now)
[[ -t 0 ]] || cat >/dev/null

if [[ ! -f "$STATE" ]]; then
  exit 0
fi

# Parse state + latest session summary
read -r PASSIVE PRUNES SESS_TOKENS < <(
  python3 - <<'PY' "$STATE" "$HOME/.claude/dodojo/telemetry/session-summary.jsonl"
import json, sys, os
try:
    s = json.load(open(sys.argv[1]))
    passive = s.get('total_passive_tokens', 0)
    prunes = s.get('prune_candidates', 0)
except Exception:
    passive, prunes = 0, 0

sess_total = 0
try:
    if os.path.exists(sys.argv[2]):
        last_line = None
        for line in open(sys.argv[2]):
            if line.strip():
                last_line = line
        if last_line:
            d = json.loads(last_line)
            t = d.get('tokens', {})
            sess_total = (t.get('input', 0) + t.get('output', 0)
                          + t.get('cache_read', 0) + t.get('cache_write', 0))
except Exception:
    pass

print(passive, prunes, sess_total)
PY
)

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

if [[ "$NOCOLOR" == "1" ]]; then
  G=""; Y=""; R=""; DIM=""; RESET=""
else
  G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'
  DIM=$'\033[2m'; RESET=$'\033[0m'
fi

color_for() {
  local t="$1"
  if   (( t < 8000 ));  then printf '%s' "$G"
  elif (( t < 12000 )); then printf '%s' "$Y"
  else                       printf '%s' "$R"
  fi
}

if [[ "$NOICONS" == "1" ]]; then
  COIN="\$"; AXE="x"; CHECK="ok"; UP="^"
else
  COIN="🪙"; AXE="🪓"; CHECK="✓"; UP="↑"
fi

PASSIVE_FMT=$(fmt "$PASSIVE")
PASSIVE_C=$(color_for "$PASSIVE")

case "$MODE" in
  compact)
    SEG="dj ${PASSIVE_C}${PASSIVE_FMT}${RESET}"
    if (( SESS_TOKENS > 0 )); then
      SEG="${SEG} ${DIM}${UP}$(fmt $SESS_TOKENS)${RESET}"
    fi
    if (( PRUNES > 0 )); then
      SEG="${SEG} ${DIM}·${RESET} ${PRUNES}${AXE}"
    else
      SEG="${SEG} ${G}${CHECK}${RESET}"
    fi
    ;;

  clear|*)
    SEG="${COIN} ${PASSIVE_C}${PASSIVE_FMT}${RESET} ${DIM}passive${RESET}"

    if (( SESS_TOKENS > 0 )); then
      SEG="${SEG} ${DIM}·${RESET} ${UP}$(fmt $SESS_TOKENS) ${DIM}session${RESET}"
    fi

    if (( PRUNES > 0 )); then
      noun="prune"
      (( PRUNES > 1 )) && noun="prunes"
      SEG="${SEG} ${DIM}·${RESET} ${Y}${PRUNES}${AXE}${RESET} ${DIM}to ${noun}${RESET}"
    else
      SEG="${SEG} ${DIM}·${RESET} ${G}${CHECK} clean${RESET}"
    fi
    ;;
esac

printf "%s" "$SEG"
