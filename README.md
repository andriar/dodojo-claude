# DoDojo

Quiet tools for AI-assisted dev. Memory, pattern coach, smart context, and audit — keeps your Claude Code workflow lean.

> Built for indie hackers tired of watching their tokens drain on Claude Code Max.

## What it does

| Layer | Role | What it does |
|-------|------|--------------|
| **Mirror** (Kagami) | memory | Captures preferences, lessons, decisions across sessions — no more re-explaining |
| **Coach** (Sensei) | pattern coach | Surfaces habits worth automating |
| **Context** | smart retrieval | Injects only the memories relevant to your current prompt |
| **Audit** | prune | Archives unused memories/skills so your stack stays lean |
| **Meter** | observability | Token-saved counter on every session start |

## Why it exists

Your Claude Code config bloats over time. CLAUDE.md grows. Memory accumulates. Tokens drain. DoDojo provides discipline so your workflow stays sharp 6 months from now.

## Install

```bash
# In Claude Code:
/plugin marketplace add github.com/andriar/DoDojo-claude
/plugin install dodojo
```

Or local development:
```bash
/plugin marketplace add /path/to/DoDojo-claude
/plugin install dodojo
```

## Configure

Optional environment variables:

| Var | Default | Purpose |
|-----|---------|---------|
| `DODOJO_DATA` | `~/.claude` | Where to read/write memory, sessions, logs |
| `KAGAMI_THEME` | `default` | Greeter theme — see `kagami-theme.sh` for list |
| `KAGAMI_ICONS` | `nerd` | `nerd` / `unicode` / `emoji` |
| `KAGAMI_COLOR` | `0` | Set to `1` to enable ANSI colors in greeter |

## Companions (not bundled)

DoDojo focuses on memory + audit. Pair with these for a full optimization stack:

- **[claude-mem](https://github.com/thedotmack/claude-mem)** — auto-summarizes long sessions
- **[RTK](https://github.com/.../rtk)** — trims shell command output
- **[caveman](https://github.com/JuliusBrussee/caveman)** — compresses prompt/response style
- **pokemon-buddy** — gamified XP system (companion plugin)

## Status

Early development. Built for one developer's workflow first; sharing for those with similar pain.

No support guarantees. Fork it, adapt it, break it.

## License

MIT
