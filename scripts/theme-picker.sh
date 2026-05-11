#!/usr/bin/env bash
# Standalone DoDojo theme picker — runs in terminal, zero Claude tokens.
#
# Usage:
#   theme-picker.sh                 interactive picker
#   theme-picker.sh <theme-name>    apply directly
#   theme-picker.sh --list          print theme names (newline-delimited)
#   theme-picker.sh --help          show this help
#
# Deps: bash 3+, AND (jq OR python3). Optional: fzf (live preview pane).
# Platforms: Linux, macOS, WSL. Native Windows not supported.
set -euo pipefail

THEME_FILE="${HOME}/.claude/.kagami-theme"

# --- Portable realpath (GNU readlink -f and BSD readlink differ) ---
_realpath() {
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"
  elif command -v perl >/dev/null 2>&1; then
    perl -MCwd -e 'print Cwd::abs_path($ARGV[0])' "$1"
  else
    local target="$1"
    [[ -L "$target" ]] && target="$(readlink "$target")"
    local d
    d="$(cd "$(dirname "$target")" && pwd)"
    echo "$d/$(basename "$target")"
  fi
}

SCRIPT_PATH="$(_realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"
PREVIEWS="${SCRIPT_DIR}/../assets/theme-previews.json"

[[ -f "$PREVIEWS" ]] || { echo "previews not found: $PREVIEWS" >&2; exit 1; }

# --- JSON helpers (prefer jq, fall back to python3) ---
HAVE_JQ=0
HAVE_PY=0
command -v jq >/dev/null 2>&1 && HAVE_JQ=1
command -v python3 >/dev/null 2>&1 && HAVE_PY=1

if (( ! HAVE_JQ && ! HAVE_PY )); then
  cat >&2 <<EOF
Need either jq or python3. Install one:
  linux:  sudo apt install jq    (or python3)
  macos:  brew install jq        (python3 ships with macOS)
  wsl:    sudo apt install jq
EOF
  exit 1
fi

_json_keys() {
  if (( HAVE_JQ )); then
    jq -r 'keys[]' "$PREVIEWS"
  else
    python3 -c 'import json, sys; print("\n".join(sorted(json.load(open(sys.argv[1])).keys())))' "$PREVIEWS"
  fi
}

_json_get() {
  local key="$1"
  if (( HAVE_JQ )); then
    jq -r --arg k "$key" '.[$k] // empty' "$PREVIEWS"
  else
    python3 -c 'import json, sys; d=json.load(open(sys.argv[1])); print(d.get(sys.argv[2], ""))' "$PREVIEWS" "$key"
  fi
}

# --- Args ---
case "${1:-}" in
  -h|--help)
    sed -n '2,11p' "$SCRIPT_PATH" | sed 's/^# \{0,1\}//'
    exit 0
    ;;
  --list)
    _json_keys
    exit 0
    ;;
esac

CURRENT="$(cat "$THEME_FILE" 2>/dev/null || echo "default")"
THEMES=($(_json_keys))

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

if [[ $# -ge 1 ]]; then
  apply "$1"
  exit 0
fi

# --- fzf: live preview pane ---
if command -v fzf >/dev/null 2>&1; then
  if (( HAVE_JQ )); then
    PREVIEW_CMD="jq -r --arg k {} '.[\$k]' '$PREVIEWS'"
  else
    PREVIEW_CMD="python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2],\"\"))' '$PREVIEWS' {}"
  fi
  pick="$(printf '%s\n' "${THEMES[@]}" | fzf \
    --ansi --height=80% --reverse --border \
    --prompt="theme (current: $CURRENT) > " \
    --preview "$PREVIEW_CMD" \
    --preview-window=right:55%:wrap)"
  [[ -n "$pick" ]] && apply "$pick"
  exit 0
fi

# --- Fallback: numbered menu ---
echo "Current theme: $CURRENT"
echo "(tip: install fzf for live preview — apt/brew/choco install fzf)"
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
      _json_get "$name"
      echo "───────────────"
      read -rp "apply $name? [y/N] " yn
      [[ "$yn" =~ ^[Yy]$ ]] && { apply "$name"; exit 0; }
      ;;
  esac
done
