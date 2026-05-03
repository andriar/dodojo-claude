# Themes

Greeter banner color palette + chrome (bullets, dividers, signature). Set via `KAGAMI_THEME` env var or `/dodojo:theme <name>`.

## Switch theme

```bash
# In Claude Code
/dodojo:theme gruvbox

# Or set env directly
echo 'KAGAMI_THEME=frieren' >> ~/.claude/settings.json    # via /dodojo:init
```

Restart Claude Code to apply (SessionStart hook re-renders only on fresh process).

## Available themes (20)

| Theme | Vibe | Tagline | Signature |
|-------|------|---------|-----------|
| `default` | Neutral baseline | (none) | — |
| `mono` | Minimal monochrome | `minimal` | — |
| `pastel` | Soft signals | `soft signals` | — |
| `neon` | Cyber | `cyber pulse` | ◢◤ |
| `retro` | Phosphor terminal | `phosphor terminal` | `[ok]` |
| `dracula` | After-dark dev classic | `after dark` | — |
| `gruvbox` | Warm earth tones | `warm signals` | — |
| `catppuccin` | Soothing pastel (mocha) | `soothing pastel` | — |
| `nord` | Arctic minimal | `arctic minimal` | — |
| `monokai` | Sublime classic | `sublime classic` | — |
| `sakura` | 🌸 Cherry blossom | `petals on the wind` | 🌸 |
| `kawaii` | 🍡 Pastel rainbow | `ganbatte yo` | (⌒‿⌒) |
| `shounen` | 🔥 Battle anime | `never give up` | 🔥 |
| `ghibli` | 🌳 Studio Ghibli | `tonari no kagami` | 🌳 |
| `mecha` | 🤖 Gundam metallic | `system online` | `[ARM-OK]` |
| `evangelion` | 🩸 NGE purple/green | `AT-field engaged` | NERV |
| `jjk` | 🟣 Jujutsu Kaisen | `domain expansion` | 領域展開 |
| `aot` | ⚔ Attack on Titan | `shinzou wo sasageyo` | 🪽 |
| `frieren` | ❄ Frost mage | `1000 years of magic` | ✨ |
| `madoka` | ✦ Magical girl | `make a contract` | 💫 |

## What changes per theme

- ANSI color palette (bullets, headers, accent)
- Bullet glyph (`▸` / `❀` / `▶` / `►` / `⚔` / `❄` / etc.)
- Section divider character (`─` / `═` / `·` / `❀` / `❄`)
- Tagline shown under banner
- Signature glyph at footer

What does NOT change: layout, section order, content, or token cost. Pure cosmetic.

## Pair with icon mode

`KAGAMI_ICONS` controls section markers (memory/sensei/route/buddy):

| Mode | Glyph source | Best for |
|------|-------------|----------|
| `nerd` | Nerd Font glyphs | Patched terminal font |
| `unicode` | Box-drawing fallback | Any modern terminal |
| `emoji` | Full-width emoji | Wide terminals, no Nerd Font |

See [icons.md](icons.md).

## Color toggle

`KAGAMI_COLOR=0` disables all ANSI codes (greeter renders as plain text). Useful for narrow terminals or terminals without true-color. Code, diffs, and Claude Code's own UI ignore this — it only affects the greeter banner.

## Preview without restart

```bash
bash scripts/preview-greet.sh
```

Renders current greeter to stdout immediately. Useful when iterating themes.

## Adding a custom theme

Themes are defined inline in `hooks/dodojo-greet.py` — search for the palette dict (~line where `pastel`, `neon`, `retro` are declared). Add a new entry with: ANSI codes, bullet, tagline, divider, signature. PRs welcome.

## Related

- [icons.md](icons.md) — icon set (orthogonal — themes set color, icons set glyphs)
- [status.md](status.md) — see how the chosen theme renders the full greeter
