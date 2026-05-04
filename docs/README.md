# DoDojo Documentation

Complete guides + reference. Pick your entry point below.

---

## 🚀 Start Here

**New to DoDojo?** Pick one:

| If you want to... | Read |
|---|---|
| Understand the philosophy | [mental-model.md](guides/mental-model.md) — Why DoDojo exists, 4 core ideas (Mirror/Coach/Context/Audit) |
| Install + get ROI in 5 min | [quickstart.md](quickstart.md) — Setup wizard + first memory |
| See it in action | [demo.md](demo.md) — 60-second asciinema (greeter → Sensei mining) |
| Know what each feature does | [FEATURES.md](FEATURES.md) — Complete reference (memory, Sensei, tips, orphan detection, smart context, categorized memory, auto-archival) |

---

## 📚 Feature Guides

| Feature | When to use | Details |
|---------|---|---|
| **Mirror (Memory)** | Capture lessons that stick across sessions | [FEATURES.md: Mirror](FEATURES.md#mirror-memory) — how-to, metadata, when to create |
| **Sensei Phase 2** | Detect friction patterns in your workflow | [FEATURES.md: Sensei](FEATURES.md#sensei-phase-2-workflow-optimization) — patterns detected, adoption tracking |
| **Smart Tips (Q3)** | Daily actionable tip tailored to what you're doing | [FEATURES.md: Smart Tips](FEATURES.md#smart-tips-q3) — context-aware, feedback-weighted, Sensei-driven |
| **Orphan Detection (Q4)** | Find stale memories, cleanup safely | [FEATURES.md: Orphan Detection](FEATURES.md#orphan-detection-q4) — scoring algorithm, reversible archival |
| **Smart Context (Phase 5)** | Auto-inject relevant memories into prompts | [FEATURES.md: Smart Context](FEATURES.md#smart-context-phase-5) — categorized search, ranking signals |
| **Categorized Memory (Phase 5c)** | Organize knowledge by domain | [FEATURES.md: Categorized Memory](FEATURES.md#categorized-memory-phase-5c) — directory structure, metadata |
| **Auto-Archival (Phase 4)** | Automatically move unused memories to archive | [FEATURES.md: Auto-Archival](FEATURES.md#auto-archival-phase-4) — reversible, high-confidence only |

---

## 🏗️ Architecture & Design

| Topic | What it covers |
|---|---|
| [phases.md](architecture/phases.md) | Complete evolution (Phase 1→5, M0→M2+) with version mapping, milestone summary, M3+ roadmap |
| [positioning.md](positioning.md) | DoDojo vs caveman vs claude-mem — layering + integration |
| [sensei.md](sensei.md) | Sensei opt-in setup, privacy modes, data lifecycle |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| Plugin won't install | [TROUBLESHOOTING.md: Installation](TROUBLESHOOTING.md#plugin-wont-install) |
| Memory files not loading | [TROUBLESHOOTING.md: Memory](TROUBLESHOOTING.md#memory-files-not-loading) |
| Sensei not showing recommendations | [TROUBLESHOOTING.md: Sensei](TROUBLESHOOTING.md#sensei-not-showing-recommendations) |
| Tips not showing in greeter | [TROUBLESHOOTING.md: Smart Tips](TROUBLESHOOTING.md#tips-not-showing-in-greeter) |
| Won't archive memories | [TROUBLESHOOTING.md: Orphan Detection](TROUBLESHOOTING.md#wont-archive-memories) |
| Claude Code slow on startup | [TROUBLESHOOTING.md: Performance](TROUBLESHOOTING.md#claude-code-slow-on-startup) |
| All issues | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — complete guide |

---

## 📖 Command Reference

| Command | Purpose |
|---------|---------|
| `/dodojo:init` | Interactive setup wizard |
| `/dodojo:status` | Show DoDojo status card |
| `/dodojo:health` | Hook smoke-test |
| `/dodojo:recall "pattern"` | Search memories |
| `/dodojo:sensei` | Run Sensei pattern mining + report |

---

## 🪝 Hooks (plugin-managed, registered in settings.json)

| Hook | Event | Purpose |
|------|-------|---------|
| `dodojo-greet.sh` | SessionStart | Greeter banner + pulse stats |
| `sensei-greeter.sh` | SessionStart | Sensei pending recs + adoption |
| `tips-display.sh` | SessionStart | Daily smart tip + rating |
| `smart-context.py` | UserPromptSubmit | Inject relevant memories (top 2) |
| `model-route.sh` | UserPromptSubmit | Classify prompt → suggest model + effort |
| `sensei-telemetry.sh` | Stop | Capture session data (prompts, tokens, tools) |

---

## 🎨 Configuration & Customization

| Topic | What it covers |
|---|---|
| [icons.md](icons.md) | `KAGAMI_ICONS` modes (nerd / unicode / emoji) |
| [theme.md](theme.md) | Greeter themes + `KAGAMI_THEME` |
| [health.md](health.md) | Hook health smoke-test |
| [status.md](status.md) | Greeter pulse stats explanation |

---

## 📦 Organizing Memories

| Topic | What it covers |
|---|---|
| [audit.md](audit.md) | Memory audit + orphan scoring |
| [prune.md](prune.md) | Pruning rules + lifecycle |

---

## 🛣️ Roadmap & Direction

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
