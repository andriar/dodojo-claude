#!/usr/bin/env bash
# dj-install — symlink the dj CLI to ~/.local/bin/dj
# Idempotent. Safe to re-run.
set -eu

GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; DIM='\033[2m'; RESET='\033[0m'

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"

# If invoked outside Claude Code (e.g., direct shell run), detect latest version
if [[ -z "$PLUGIN_ROOT" ]]; then
  PLUGIN_ROOT=$(ls -td "$HOME"/.claude/plugins/cache/dodojo/dodojo/*/ 2>/dev/null | head -1)
  if [[ -z "$PLUGIN_ROOT" ]]; then
    echo -e "${RED}✗ Cannot find installed dodojo plugin.${RESET}"
    echo "  Install via: /plugin install dodojo"
    exit 1
  fi
  PLUGIN_ROOT="${PLUGIN_ROOT%/}"
fi

DJ_SRC="$PLUGIN_ROOT/bin/dj"
DJ_DST="$HOME/.local/bin/dj"

if [[ ! -x "$DJ_SRC" ]]; then
  echo -e "${RED}✗ Source not found or not executable: $DJ_SRC${RESET}"
  exit 1
fi

mkdir -p "$HOME/.local/bin"

if [[ -L "$DJ_DST" ]]; then
  cur=$(readlink "$DJ_DST")
  if [[ "$cur" == "$DJ_SRC" ]]; then
    echo -e "${DIM}symlink already correct: $DJ_DST -> $DJ_SRC${RESET}"
  else
    ln -sf "$DJ_SRC" "$DJ_DST"
    echo -e "${GREEN}✓ updated symlink: $DJ_DST -> $DJ_SRC${RESET}"
  fi
elif [[ -e "$DJ_DST" ]]; then
  echo -e "${RED}✗ $DJ_DST exists and is not a symlink. Refusing to overwrite.${RESET}"
  echo "  Move or delete it, then re-run."
  exit 1
else
  ln -s "$DJ_SRC" "$DJ_DST"
  echo -e "${GREEN}✓ symlinked $DJ_DST -> $DJ_SRC${RESET}"
fi

# PATH check
if command -v dj >/dev/null 2>&1; then
  echo -e "${GREEN}✓ dj is on PATH:${RESET} $(command -v dj)"
else
  echo -e "${YELLOW}⚠ ~/.local/bin is not on your PATH${RESET}"
  echo "  Add to your shell rc:"
  echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# Populate initial state
echo ""
echo -e "${DIM}running initial dj audit...${RESET}"
python3 "$PLUGIN_ROOT/bin/audit-stack.py"
echo ""
echo -e "${GREEN}Setup complete.${RESET} Try: ${DIM}dj help${RESET}"
