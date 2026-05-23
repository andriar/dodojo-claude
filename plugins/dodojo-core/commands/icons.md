---
description: Switch DoDojo icon mode. Usage — /dodojo:icons <nerd|unicode|emoji>
---

# /dodojo:icons

Switch the greeter icon mode. Persists to `~/.claude/.dodojo-icons`.

## Usage

```
/dodojo:icons <nerd|unicode|emoji>
```

| mode | needs | best for |
|------|-------|----------|
| `nerd` | Nerd Font installed in terminal | rich glyphs (󰀦 󰈤 etc.) |
| `unicode` | any modern terminal | safe geometric symbols (◆ ▲ ●) |
| `emoji` | any modern terminal | colorful (🌸 ⚡ 🔥) |

Default auto-detects: uses `nerd` if `NERD_FONT=1` env or `fc-list` reports a Nerd Font; otherwise falls back to `unicode`.

## Behavior

Validate mode. Write to `~/.claude/.dodojo-icons`. Confirm. Applies on next session greeter render.
