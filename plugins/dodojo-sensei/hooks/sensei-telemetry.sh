#!/usr/bin/env bash
# HOOK: sensei-telemetry
# EVENT: Stop
# MATCHER: all
# PURPOSE: Capture session telemetry (prompts, tokens, tools) for Sensei pattern analysis
# EXIT: 0=allow, 2=block-with-message

set -e

SENSEI_DIR="${HOME}/.claude/sensei"
mkdir -p "${SENSEI_DIR}"

# Read session data from stdin (JSON)
STDIN=$(cat)

# Extract session ID and CWD from hook context
SESSION_ID=$(echo "${STDIN}" | jq -r '.sessionId // empty' 2>/dev/null || echo "unknown")
CWD=$(echo "${STDIN}" | jq -r '.cwd // empty' 2>/dev/null || echo "$(pwd)")

# Location of transcript for this session
# Claude Code stores transcripts at ~/.claude/projects/<proj>/<uuid>.jsonl
TRANSCRIPT_DIR="${HOME}/.claude/projects"
if [ ! -d "${TRANSCRIPT_DIR}" ]; then
  exit 0  # No transcript directory, skip
fi

# Find most recent .jsonl file in projects (the current session transcript)
TRANSCRIPT=$(find "${TRANSCRIPT_DIR}" -name "*.jsonl" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

if [ -z "${TRANSCRIPT}" ] || [ ! -f "${TRANSCRIPT}" ]; then
  exit 0  # No transcript found, skip
fi

# Parse transcript and extract telemetry data
# This is a simplified version - full parser would be in Python
python3 << 'PYTHON_EOF'
import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path

SENSEI_DIR = os.path.expanduser("~/.claude/sensei")
TRANSCRIPT = sys.argv[1] if len(sys.argv) > 1 else None

if not TRANSCRIPT or not os.path.exists(TRANSCRIPT):
    sys.exit(0)

# Parse .jsonl transcript
prompts = []
current_prompt = None
file_reads = {}
tool_calls = {}

try:
    with open(TRANSCRIPT, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Extract user prompts
            if record.get('type') == 'user' and 'message' in record:
                msg = record['message']
                if isinstance(msg, dict) and msg.get('content'):
                    content = msg['content']
                    if isinstance(content, str):
                        current_prompt = {
                            'timestamp': record.get('timestamp', datetime.now().isoformat()),
                            'text': content[:200],  # First 200 chars
                            'text_length': len(content),
                            'category': 'unknown'
                        }
                        prompts.append(current_prompt)

            # Extract tool uses (Bash, Read, etc)
            if record.get('type') == 'tool-use':
                tool_name = record.get('toolName', 'unknown')
                tool_calls[tool_name] = tool_calls.get(tool_name, 0) + 1

            # Extract file reads from tool results
            if record.get('type') == 'tool-result':
                if 'file_path' in record:
                    path = record['file_path']
                    file_reads[path] = file_reads.get(path, 0) + 1

            # Extract response tokens
            if record.get('type') == 'assistant' and 'message' in record:
                msg = record['message']
                if isinstance(msg, dict) and 'usage' in msg:
                    usage = msg['usage']
                    if current_prompt:
                        current_prompt['response_tokens'] = {
                            'input': usage.get('input_tokens', 0),
                            'output': usage.get('output_tokens', 0),
                            'cache_read': usage.get('cache_read_input_tokens', 0),
                            'cache_write': usage.get('cache_creation_input_tokens', 0)
                        }

except Exception as e:
    # Silently fail if parsing errors
    sys.exit(0)

# Write telemetry record
if prompts:
    telemetry_file = os.path.join(SENSEI_DIR, 'telemetry.jsonl')

    # Categorize prompts (simple heuristic)
    for p in prompts:
        text = p['text'].lower()
        if any(x in text for x in ['fix', 'bug', 'error', 'broken']):
            p['category'] = 'debug'
        elif any(x in text for x in ['review', 'check', 'audit', 'look']):
            p['category'] = 'review'
        elif any(x in text for x in ['test', 'spec', 'cover']):
            p['category'] = 'testing'
        elif any(x in text for x in ['refactor', 'improve', 'clean', 'simplify']):
            p['category'] = 'refactor'
        elif any(x in text for x in ['explain', 'what', 'how', 'why', 'understand']):
            p['category'] = 'explain'
        elif any(x in text for x in ['read', 'find', 'search', 'grep', 'look for']):
            p['category'] = 'search'
        elif any(x in text for x in ['create', 'write', 'add', 'new', 'build']):
            p['category'] = 'create'
        elif any(x in text for x in ['git', 'commit', 'push', 'pull']):
            p['category'] = 'vcs'

    # Write each prompt as telemetry
    with open(telemetry_file, 'a') as f:
        for p in prompts:
            telemetry = {
                'timestamp': p['timestamp'],
                'prompt': {
                    'text': p['text'],
                    'text_length': p['text_length'],
                    'category': p['category']
                },
                'response': p.get('response_tokens', {}),
                'tools_used': [
                    {'name': tool, 'count': count}
                    for tool, count in tool_calls.items()
                ] if tool_calls else [],
                'files_accessed': [
                    {'path': path, 'reads': count}
                    for path, count in file_reads.items()
                ] if file_reads else []
            }
            f.write(json.dumps(telemetry) + '\n')

sys.exit(0)

PYTHON_EOF
