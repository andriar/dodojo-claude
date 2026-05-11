---
description: Switch DoDojo greeter theme. Usage — /dodojo:theme <name>
---

# /dodojo:theme

Switch the greeter theme. Persists to `~/.claude/.kagami-theme`.

## Usage

```
/dodojo:theme [name]
```

- With name → validate + apply directly.
- Without name → interactive picker via `AskUserQuestion` (drill-down by group).

## Themes

Color-Classic: `default · pastel · neon · retro · mono`
Color-Dark-Editor: `dracula · gruvbox · tokyo-night · catppuccin · nord · rose-pine · solarized-dark · monokai · one-dark · github-dark`
Anime-Vibe: `ghibli · sakura · kawaii · frieren · madoka`
Anime-Shounen: `demon-slayer · jjk · chainsaw-man · evangelion · aot · one-piece · shounen · mecha`

## Behavior

**Name passed**: validate against THEMES dict. Valid → write `~/.claude/.kagami-theme` + confirm. Invalid → list themes + exit.

**No name (interactive picker)**:
1. Read current theme from `~/.claude/.kagami-theme` (show in prompt).
2. Load preview map from plugin asset `assets/theme-previews.json` (key = theme name, value = ASCII snippet showing bullet/tagline/divider/sig).
3. Call `AskUserQuestion` step 1 — pick group (4 options: Color-Classic, Color-Dark-Editor, Anime-Vibe, Anime-Shounen). No previews on group step.
4. Call `AskUserQuestion` step 2 — pick theme within group. **Pass `previews[name]` as the `preview` field on each option** (side-by-side layout auto-activates). Group has >4 themes → split into multiple questions (≤4 options each), each option still carries its preview.
5. Write selection to `~/.claude/.kagami-theme` + confirm.

If `assets/theme-previews.json` missing (older install), fall back to picker without previews. Regenerate via `scripts/gen-theme-previews.py` after editing `DECORATIONS` in `hooks/dodojo-greet.py`.

Theme applies on next session greeter render — current session keeps the old banner.
