#!/usr/bin/env bash
# Standalone DoDojo theme picker — runs in terminal, zero Claude tokens.
# Usage: theme-picker.sh [theme-name]   (no arg = interactive)
set -euo pipefail

THEME_FILE="${HOME}/.claude/.kagami-theme"
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PREVIEWS="${SCRIPT_DIR}/../assets/theme-previews.json"

[[ -f "$PREVIEWS" ]] || { echo "previews not found: $PREVIEWS" >&2; exit 1; }
command -v jq >/dev/null || { echo "jq required" >&2; exit 1; }

CURRENT="$(cat "$THEME_FILE" 2>/dev/null || echo "default")"
THEMES=($(jq -r 'keys[]' "$PREVIEWS"))

apply() {
  local name="$1"
  if ! printf '%s\n' "${THEMES[@]}" | grep -qx "$name"; then
    echo "unknown theme: $name" >&2
    echo "available: ${THEMES[*]}" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$THEME_FILE")"
  printf '%s' "$name" > "$THEME_FILE"
  echo "theme → $name (applies next session)"
}

# Direct apply if arg passed
if [[ $# -ge 1 ]]; then
  apply "$1"
  exit 0
fi

# fzf path — best UX, live preview pane
if command -v fzf >/dev/null; then
  pick="$(printf '%s\n' "${THEMES[@]}" | fzf \
    --height=80% --reverse --border \
    --prompt="theme (current: $CURRENT) > " \
    --preview "jq -r --arg k {} '.[\$k]' '$PREVIEWS'" \
    --preview-window=right:50%:wrap)"
  [[ -n "$pick" ]] && apply "$pick"
  exit 0
fi

# Fallback: numbered menu with inline preview on demand
echo "Current theme: $CURRENT"
echo "Themes (type number to preview, 'a NAME' to apply, q to quit):"
i=1
for t in "${THEMES[@]}"; do
  marker=" "
  [[ "$t" == "$CURRENT" ]] && marker="*"
  printf "  %s %2d) %s\n" "$marker" "$i" "$t"
  ((i++))
done

while true; do
  read -rp "> " input
  case "$input" in
    q|quit|exit) exit 0 ;;
    a\ *) apply "${input#a }"; exit 0 ;;
    ''|*[!0-9]*) echo "type number, 'a NAME', or q" ;;
    *)
      idx=$((input - 1))
      if [[ $idx -lt 0 || $idx -ge ${#THEMES[@]} ]]; then
        echo "out of range"
        continue
      fi
      name="${THEMES[$idx]}"
      echo "─── $name ───"
      jq -r --arg k "$name" '.[$k]' "$PREVIEWS"
      echo "───────────────"
      read -rp "apply $name? [y/N] " yn
      [[ "$yn" =~ ^[Yy]$ ]] && { apply "$name"; exit 0; }
      ;;
  esac
done
