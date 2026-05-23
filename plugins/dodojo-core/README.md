# dodojo-core

Core dodojo. Zero-token `dj` CLI for plugin stack auditing, session telemetry, greeter banner, heartbeat alerts, and maintenance skills (memory curator, surgical-edit, recall, hook-health, repro-this, pr-describe, etc).

Companion plugins (split for blast-radius isolation):

- **`dodojo-guards`** — assertive safety blockers (secret/force-push/cost guards). Stateless. Install standalone if you only want safety.
- **`dodojo-sensei`** — ROI advisor + weekly digest (Phase 3, not yet split).

## Install

```sh
/plugin marketplace add andriar/dodojo-claude
/plugin install dodojo-core@dodojo
```

For just safety blockers: `dodojo-guards@dodojo`.

## What ships

### Hooks

| Event | Hook | Role |
|-------|------|------|
| SessionStart | `dodojo-greet.sh` | Themed greeter (terminal-only by default; ~0 Claude tokens) |
| SessionStart | `log-session-start.sh` | Session denominator telemetry |
| SessionStart | `heartbeat-check.py` | Detects silent Stop-hook outages |
| SessionStart | `greeter-lean.sh` | One-liner alert when stack has actionable items |
| UserPromptSubmit | `smart-context.py` | Inject relevant memory matches |
| UserPromptSubmit | `skill-suggest.py` | Surface candidate skills |
| UserPromptSubmit | `memory-trigger.py` | Context expansion |
| UserPromptSubmit | `model-route.py` | Verdict hint (trivial/medium/hard) |
| Stop | `session-summary.py` | Per-turn telemetry + memory metadata update |
| Stop | `log-session-stop.sh` | Per-session aggregate |

### CLI (`dj`)

| Command | What it does |
|---------|--------------|
| `dj audit` | Plugin stack token audit; writes Markdown report |
| `dj prune` | Interactive cleanup of unused plugins (`--dry-run` safe) |
| `dj report` | Open latest report in `$EDITOR` |
| `dj stats` | Telemetry file sizes |
| `dj sessions` | Per-session token cost |
| `dj profile-hooks` | Time each registered hook |
| `dj help` | Help |

### Skills (loaded into system reminder)

- `audit-context` — token budget audit
- `archive-orphans` — prune orphan memories
- `memory-curator` — periodic memory health audit
- `surgical-edit` — large-file edit protocol
- `recall` — cross-silo search
- `hook-health` — smoke-test registered hooks
- `route-tune` — model-route rule audit
- `companions` — companion plugin audit
- `new-skill` — scaffold custom skill
- `pr-describe` — draft PR body from diff
- `repro-this` — convert error to minimal repro test

### Commands

`/dodojo:audit`, `/dodojo:prune`, `/dodojo:audit-memory`, `/dodojo:prune-memory`, `/dodojo:health`, `/dodojo:status`, `/dodojo:theme`, `/dodojo:icons`, `/dodojo:init`, `/dodojo:dj-install`, `/dodojo:companions`

## Env knobs

| Var | Default | Effect |
|-----|---------|--------|
| `DODOJO_DATA` | `~/.claude` | User-data root (memory, themes, alerts) |
| `DODOJO_TELEMETRY_HOME` | `$DODOJO_DATA/plugins/data/dodojo-dodojo` | Plugin telemetry root (sessions/, hook logs) |
| `DODOJO_GREETER_MODE` | `terminal` | `inline` to inject banner into Claude context |
| `DODOJO_TELEMETRY_DISABLED` | `0` | Skip session start/stop telemetry |
| `DODOJO_SKIP_HEARTBEAT` | `0` | Skip heartbeat outage check |
| `DODOJO_HEARTBEAT_STALE_HOURS` | `12` | Outage threshold for heartbeat |
| `DODOJO_SKIP_BUDDY_XP` | `0` | Bypass pokemon-buddy XP bridge |
| `DODOJO_POKEMON_XP_QUEUE` | (auto-probe) | Explicit path to buddy XP queue file |

Run `dj profile-hooks SessionStart` to measure per-hook ms.

## Relation to legacy `dodojo` plugin

Until Phase 4, the original `dodojo` plugin manifest still ships the same files at the repo root. Install only one of `dodojo` or `dodojo-core` to avoid double-fire on hooks. New users: prefer `dodojo-core` + opt-in `dodojo-guards`.
