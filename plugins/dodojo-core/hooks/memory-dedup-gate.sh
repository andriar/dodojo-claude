#!/usr/bin/env bash
# HOOK: memory-dedup-gate
# EVENT: PreToolUse
# MATCHER: Write
# PURPOSE: Block creating a NEW memory *.md (under ~/.claude/memory) that is >=0.35 jaccard-similar to an existing memory; advise update instead
# EXIT: 0=allow, 2=block-with-message
# Default-ON. Set MEMGRAPH_GATE_DISABLED=1 to opt out.
[ -n "$MEMGRAPH_GATE_DISABLED" ] && exit 0
ENGINE="${CLAUDE_PLUGIN_ROOT}/skills/memory-graph/memory_graph.py"
[ -f "$ENGINE" ] || exit 0   # fail-open if engine missing
exec python3 "$ENGINE" gate
