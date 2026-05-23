#!/usr/bin/env bash
# HOOK: dodojo-log-session-stop
# EVENT: Stop
# MATCHER: all
# PURPOSE: Parse session transcript on Stop, log summary (tools, tokens, duration) to sessions-summary.jsonl
# EXIT: 0=allow (always; never blocks)

set -u

if [[ "${DODOJO_TELEMETRY_DISABLED:-0}" == "1" ]]; then
  exit 0
fi

SUMMARY_FILE="$HOME/.claude/dodojo/telemetry/session-summary.jsonl"
mkdir -p "$(dirname "$SUMMARY_FILE")" 2>/dev/null

PAYLOAD="$(cat || true)"

# Find most recent transcript for the active project
SESSION_ID=""
CWD=""
TRANSCRIPT=""
if command -v jq >/dev/null 2>&1; then
  SESSION_ID=$(printf '%s' "$PAYLOAD" | jq -r '.session_id // .sessionId // empty' 2>/dev/null)
  CWD=$(printf '%s' "$PAYLOAD" | jq -r '.cwd // empty' 2>/dev/null)
  TRANSCRIPT=$(printf '%s' "$PAYLOAD" | jq -r '.transcript_path // .transcriptPath // empty' 2>/dev/null)
fi

# Fallback: find latest transcript in projects/
if [[ -z "$TRANSCRIPT" || ! -f "$TRANSCRIPT" ]]; then
  TRANSCRIPT=$(find "$HOME/.claude/projects" -name "*.jsonl" -type f -printf '%T@ %p\n' 2>/dev/null \
    | sort -rn | head -1 | cut -d' ' -f2-)
fi

if [[ -z "$TRANSCRIPT" || ! -f "$TRANSCRIPT" ]]; then
  exit 0
fi

# Parse via Python — pass transcript path as argv (fixes sensei bug)
SUMMARY_JSON=$(python3 - "$TRANSCRIPT" "$SESSION_ID" "$CWD" <<'PYEOF'
import json, sys, os
from collections import Counter
from datetime import datetime

transcript = sys.argv[1] if len(sys.argv) > 1 else None
session_id = sys.argv[2] if len(sys.argv) > 2 else ""
cwd = sys.argv[3] if len(sys.argv) > 3 else ""

if not transcript or not os.path.exists(transcript):
    sys.exit(0)

tools = Counter()
skills = Counter()
plugins = Counter()
prompts = 0
in_tokens = 0
out_tokens = 0
cache_read = 0
cache_write = 0
first_ts = None
last_ts = None

with open(transcript) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue

        ts = d.get('timestamp')
        if ts:
            if first_ts is None:
                first_ts = ts
            last_ts = ts

        msg_type = d.get('type', '')
        if msg_type == 'user':
            msg = d.get('message', {}) or {}
            content = msg.get('content', '')
            # If content is a string (user prompt) not a tool_result list
            if isinstance(content, str):
                prompts += 1
        elif msg_type == 'assistant':
            msg = d.get('message', {}) or {}
            usage = msg.get('usage', {}) or {}
            in_tokens += usage.get('input_tokens', 0) or 0
            out_tokens += usage.get('output_tokens', 0) or 0
            cache_read += usage.get('cache_read_input_tokens', 0) or 0
            cache_write += usage.get('cache_creation_input_tokens', 0) or 0
            content = msg.get('content', []) or []
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('type') == 'tool_use':
                        name = block.get('name', '')
                        tools[name] += 1
                        if name == 'Skill':
                            sk = (block.get('input') or {}).get('skill', '')
                            skills[sk] += 1
                            if ':' in sk:
                                plugins[sk.split(':', 1)[0]] += 1
                            else:
                                plugins['_custom'] += 1
                        elif name.startswith('mcp__'):
                            # mcp__<plugin>__<tool>
                            parts = name.split('__')
                            if len(parts) >= 2:
                                plugins[f'mcp:{parts[1]}'] += 1

# Compute duration
duration_s = None
if first_ts and last_ts:
    try:
        a = datetime.fromisoformat(first_ts.replace('Z', '+00:00'))
        b = datetime.fromisoformat(last_ts.replace('Z', '+00:00'))
        duration_s = int((b - a).total_seconds())
    except Exception:
        pass

summary = {
    'ts': datetime.now().astimezone().strftime('%Y-%m-%dT%H:%M:%S%z'),
    'session_id': session_id,
    'cwd': cwd,
    'repo': os.path.basename(cwd) if cwd else '',
    'transcript': transcript,
    'duration_s': duration_s,
    'prompts': prompts,
    'tokens': {
        'input': in_tokens,
        'output': out_tokens,
        'cache_read': cache_read,
        'cache_write': cache_write,
    },
    'tool_counts': dict(tools.most_common(20)),
    'skill_counts': dict(skills.most_common(20)),
    'plugin_counts': dict(plugins.most_common(20)),
}
print(json.dumps(summary))
PYEOF
)

if [[ -n "$SUMMARY_JSON" ]]; then
  printf '%s\n' "$SUMMARY_JSON" >> "$SUMMARY_FILE" 2>/dev/null || true
fi

exit 0
