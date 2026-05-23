---
description: Sensei — pattern miner + ROI advisor (paired with Kagami memory layer)
argument-hint: "[review | accept <id> | reject <id> --reason ... | weights | history]"
---

Run Sensei pipeline. Mines work patterns from zsh history + claude-mem timeline + git log → ranks by ROI → renders Obsidian markdown report.

## Usage

| Action | Command (run in shell) |
|---|---|
| Generate weekly report | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/report.py` |
| Dry run | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/report.py --dry` |
| Accept rec | `${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/decide.py accept <id>` |
| Reject rec | `${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/decide.py reject <id> --reason "..."` |
| Defer | `${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/decide.py later <id>` |
| Outcome check | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/outcome.py` |

## Required env (in `~/.claude/settings.json` → `env`)

| Var | Default | Purpose |
|---|---|---|
| `SENSEI_HOME` | `${CLAUDE_PLUGIN_ROOT}/skills/sensei` | Skill root (scripts + templates) |
| `SENSEI_STATE` | `~/.claude/dodojo/sensei` | weights/feedback/raw.tsv (user-local) |
| `SENSEI_VAULT` | `~/Documents/Obsidian Vault/Sensei` | Where weekly markdown lands |
| `SENSEI_HISTORY` | `~/.zsh_history` | Shell history source |
| `SENSEI_REPOS` | `~/Development` | Colon-separated repo roots for git-log mining |

## Optional dependencies

- **claude-mem plugin** — for session timeline mining (skipped if absent)
- **Obsidian** — output target (skipped if `SENSEI_VAULT` unwritable)
- **zsh** — bash history works too, point `SENSEI_HISTORY` at `~/.bash_history`

## Pair with Kagami

Accepted recs → Kagami auto-reflects to memory. Rejected recs → scorer L1-tunes weights. Pattern rejected 3× → detector auto-disabled (L2).
