#!/usr/bin/env bash
# Cache GC — keep N most recent dodojo versions in plugin cache, prune older.
#
# Usage:
#   scripts/cache-gc.sh           # dry-run, list candidates
#   scripts/cache-gc.sh --apply   # actually delete
#   KEEP=3 scripts/cache-gc.sh    # keep 3 latest instead of default 2
#
# Safe by default (dry-run). Keeps N newest by semver, so the currently-
# installed version is preserved as long as it's among the latest. Downgrade
# users: bump KEEP or run with care.

set -euo pipefail

KEEP="${KEEP:-2}"
APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

CACHE_DIR="${HOME}/.claude/plugins/cache/dodojo/dodojo"

if [[ ! -d "$CACHE_DIR" ]]; then
  echo "no cache dir at $CACHE_DIR"
  exit 0
fi

# Sort versions semantically (sort -V), oldest first
mapfile -t versions < <(find "$CACHE_DIR" -maxdepth 1 -mindepth 1 -type d -printf '%f\n' | sort -V)
total=${#versions[@]}

if (( total <= KEEP )); then
  echo "have $total version(s); keep=$KEEP → nothing to prune"
  exit 0
fi

prune_count=$((total - KEEP))
prune=("${versions[@]:0:prune_count}")
keep=("${versions[@]:prune_count}")

echo "found $total versions, keeping $KEEP newest:"
for v in "${keep[@]}"; do printf "  keep  %s\n" "$v"; done
for v in "${prune[@]}"; do printf "  prune %s\n" "$v"; done

if (( APPLY == 0 )); then
  echo ""
  echo "dry-run — re-run with --apply to delete"
  exit 0
fi

freed_kb=0
for v in "${prune[@]}"; do
  path="$CACHE_DIR/$v"
  size=$(du -sk "$path" 2>/dev/null | awk '{print $1}')
  rm -rf "$path"
  freed_kb=$((freed_kb + size))
  printf "removed %s (%d KB)\n" "$v" "$size"
done

printf "freed %d MB total\n" "$((freed_kb / 1024))"
