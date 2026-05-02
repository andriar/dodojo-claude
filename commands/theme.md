---
description: Switch DoDojo greeter theme. Usage — /dodojo:theme <name>
---

# /dodojo:theme

Switch the greeter theme. Persists to `~/.claude/.kagami-theme`.

## Usage

```
/dodojo:theme <name>
```

If no name passed, list available themes from `hooks/dodojo-greet.py` (THEMES dict) and current selection.

## Themes

Color: `default · pastel · neon · retro · mono · dracula · gruvbox · tokyo-night · catppuccin · nord · rose-pine · solarized-dark · monokai · one-dark · github-dark`

Anime / vibe: `ghibli · sakura · kawaii · frieren · madoka · demon-slayer · jjk · chainsaw-man · evangelion · aot · one-piece · shounen · mecha`

## Behavior

Validate name against THEMES dict. If valid → write to `~/.claude/.kagami-theme` and confirm. If invalid → list themes and exit.

Theme applies on next session greeter render — current session keeps the old banner.
