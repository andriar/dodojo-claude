#!/usr/bin/env bash
# Install or remove the DoDojo `claude()` shell wrapper that paints the greeter
# in the terminal BEFORE Claude Code launches (zero token cost vs. SessionStart
# hook injection).
#
# Usage:
#   dodojo-greeter-install.sh install   # detect $SHELL, append wrapper to rc
#   dodojo-greeter-install.sh uninstall # strip wrapper block from rc
#   dodojo-greeter-install.sh status    # report which rc has the block
#
# Idempotent: re-running install with the block already present is a no-op.
# Block is sentinel-fenced for safe automated removal.

set -euo pipefail

SENTINEL_BEGIN="# >>> DODOJO_GREETER_BEGIN >>>"
SENTINEL_END="# <<< DODOJO_GREETER_END <<<"

# Resolve absolute path to the greeter python script. Walk up from this file:
# scripts/dodojo-greeter-install.sh -> plugin root -> hooks/dodojo-greet.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GREETER_PY="$PLUGIN_ROOT/hooks/dodojo-greet.py"

detect_shell_rc() {
  local sh="${SHELL##*/}"
  case "$sh" in
    zsh)  echo "$HOME/.zshrc" ;;
    bash)
      # Prefer .bashrc on Linux, .bash_profile on macOS interactive logins.
      if [ "$(uname -s)" = "Darwin" ] && [ -f "$HOME/.bash_profile" ]; then
        echo "$HOME/.bash_profile"
      else
        echo "$HOME/.bashrc"
      fi
      ;;
    fish) echo "$HOME/.config/fish/config.fish" ;;
    *)    echo "" ;;  # unsupported (cmd, nu, xonsh, etc.)
  esac
}

shell_block_posix() {
  cat <<EOF
$SENTINEL_BEGIN
# Paint DoDojo greeter in terminal before Claude Code launches.
# Managed by dodojo-greeter-install.sh — edit between sentinels at your own risk.
claude() {
  if [ -t 1 ] && [ -x "\$(command -v python3)" ]; then
    KAGAMI_COLOR="\${KAGAMI_COLOR:-1}" python3 "$GREETER_PY" 2>/dev/null || true
  fi
  command claude "\$@"
}
$SENTINEL_END
EOF
}

shell_block_fish() {
  cat <<EOF
$SENTINEL_BEGIN
# Paint DoDojo greeter in terminal before Claude Code launches.
function claude
  if status is-interactive; and type -q python3
    KAGAMI_COLOR=(set -q KAGAMI_COLOR; and echo \$KAGAMI_COLOR; or echo 1) python3 "$GREETER_PY" 2>/dev/null
  end
  command claude \$argv
end
$SENTINEL_END
EOF
}

cmd="${1:-status}"
RC="$(detect_shell_rc)"

case "$cmd" in
  status)
    if [ -z "$RC" ]; then
      echo "shell=$SHELL  rc=(unsupported)"
      exit 0
    fi
    if [ -f "$RC" ] && grep -qF "$SENTINEL_BEGIN" "$RC"; then
      echo "shell=$SHELL  rc=$RC  installed=yes"
    else
      echo "shell=$SHELL  rc=$RC  installed=no"
    fi
    ;;
  install)
    if [ -z "$RC" ]; then
      echo "Unsupported shell: $SHELL" >&2
      echo "Manually add a wrapper that runs: python3 $GREETER_PY" >&2
      exit 1
    fi
    mkdir -p "$(dirname "$RC")"
    [ -f "$RC" ] || : > "$RC"
    if grep -qF "$SENTINEL_BEGIN" "$RC"; then
      echo "Already installed in $RC (no change)"
      exit 0
    fi
    if [[ "$RC" == *config/fish/config.fish ]]; then
      shell_block_fish >> "$RC"
    else
      shell_block_posix >> "$RC"
    fi
    echo "Installed wrapper in $RC"
    echo "Reload shell: source $RC  (or open a new terminal)"
    ;;
  uninstall)
    if [ -z "$RC" ] || [ ! -f "$RC" ]; then
      echo "Nothing to remove (rc=$RC)"
      exit 0
    fi
    if ! grep -qF "$SENTINEL_BEGIN" "$RC"; then
      echo "No DoDojo wrapper in $RC (no change)"
      exit 0
    fi
    # Strip block between sentinels (inclusive). awk-based for portability.
    tmp="$(mktemp)"
    awk -v b="$SENTINEL_BEGIN" -v e="$SENTINEL_END" '
      $0 == b {skip=1; next}
      $0 == e {skip=0; next}
      !skip {print}
    ' "$RC" > "$tmp"
    mv "$tmp" "$RC"
    echo "Removed wrapper from $RC"
    ;;
  *)
    echo "Usage: $0 {install|uninstall|status}" >&2
    exit 2
    ;;
esac
