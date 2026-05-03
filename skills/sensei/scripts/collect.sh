#!/usr/bin/env bash
# Sensei collector — scrape work signals over last N days.
# Usage: collect.sh [days=7] > /tmp/sensei-raw.json
# Excludes paths/lines matching state/exclusions.txt.

set -euo pipefail

DAYS="${1:-7}"
SENSEI_HOME="${SENSEI_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
SENSEI_STATE="${SENSEI_STATE:-$HOME/.claude/dodojo/sensei}"
SENSEI_HISTORY="${SENSEI_HISTORY:-$HOME/.zsh_history}"
SENSEI_REPOS="${SENSEI_REPOS:-$HOME/Development}"
EXCL="$SENSEI_STATE/exclusions.txt"
[ -f "$EXCL" ] || EXCL="$SENSEI_HOME/state/exclusions.txt"
OUT_DIR="$SENSEI_STATE"
mkdir -p "$OUT_DIR"

# Build exclusion grep pattern
build_excl_pattern() {
  [ -f "$EXCL" ] || { echo ""; return; }
  grep -v '^#' "$EXCL" | grep -v '^$' | paste -sd '|' -
}
EXCL_PATTERN="$(build_excl_pattern)"

filter_secrets() {
  if [ -z "$EXCL_PATTERN" ]; then cat; else grep -Eiv "$EXCL_PATTERN" || true; fi
}

# Cutoff timestamp (epoch seconds, N days ago)
CUTOFF=$(date -d "$DAYS days ago" +%s 2>/dev/null || date -v-"${DAYS}"d +%s)

# 1. zsh history — extended format ": <ts>:<dur>;<cmd>"
collect_zsh() {
  local hist="$SENSEI_HISTORY"
  [ -f "$hist" ] || { echo ""; return; }
  awk -F';' -v cutoff="$CUTOFF" '
    /^: [0-9]+:[0-9]+;/ {
      split($1, a, ":"); ts=a[2]+0
      if (ts >= cutoff) {
        cmd=$0; sub(/^: [0-9]+:[0-9]+;/, "", cmd)
        print ts "\t" cmd
      }
    }
  ' "$hist" 2>/dev/null | filter_secrets
}

# 2. claude-mem timeline (if installed) — pipe via mcp not available in shell; fallback to project memory dirs
collect_claude_mem() {
  local memdir="$HOME/.claude/projects"
  [ -d "$memdir" ] || return
  find "$memdir" -name "*.md" -newermt "$DAYS days ago" -type f 2>/dev/null | filter_secrets | while read -r f; do
    echo -e "$(stat -c %Y "$f")\tmem\t$f"
  done
}

# 3. git log across user's repos — scan ~/Development + ~/.claude
collect_git() {
  local roots
  IFS=':' read -ra roots <<< "$SENSEI_REPOS"
  for root in "${roots[@]}"; do
    [ -d "$root" ] || continue
    find "$root" -maxdepth 4 -name ".git" -type d 2>/dev/null | while read -r gitdir; do
      local repo
      repo="$(dirname "$gitdir")"
      git -C "$repo" log --since="$DAYS days ago" --pretty=format:"%at%x09%H%x09%s%x09%an" 2>/dev/null \
        | filter_secrets | awk -v r="$repo" -F'\t' '{print $1"\tgit\t"r"\t"$3}'
    done
  done
}

# 4. hook telemetry — smart-context + skill-suggest + session-summary
collect_hooks() {
  local sc="$HOME/.claude/hooks/smart-context.log"
  local ss="$HOME/.claude/hooks/skill-suggest.log"
  local sessions_dir="$HOME/.claude/sessions"
  local cutoff="$CUTOFF"

  python3 - "$sc" "$ss" "$sessions_dir" "$cutoff" <<'PY' 2>/dev/null
import json, sys
from pathlib import Path
sc, ss, sessions_dir, cutoff = sys.argv[1:5]
cutoff = int(cutoff)

if Path(sc).is_file():
    for line in Path(sc).read_text(errors="replace").splitlines():
        line = line.strip()
        if not line: continue
        try:
            r = json.loads(line)
            ts = r.get('ts', 0)
            if ts < cutoff: continue
            print(f"{ts}\thook\tsmart-context\tmatched={r.get('matched_count',0)}\tscore={r.get('top_score',0)}")
        except Exception: pass

if Path(ss).is_file():
    for line in Path(ss).read_text(errors="replace").splitlines():
        line = line.strip()
        if not line: continue
        try:
            r = json.loads(line)
            ts = r.get('ts', 0)
            if ts < cutoff: continue
            names = ",".join(h.get("name","?") for h in r.get("hints", []))
            print(f"{ts}\thook\tskill-suggest\thints={names or '-'}")
        except Exception: pass

sd = Path(sessions_dir)
if sd.is_dir():
    for f in sd.glob("*.jsonl"):
        try:
            for line in f.read_text(errors="replace").splitlines():
                line = line.strip()
                if not line: continue
                try:
                    r = json.loads(line)
                    ts = r.get('ts', 0)
                    if ts < cutoff: continue
                    print(f"{ts}\thook\tsession\ttools={r.get('tool_total',0)}\tfiles={r.get('files_touched_count',0)}")
                except Exception: pass
        except Exception: pass
PY
}

# Output as TSV: <ts> <source> <data...>
{
  collect_zsh    | awk -F'\t' '{print $1"\tzsh\t"$2}'
  collect_claude_mem
  collect_git
  collect_hooks
} | sort -n > "$OUT_DIR/raw.tsv"

echo "Collected $(wc -l < "$OUT_DIR/raw.tsv") events to $OUT_DIR/raw.tsv (last $DAYS days)" >&2
