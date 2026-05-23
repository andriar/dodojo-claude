---
name: sensei
description: Meta-organizer agent. Mines work patterns (zsh history + claude-mem timeline + git log) and recommends top-ROI automations weekly. Pair with Kagami (memory mirror) — Sensei is the action-advisor, Kagami is the fact-keeper. Use when user says "sensei review", "what should I automate", or for weekly ROI digest.
domain: meta
category: ops
user_invocable: true
---

# Sensei — work pattern miner + ROI advisor

## Role
Observe how user works → detect repetitive patterns → rank by ROI → recommend automations. Manual approval required for all recommendations.

## Pipeline
1. **collect** (`scripts/collect.sh`) — scrape last N days from:
   - `~/.zsh_history` (commands)
   - `claude-mem` timeline (sessions, tasks)
   - `git log --author=me --all-branches` (commit pattern, file churn)
   - **Excluded**: `.env*`, `*credential*`, `*secret*`, `*.key`, vaultwarden paths
2. **score** (`scripts/score.py`) — ROI = freq × est_time_per_run / est_effort_to_automate. Linear weighted sum, weights in `state/weights.json`.
3. **report** (`scripts/report.sh`) — render markdown → Obsidian vault `~/Documents/Obsidian Vault/Sensei/weekly-YYYY-MM-DD.md`
4. **approve** — user accepts/rejects via response. Decisions logged to `state/feedback.jsonl`. Bobot scorer adjust based on accept/reject.

## State files
- `state/weights.json` — scorer weights (tunable)
- `state/feedback.jsonl` — accept/reject log (one line per decision)
- `state/patterns_seen.json` — detected patterns history (avoid duplicate recs)
- `state/exclusions.txt` — user-managed deny list

## Slash trigger / scripts

Plugin paths use `${CLAUDE_PLUGIN_ROOT}`. For ad-hoc shell, resolve to
`~/.claude/plugins/cache/dodojo/dodojo/<version>/skills/sensei/scripts/`.

| Action | Command |
|--------|---------|
| Generate weekly | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/report.py` |
| Dry run | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/report.py --dry` |
| Accept rec | `${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/decide.py accept <pattern_id>` |
| Reject rec | `${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/decide.py reject <pattern_id> --reason "..."` |
| Defer | `${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/decide.py later <pattern_id>` |
| Show weights | `${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/decide.py weights` |
| Show disabled rules | `${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/decide.py rules` |
| Decision history | `${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/decide.py history` |
| Outcome check | `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sensei/scripts/outcome.py [--write-report]` |

## Required env vars (override defaults)

| Var | Default | Purpose |
|---|---|---|
| `SENSEI_HOME` | `${CLAUDE_PLUGIN_ROOT}/skills/sensei` | Skill root (scripts + templates, read-only) |
| `SENSEI_STATE` | `~/.claude/dodojo/sensei` | weights/feedback/raw.tsv (user-local) |
| `SENSEI_VAULT` | `~/Documents/Obsidian Vault/Sensei` | Markdown report output |
| `SENSEI_HISTORY` | `~/.zsh_history` | Shell history source |
| `SENSEI_REPOS` | `~/Development` | Colon-separated repo roots |

## Cadence (cron)
- **Weekly Mon 09:00** — `report.py` writes Obsidian
- **Biweekly 1st & 15th 09:00** — `outcome.py --write-report` checks 14d-old accepts, penalizes abandoned kinds
- Ad-hoc: invoke skill / scripts directly

## Self-improvement (L1 + L2)
- **L1 Tuning** (auto): accepted recs → gradient nudge weights toward dominant features. Rejected → penalize.
- **L2 Heuristic** (auto): pattern reject 3x → auto-disable detector rule. User flag manual via `/sensei add-rule`.
- **L3 Skill-gen** (manual approval): Sensei drafts skill skeleton to `~/.claude/skills/_drafts/`. User runs `/sensei approve <name>` to activate.
- **Anti reward-hacking**: track outcome (rec actually used 2 weeks later) not just accept rate. 10% epsilon-greedy exploration.

## Output format

```markdown
# Sensei Weekly — 2026-05-04

## Top recommendations (ranked by ROI)

### 1. Auto-commit msg from ticket ID  [score: 87]
**Pattern**: `git commit -m` followed by branch name 12x this week
**Why high ROI**: 12× per week × 30s saved × low effort (script)
**Proposed**: skill `commit-from-ticket` — parse branch → fetch ticket title → conventional commit
**Decision**: [ ] accept  [ ] reject  [ ] later
```

## Pair with Kagami
Sensei accepted recs → write project memory note via Kagami auto-reflect. Kagami stores **what was decided**, Sensei stores **why it was recommended**.
