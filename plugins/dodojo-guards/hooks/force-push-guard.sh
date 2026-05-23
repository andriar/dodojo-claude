#!/usr/bin/env bash
# PreToolUse Bash guard: block force-push to main/master/develop.
set -u

input=$(cat)

if command -v jq >/dev/null 2>&1; then
  cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
else
  cmd=$input
fi

# Match: git push ... (--force|--force-with-lease|-f) ... (main|master|develop)
# Covers: `git push -f origin main`, `git push origin +main`, `git push --force origin master`
if printf '%s' "$cmd" | grep -Eq 'git[[:space:]]+push([[:space:]]+[^[:space:]]+)*[[:space:]]+(--force(-with-lease)?|-f|[^[:space:]]+[[:space:]]+\+)[^|;]*\b(main|master|develop)\b'; then
  cat >&2 <<EOF
[force-push-guard] Blocked: force-push to main/master/develop detected.

Command: $cmd

Force-pushing a shared branch rewrites history for everyone.
If this is truly needed (rare), run the git command yourself outside Claude.
For hotfixes, use a normal push with a new commit instead.
EOF
  exit 2
fi

exit 0
