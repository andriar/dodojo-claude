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

Other Sensei pieces (`sensei-telemetry.sh` for Stop, `sensei-2week-report.sh` for systemd) are user-installed scripts — not bundled here because they require manual systemd unit setup and user-settings hook registration. See the skill's docs.

## Cross-plugin contract

Sensei reads from `DODOJO_TELEMETRY_HOME` (defaults to `~/.claude/plugins/data/dodojo-dodojo/`). This is the same env var dodojo-core writes to. As long as both plugins are installed in the same Claude Code, the data flows.

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
