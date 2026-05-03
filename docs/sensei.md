# Sensei — pattern miner + ROI advisor

Sensei observes how you actually work, ranks repetitive patterns by ROI, and recommends automations weekly. Pair with **Kagami** (memory mirror): Sensei = action-advisor, Kagami = fact-keeper.

## Why opt-in (and what changed)

Originally Sensei required Obsidian. Now it auto-detects + falls back, so the friction is mostly gone — but it stays opt-in for three reasons:

1. **Privacy** — Sensei reads your shell history. By default it strips command args (keeps cmd name only) to shrink the secret surface, but you should know it's reading.
2. **Output storage** — weekly markdown lands somewhere. We auto-detect Obsidian; if absent, fall back to `~/.claude/dodojo/sensei/reports/`. Either way, you opt-in to the writes.
3. **Repo scanning** — `git log` walks your repo roots (default `~/Development`). You should know the scope before enabling.

## Setup cascade

`SENSEI_VAULT` resolves in this order (first match wins):

1. **Explicit env var** — `SENSEI_VAULT=/some/path`
2. **Auto-detect Obsidian** — first existing of:
   - `~/Documents/Obsidian Vault`
   - `~/Obsidian`
   - `~/vaults`
   - `~/Documents/vaults`
3. **Fallback** — `~/.claude/dodojo/sensei/reports/` (always works, no Obsidian needed)

Run `/dodojo:init` → "Enable Sensei?" → "Use defaults?" — it picks the right path automatically.

## Privacy modes

| Var | Default | What it does |
|-----|---------|--------------|
| `SENSEI_HISTORY` | `~/.zsh_history` | Path to shell history file |
| `SENSEI_FULL_HISTORY` | `0` (off) | When `1`, keep full command + args. Default keeps cmd name only and strips `FOO=bar` env prefixes |
| `SENSEI_REPOS` | `~/Development` | Colon-separated repo roots for `git log` scan |
| `SENSEI_VAULT` | (auto-detect) | Output dir for weekly markdown |
| `SENSEI_STATE` | `~/.claude/dodojo/sensei` | State files (weights, feedback, raw events) |

Exclusions: `state/exclusions.txt` filters out paths/patterns matching `.env*`, `*credential*`, `*secret*`, `*.key`, vaultwarden, etc. Edit to add your own.

## Pipeline

1. **collect** (`scripts/collect.sh`) — scrapes zsh history (cmd names by default), claude-mem timeline, `git log`, hook telemetry → `state/raw.tsv`
2. **score** (`scripts/score.py`) — `ROI = freq × est_time_per_run / est_effort_to_automate`. Weights tunable in `state/weights.json`
3. **report** (`scripts/report.py`) — render markdown to `$SENSEI_VAULT/weekly-YYYY-MM-DD.md`
4. **approve** — accept/reject via `/sensei accept <id>` or `/sensei reject <id> <reason>`. Decisions log to `state/feedback.jsonl`

## Self-improvement layers

- **L1 Tuning** (auto): accepted recs nudge weights toward dominant features. Rejected = penalize
- **L2 Heuristic** (auto): pattern rejected 3× → auto-disable detector
- **L3 Skill-gen** (manual): Sensei drafts skill skeleton → `~/.claude/skills/_drafts/`. User runs `/sensei approve <name>` to activate
- **Anti reward-hacking**: tracks 2-week outcome (rec actually used) not just accept rate. 10% epsilon-greedy exploration

## Trigger

```bash
# Manual
/sensei                        # in Claude
python3 .../skills/sensei/scripts/report.py --dry   # preview to stdout

# Weekly cron
0 9 * * 1  python3 ~/.claude/plugins/cache/dodojo/dodojo/<ver>/skills/sensei/scripts/report.py
```

## Roadmap

Sensei is the most ambitious DoDojo subsystem. Open improvements:

- [ ] Default-on for fresh installs once auto-detect proven across 10+ users
- [ ] Per-shell history adapters (bash, fish) — currently zsh-only
- [ ] Built-in cron registration via `/sensei cron-install`
- [ ] Web dashboard for accept/reject (currently markdown-only)
- [ ] Cross-machine sync (state files → git-tracked dotfiles)

File issues at `andriar/dodojo-claude` for prioritization.

## Related

- [positioning.md](positioning.md) — why Sensei is one of DoDojo's six layers
- [status.md](status.md) — Sensei pending recs surface in the greeter banner
- [audit.md](audit.md) — companion: Sensei mines patterns, audit measures bloat
