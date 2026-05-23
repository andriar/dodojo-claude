#!/usr/bin/env bash
# HOOK: dodojo-greeter-lean
# EVENT: SessionStart
# MATCHER: all
# PURPOSE: Tiny session greeter — silent when stack is clean, prints ONE line
#          of actionable info when there is something to act on. Costs <30 tokens
#          when speaking, 0 tokens when silent.
# EXIT: 0 always (never blocks)
#
# RUNS AUDIT INLINE so the greeter always reads fresh state.
# Previously a background `refresh-audit.sh` was used, but the greeter
# read stale state because the background audit hadn't finished yet.
# Now audit is synchronous (~200ms) — worth the startup cost for accuracy.
#
# Reads: ~/.claude/dodojo/state/audit-stack.json (after fresh audit)
# Outputs: one line to stdout → Claude Code injects as additionalContext

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE="$HOME/.claude/dodojo/state/audit-stack.json"

# Drain stdin
[[ -t 0 ]] || cat >/dev/null

# Refresh state if stale (>5 min old) or missing. Otherwise reuse — fast.
# Suppress audit stdout (we don't want its summary as greeter output).
NEEDS_REFRESH=1
if [[ -f "$STATE" ]]; then
  AGE=$(( $(date +%s) - $(stat -c %Y "$STATE" 2>/dev/null || echo 0) ))
  (( AGE < 300 )) && NEEDS_REFRESH=0
fi

if (( NEEDS_REFRESH )); then
  python3 "$SCRIPT_DIR/audit-stack.py" >/dev/null 2>&1 || true
fi

# Silent if state still missing (audit failed)
if [[ ! -f "$STATE" ]]; then
  exit 0
fi

# Surface the most-actionable signal — one line, ~15 tokens max
python3 - "$STATE" <<'PY' || true
import json, sys
try:
    s = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(0)

total = s.get('total_passive_tokens', 0)
prunes = s.get('prune_candidates', 0)

if total >= 12000:
    print(f"🥷 dj: passive load high ({total:,} tokens/session) — `dj audit` to investigate")
elif prunes >= 3:
    print(f"🥷 dj: {prunes} prune candidates — `dj prune` to clean up")
elif prunes >= 1:
    print(f"🥷 dj: {prunes} prune candidate{'' if prunes==1 else 's'} — `dj prune --dry-run`")
# else: silent. Stack is clean.
PY
