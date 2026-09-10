# dodojo-sensei

Meta-organizer for your Claude Code workflow. Mines work patterns (zsh history, claude-mem timeline, git log) and surfaces top-ROI automation recommendations weekly.

Sensei is the **action-advisor**. Pairs with `dodojo-core` (the **fact-keeper**) — Sensei reads core's telemetry to decide what's worth automating.

## Install

```sh
/plugin marketplace add andriar/dodojo-claude
/plugin install dodojo-sensei@dodojo
```

Requires `dodojo-core` (or legacy `dodojo`) for telemetry source. Without it, Sensei has no signal to mine.

## What ships

| Component | Role |
|-----------|------|
| `hooks/sensei-greet.sh` | SessionStart — surfaces pending Sensei recs |
| `skills/sensei` | The Sensei skill itself (review, ideas, decide) |
| `commands/sensei.md` | `/dodojo:sensei` slash command |

`sensei-2week-report.sh` (systemd) stays a user-installed script — it needs a manual unit. See the skill's docs.

`sensei-telemetry.sh` is gone (0.6.3): it was registered nowhere and could not write even when run by hand, because its heredoc `python3` received no argv and bailed on a `None` transcript path. Sensei now analyses the session records `dodojo-core`'s `session-summary.py` already writes on every Stop.

## Cross-plugin contract

Sensei reads the session records dodojo-core writes under `DODOJO_TELEMETRY_HOME` (defaults to `~/.claude/plugins/data/dodojo-core/`), newest location first, then the legacy `dodojo-dodojo/` and `~/.claude/sessions/` dirs, then any historical `sensei/telemetry.jsonl`. As long as both plugins are installed in the same Claude Code, the data flows.

## Env knobs

| Var | Default | Effect |
|-----|---------|--------|
| `SENSEI_STATE` | `$DODOJO_DATA/dodojo/sensei` | Where Sensei stores recommendations + feedback |
| `SENSEI_VAULT` | `~/sensei-reports` | Where weekly reports get written |
| `SENSEI_HOME` | (plugin root) | Override skill scripts location |

## Relation to other dodojo plugins

- **dodojo-core** — telemetry source. Required.
- **dodojo-guards** — independent. Sensei can advise on guard policy but doesn't depend on it.
- **dodojo** (legacy) — bundles sensei. Until Phase 4, install only one of `dodojo` or `dodojo-sensei` to avoid double-fire.
