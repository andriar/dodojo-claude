#!/usr/bin/env bash
# PreToolUse guard: block tool calls containing likely secrets.
# Reads tool call JSON from stdin. Exit 2 = block + feed stderr back to model.
set -u

input=$(cat)

# Extract relevant fields without requiring jq — fall back to grep if jq absent.
if command -v jq >/dev/null 2>&1; then
  tool=$(printf '%s' "$input" | jq -r '.tool_name // empty')
  payload=$(printf '%s' "$input" | jq -r '
    (.tool_input.command // "") + "\n" +
    (.tool_input.content // "") + "\n" +
    (.tool_input.new_string // "") + "\n" +
    (.tool_input.file_path // "")
  ')
else
  tool=$(printf '%s' "$input" | grep -oE '"tool_name"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
  payload=$input
fi

# Secret signatures. Extend as needed.
patterns=(
  'AKIA[0-9A-Z]{16}'                          # AWS access key
  'ASIA[0-9A-Z]{16}'                          # AWS temp key
  'aws_secret_access_key[[:space:]]*=[[:space:]]*[A-Za-z0-9/+=]{40}'
  'ghp_[A-Za-z0-9]{36}'                       # GitHub PAT classic
  'github_pat_[A-Za-z0-9_]{82}'               # GitHub fine-grained
  'gho_[A-Za-z0-9]{36}'                       # GitHub OAuth
  'xox[baprs]-[A-Za-z0-9-]{10,}'              # Slack
  'sk-[A-Za-z0-9]{20,}'                       # OpenAI / Anthropic-style
  'sk-ant-[A-Za-z0-9_-]{20,}'                 # Anthropic
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'        # PEM keys
  'AIza[0-9A-Za-z_-]{35}'                     # Google API
  'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}'  # JWT with real payload
)

hit=""
for p in "${patterns[@]}"; do
  if printf '%s' "$payload" | grep -Eq -- "$p"; then
    hit="$p"
    break
  fi
done

# Heuristic: .env line with real-looking value (>=16 chars, not placeholder).
if [ -z "$hit" ]; then
  if printf '%s' "$payload" | grep -Eq '^[A-Z][A-Z0-9_]{3,}=[A-Za-z0-9/+=_.-]{16,}' \
     && ! printf '%s' "$payload" | grep -Eq '=(\$\{|<|your-|example|changeme|REDACTED|xxx)'; then
    hit=".env line with real-looking secret value"
  fi
fi

if [ -n "$hit" ]; then
  cat >&2 <<EOF
[secret-guard] Blocked: tool=$tool matched pattern: $hit

Likely secret detected in the tool input. Refusing to run.
If this is a mock/example, replace the real value with a placeholder
(e.g. <REDACTED>, your-token-here) and retry. Never commit real secrets.
EOF
  exit 2
fi

exit 0
