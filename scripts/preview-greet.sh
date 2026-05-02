#!/usr/bin/env bash
# Render the greeter banner straight to terminal — no Claude Code restart needed.
# Use during dev iteration: edit hooks/dodojo-greet.py → run this → see result.
#
# Usage:
#   scripts/preview-greet.sh                  # default theme
#   DODOJO_THEME=sakura scripts/preview-greet.sh
#   DODOJO_ICONS=emoji scripts/preview-greet.sh
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export KAGAMI_COLOR=1
exec python3 "$REPO/hooks/dodojo-greet.py"
