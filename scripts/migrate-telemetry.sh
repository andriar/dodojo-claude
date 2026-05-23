#!/usr/bin/env bash
# Migrate historical telemetry from ~/.claude/{sessions,hooks/*.log} to
# ~/.claude/plugins/data/dodojo-dodojo/{sessions,hooks/*.log}.
#
# Safe: copies (not moves) by default, so the legacy location remains
# readable. Pass --move to move instead. Pass --dry-run to preview.
#
# After migration, dodojo's readers (greeter, heartbeat) merge both
# locations, so historical data continues to surface either way.
set -euo pipefail

LEGACY="${HOME}/.claude"
CANONICAL="${DODOJO_TELEMETRY_HOME:-${LEGACY}/plugins/data/dodojo-dodojo}"
MODE="copy"
DRY=0
for arg in "$@"; do
  case "$arg" in
    --move) MODE="move" ;;
    --dry-run) DRY=1 ;;
    -h|--help)
      echo "Usage: $0 [--move] [--dry-run]"
      echo "  legacy:    $LEGACY/{sessions,hooks/*.log}"
      echo "  canonical: $CANONICAL/{sessions,hooks/*.log}"
      exit 0
      ;;
  esac
done

echo "Migrating telemetry"
echo "  from: $LEGACY/{sessions,hooks/*.log}"
echo "  to:   $CANONICAL/{sessions,hooks/*.log}"
echo "  mode: $MODE  (dry-run=$DRY)"

migrate_dir() {
  local src="$1" dst="$2" pattern="$3"
  [[ -d "$src" ]] || { echo "  skip $src (not a dir)"; return; }
  local files=()
  while IFS= read -r -d '' f; do files+=("$f"); done < <(find "$src" -maxdepth 1 -name "$pattern" -type f -print0)
  if [[ ${#files[@]} -eq 0 ]]; then
    echo "  $src: no $pattern files"
    return
  fi
  mkdir -p "$dst"
  for f in "${files[@]}"; do
    local base; base=$(basename "$f")
    if [[ -e "$dst/$base" ]]; then
      echo "    skip $base (already at destination)"
      continue
    fi
    if [[ $DRY -eq 1 ]]; then
      echo "    would $MODE $f → $dst/"
    else
      if [[ "$MODE" == "move" ]]; then
        mv "$f" "$dst/"
      else
        cp "$f" "$dst/"
      fi
      echo "    $MODE $base"
    fi
  done
}

migrate_dir "$LEGACY/sessions" "$CANONICAL/sessions" "*.jsonl"
# Only known plugin hook logs — leaves user-level logs (e.g. cache-heal) alone.
for log in smart-context.log model-route.log skill-suggest.log; do
  migrate_dir "$LEGACY/hooks" "$CANONICAL/hooks" "$log"
done

echo "done"
