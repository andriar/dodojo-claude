# DoDojo docs

Short topical fragments — one concern each.

| Topic | What it covers |
|-------|----------------|
| [positioning.md](positioning.md) | DoDojo vs caveman vs claude-mem — what each layer does |
| [sensei.md](sensei.md) | Sensei opt-in rationale, setup cascade, privacy modes |
| [audit.md](audit.md) | Memory audit + orphan detection |
| [health.md](health.md) | Hook health smoke-test |
| [icons.md](icons.md) | `KAGAMI_ICONS` modes (nerd / unicode / emoji) |
| [prune.md](prune.md) | Pruning rules + lifecycle |
| [status.md](status.md) | Greeter pulse stats explanation |
| [theme.md](theme.md) | Greeter themes + `KAGAMI_THEME` |

Project goal tracking → [ROADMAP.md](../ROADMAP.md).

## Hooks (registered in `hooks.json`)

| Hook | Event | Purpose |
|------|-------|---------|
| `dodojo-greet.sh` | SessionStart | Greeter banner + pulse stats |
| `sensei-greet.sh` | SessionStart | Sensei pending recs + drafts + stale acceptances |
| `inject-git-context.sh` | UserPromptSubmit | Append branch + dirty status |
| `smart-context.py` | UserPromptSubmit | Rank memory files vs prompt; inject top matches |
| `skill-suggest.py` | UserPromptSubmit | Hint relevant custom skills |
| `memory-trigger.py` | UserPromptSubmit | Detect save/remember phrases; nudge auto-reflect |
| `model-route.py` | UserPromptSubmit | Classify prompt → suggest model + effort (haiku/sonnet/opus). Rules at `routing/` (plugin) + `~/.claude/memory/routing/` (user override) |
| `secret-guard.sh` | PreToolUse | Block secrets in tool args |
| `force-push-guard.sh` | PreToolUse | Block force-push to main/master/develop |
| `cost-guard.py` | PreToolUse | Block runaway ops (`find /`, `rm -rf /`, etc.) |
| `session-summary.py` | Stop | Per-turn telemetry to `~/.claude/sessions/YYYY-MM-DD.jsonl` |

## Commands (slash commands)

| Command | Purpose |
|---------|---------|
| `/dodojo:audit` | Memory + skill audit report |
| `/dodojo:companions` | Audit companion plugins (caveman, claude-mem, pokemon-buddy) |
| `/dodojo:health` | Hook smoke-test |
| `/dodojo:icons` | Switch icon mode |
| `/dodojo:init` | Interactive setup wizard |
| `/dodojo:prune` | Archive orphan memories |
| `/dodojo:sensei` | Run pattern miner + ROI advisor |
| `/dodojo:status` | Show DoDojo status card |
| `/dodojo:theme` | Switch greeter theme |

## Skills (bundled)

`archive-orphans`, `audit-context`, `companions`, `hook-health`, `memory-curator`, `new-skill`, `pr-describe`, `recall`, `repro-this`, `route-tune`, `sensei` — see each `SKILL.md` for trigger phrases.

## Releasing

```bash
# 1. Add notes under [Unreleased] in CHANGELOG.md
# 2. Bump (auto-promotes Unreleased → new version)
scripts/bump.sh 0.2.4
git push && git push --tags
```

Updates `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` + `CHANGELOG.md` together so versions and notes don't drift.

## Tests

```bash
uv venv .venv && uv pip install --python .venv pytest
.venv/bin/python -m pytest tests/ -q
```

CI: `.github/workflows/ci.yml` runs pytest + py_compile on Python 3.10/3.12, shellcheck on every `.sh` (hooks/scripts/skills), version-sync between plugin.json and marketplace.json, and JSON schema validity for all manifests.
