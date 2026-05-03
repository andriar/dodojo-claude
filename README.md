# DoDojo

Quiet tools for AI-assisted dev. Memory, pattern coach, smart context, and audit — keeps your Claude Code workflow lean.

> Built for indie hackers tired of watching their tokens drain on Claude Code Max.

## What it does

| Layer | Role | What it does |
|-------|------|--------------|
| **Mirror** (Kagami) | memory | Captures preferences, lessons, decisions across sessions — no more re-explaining |
| **Coach** (Sensei) | pattern coach | Mines work patterns → ranks by ROI → recommends automations weekly *(opt-in, requires env setup — see below)* |
| **Context** | smart retrieval | Injects only the memories relevant to your current prompt |
| **Audit** | prune | Archives unused memories/skills so your stack stays lean |
| **Route** | model picker | Classifies each prompt → suggests model + effort (haiku/sonnet/opus). Override rules at `~/.claude/memory/routing/` |
| **Meter** | observability | Token-saved counter on every session start |

## Why it exists

Your Claude Code config bloats over time. CLAUDE.md grows. Memory accumulates. Tokens drain. DoDojo provides discipline so your workflow stays sharp 6 months from now.

## Install

```bash
# In Claude Code:
/plugin marketplace add andriar/dodojo-claude
/plugin install dodojo@dodojo
```

Or local development:
```bash
/plugin marketplace add /path/to/dodojo-claude
/plugin install dodojo
```

## Configure

Run the setup wizard once after install:

```bash
# In Claude Code:
/dodojo:init

# Or headless / CI:
bash ~/.claude/plugins/cache/dodojo/dodojo/<version>/scripts/dodojo-init.sh
```

Both prompt for theme, icons, color, silent mode, and Coach (Sensei) paths — then write to `~/.claude/settings.json` `env` block. Same questions, same outcome.

Show current values: `bash .../dodojo-init.sh --print` · Reset: `--reset`.

Manual env vars (override or skip the wizard):

| Var | Default | Purpose |
|-----|---------|---------|
| `DODOJO_DATA` | `~/.claude` | Where to read/write memory, sessions, logs |
| `KAGAMI_THEME` | `default` | Greeter theme — see `kagami-theme.sh` for list |
| `KAGAMI_ICONS` | `nerd` | `nerd` / `unicode` / `emoji` |
| `KAGAMI_COLOR` | `0` | Set to `1` to enable ANSI colors in greeter |
| `KAGAMI_SILENT` | `0` | Set to `1` to skip injecting greeter into Claude's context (~400 tokens/session). Greeter still renders to terminal. |

## Coach (Sensei) — opt-in

Sensei mines work patterns from shell history + git log → ranks by ROI → writes weekly markdown report.

Easiest setup: `/dodojo:init` (or `scripts/dodojo-init.sh`) prompts for vault + repos + history paths. Manual override via `~/.claude/settings.json` `env` block (`SENSEI_VAULT`, `SENSEI_REPOS` colon-separated, `SENSEI_HISTORY`).

Defaults assume zsh + Obsidian at standard paths. State (weights, feedback, raw events) lives at `~/.claude/dodojo/sensei/` — user-local, never in plugin cache.

Trigger weekly report:
```bash
python3 ~/.claude/plugins/cache/dodojo/dodojo/<version>/skills/sensei/scripts/report.py
```

Or invoke `/sensei` in Claude. Optional cron via `crontab -e`:
```cron
0 9 * * 1  python3 ~/.claude/plugins/cache/dodojo/dodojo/0.3.8/skills/sensei/scripts/report.py
```

Optional integration with **claude-mem** plugin for session timeline mining (auto-skipped if absent).

## Companions (not bundled)

DoDojo focuses on memory + audit. Pair with these for a full optimization stack:

- **[claude-mem](https://github.com/thedotmack/claude-mem)** — auto-summarizes long sessions
- **RTK** — trims shell command output (Rust-based proxy)
- **[caveman](https://github.com/JuliusBrussee/caveman)** — compresses prompt/response style
- **pokemon-buddy** — gamified XP system (companion plugin)

## Docs

See [docs/README.md](docs/README.md) for hooks, commands, skills, release process.

## Develop

```bash
uv venv .venv && uv pip install --python .venv pytest
.venv/bin/python -m pytest tests/ -q
```

Release: `scripts/bump.sh <new-version>`.

## Status

Early development. Built for one developer's workflow first; sharing for those with similar pain.

No support guarantees. Fork it, adapt it, break it.

## License

MIT
