#!/usr/bin/env bash
# UserPromptSubmit hook: inject current git branch + dirty status.
# Output to stdout is appended to the user prompt as additional context.
set -u

# Only act inside a git working tree.
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  exit 0
fi

branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
ahead_behind=$(git rev-list --left-right --count "@{u}...HEAD" 2>/dev/null)
if [ -n "$ahead_behind" ]; then
  behind=$(printf '%s' "$ahead_behind" | awk '{print $1}')
  ahead=$(printf '%s' "$ahead_behind" | awk '{print $2}')
  tracking=" | ↑$ahead ↓$behind vs upstream"
else
  tracking=" | no upstream"
fi

printf '[git] branch=%s | dirty=%s file(s)%s\n' "$branch" "$dirty" "$tracking"
