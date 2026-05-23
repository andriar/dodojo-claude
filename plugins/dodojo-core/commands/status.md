---
description: Show DoDojo status — theme, icons, data path, memory + hook counts
---

# /dodojo:status

Print current DoDojo configuration.

## Behavior

Output a table with:
- `theme` — current greeter theme (from `~/.claude/.kagami-theme` or `KAGAMI_THEME` env, default `default`)
- `icons` — current icon mode (from `~/.claude/.dodojo-icons` or `KAGAMI_ICONS` env, auto-detected if unset)
- `data path` — value of `DODOJO_DATA` env (default `~/.claude`)
- `memory files` — count of `.md` files under `~/.claude/memory/` (recursive, depth 2)
- `hooks (custom settings.json)` — sum of hook entries in `~/.claude/settings.json` (does not include plugin-provided hooks)
