# DoDojo docs

Short topical fragments — one concern each.

| Topic | What it covers |
|-------|----------------|
| [audit.md](audit.md) | Memory audit + orphan detection |
| [health.md](health.md) | Hook health smoke-test |
| [icons.md](icons.md) | `KAGAMI_ICONS` modes (nerd / unicode / emoji) |
| [prune.md](prune.md) | Pruning rules + lifecycle |
| [status.md](status.md) | Greeter pulse stats explanation |
| [theme.md](theme.md) | Greeter themes + `KAGAMI_THEME` |

## Hooks (registered in `hooks.json`)

| Hook | Event | Purpose |
|------|-------|---------|
| `dodojo-greet.sh` | SessionStart | Greeter banner + pulse stats |
| `inject-git-context.sh` | UserPromptSubmit | Append branch + dirty status |
| `smart-context.py` | UserPromptSubmit | Rank memory files vs prompt; inject top matches |
| `skill-suggest.py` | UserPromptSubmit | Hint relevant custom skills |
| `memory-trigger.py` | UserPromptSubmit | Detect save/remember phrases; nudge auto-reflect |
| `secret-guard.sh` | PreToolUse | Block secrets in tool args |
| `force-push-guard.sh` | PreToolUse | Block force-push to main/master/develop |
| `cost-guard.py` | PreToolUse | Block runaway ops (`find /`, `rm -rf /`, etc.) |
| `session-summary.py` | Stop | Per-turn telemetry to `~/.claude/sessions/YYYY-MM-DD.jsonl` |

## Commands (slash commands)

| Command | Purpose |
|---------|---------|
| `/dodojo:audit` | Memory + skill audit report |
| `/dodojo:health` | Hook smoke-test |
| `/dodojo:icons` | Switch icon mode |
| `/dodojo:prune` | Archive orphan memories |
| `/dodojo:status` | Show DoDojo status card |
| `/dodojo:theme` | Switch greeter theme |

## Skills (bundled)

`archive-orphans`, `audit-context`, `hook-health`, `memory-curator`, `new-skill`, `pr-describe`, `recall`, `repro-this` — see each `SKILL.md` for trigger phrases.

## Releasing

```bash
scripts/bump.sh 0.2.4
git push && git push --tags
```

Updates `.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` together so versions don't drift.

## Tests

```bash
uv venv .venv && uv pip install --python .venv pytest
.venv/bin/python -m pytest tests/ -q
```

CI: `.github/workflows/ci.yml` runs pytest on Python 3.10/3.12 + shellcheck on every `.sh`.
