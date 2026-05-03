# Icons — `KAGAMI_ICONS` modes

Greeter section markers (memory / sensei / route / buddy / pulse / alerts) use one of three glyph sets. Set via `KAGAMI_ICONS` env var or `/dodojo:icons <mode>`.

## Modes

| Mode | Source | Looks like | Best for |
|------|--------|-----------|----------|
| `nerd` | Nerd Font glyphs | 󰈤 󰀦  | Patched terminal font (recommended) |
| `unicode` | Box-drawing fallback | ◆ ▲ ● ★ | Any modern terminal, no font install |
| `emoji` | Full-width emoji | 🌸 ⚡ 🔥 ✨ | Wide terminals, no Nerd Font |

## Auto-detect

If `KAGAMI_ICONS` unset, greeter checks:

1. `NERD_FONT=1` env → `nerd`
2. `fc-list` reports a Nerd Font installed → `nerd`
3. Otherwise → `unicode` (safest fallback)

Override anytime with `/dodojo:icons emoji` (or any mode).

## Switch

```bash
# In Claude Code
/dodojo:icons nerd

# Or persisted manually
echo 'nerd' > ~/.claude/.dodojo-icons

# Or via init wizard
/dodojo:init
```

Restart Claude Code to apply (SessionStart hook re-renders only on fresh process).

## Install Nerd Font

Recommended for `nerd` mode:

- macOS: `brew install --cask font-fira-code-nerd-font`
- Linux: `paru -S nerd-fonts-complete` / download from [nerdfonts.com](https://nerdfonts.com)
- WSL: install on Windows side, terminal will inherit

Verify: `fc-list | grep -i nerd` should list at least one font.

## Why three modes

- **Nerd**: prettiest, but breaks if font missing → tofu boxes (□)
- **Unicode**: always works, monochrome, ASCII-art adjacent
- **Emoji**: colorful but takes 2 columns each; misaligns narrow terminals

Pair with [theme.md](theme.md) — themes can recommend an icon mode (e.g. `madoka` looks best in `emoji`).

## Related

- [theme.md](theme.md) — color palette + chrome (orthogonal to icons)
- [status.md](status.md) — see how icons render in the live greeter banner
