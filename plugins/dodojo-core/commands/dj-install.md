---
description: Bootstrap the dj CLI — symlinks bin/dj to ~/.local/bin/dj for shell access
---

# /dodojo:dj-install

Bootstrap the `dj` CLI on your PATH. Runs `${CLAUDE_PLUGIN_ROOT}/scripts/dj-install.sh`.

What it does:
1. Detects the latest installed dodojo version
2. Symlinks `bin/dj` to `~/.local/bin/dj`
3. Verifies `~/.local/bin` is on your shell PATH (warns if not)
4. Runs `dj audit` once to populate state

After this, you can type `dj audit`, `dj prune`, `dj report` directly in your terminal — no need to call the slash command again.
