#!/usr/bin/env bash
# HOOK: dodojo-greeter-lean
# EVENT: SessionStart
# MATCHER: all
# PURPOSE: Tiny session greeter — silent when stack is clean, prints ONE line of
#          actionable info when there is something to act on. Costs <30 tokens
#          when speaking, 0 tokens when silent.
# EXIT: 0 always (never blocks)
#
# Reads: ~/.claude/dodojo/state/audit-stack.json (written by audit-stack.py)
# Outputs: one line to stdout → Claude Code injects as additionalContext

set -u

STATE="$HOME/.claude/dodojo/state/audit-stack.json"

# Drain stdin (Claude Code's payload), unused here
[[ -t 0 ]] || cat >/dev/null

# Silent if no state yet
if [[ ! -f "$STATE" ]]; then
  exit 0
fi

# Parse — pick the one most-actionable signal to surface
python3 - "$STATE" <<'PY' || true
import json, sys
try:
    s = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(0)

total = s.get('total_passive_tokens', 0)
prunes = s.get('prune_candidates', 0)
plugin_count = s.get('plugin_count', 0)

# Priority: high passive load > prune candidates > nothing
# Each branch outputs exactly ONE line, total <= ~30 tokens.

if total >= 12000:
    print(f"🥷 dj: passive load high ({total:,} tokens/session) — `dj audit` to investigate")
elif prunes >= 3:
    print(f"🥷 dj: {prunes} prune candidates — `dj prune` to clean up")
elif prunes >= 1:
    print(f"🥷 dj: {prunes} prune candidate{'' if prunes==1 else 's'} — `dj prune --dry-run`")
# else: silent. Stack is clean. No greeting.
PY
