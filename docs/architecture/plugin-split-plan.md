# Plugin split plan

Status: **in progress**. Phase 1 (guards) ✅ shipped v0.1.0. Phase 2 (core) ✅ shipped v0.1.0. Phase 3 (sensei) and Phase 4 (legacy retire) pending.

## Motivation

`dodojo` currently bundles 4 subsystems under one plugin manifest:

| Subsystem | Hooks | Skills | Role |
|-----------|-------|--------|------|
| **Greeter + telemetry** | dodojo-greet, greeter-lean, log-session-start/stop, session-summary, smart-context, model-route, skill-suggest, memory-trigger, heartbeat-check | audit-context, archive-orphans, memory-curator, surgical-edit, repro-this, pr-describe, recall, hook-health, route-tune, companions, new-skill | Observe + inject context |
| **Guards** | secret-guard, force-push-guard, cost-guard, inject-git-context | — | Block dangerous tool calls |
| **Sensei** | sensei-greet, sensei-telemetry, sensei-2week-report | sensei | Weekly ROI digest |
| **CLI / scripts** | (none — `dj` is a shell entry point) | — | Zero-token ops |

Issues with single-plugin packaging:

- **Blast radius** — a bug in any subsystem disables everything (the 2026-05-20..22 outage took down telemetry *and* guards).
- **Naming collision** — `audit` / `audit-memory`, `prune` / `prune-memory` overload because all skills compete in one namespace.
- **Install size** — users who only want guards still load all skill descriptions in the system reminder.
- **Versioning friction** — a sensei-only change forces a bump that re-deploys everything.

## Target architecture

Split into three plugins distributed from this same monorepo (multi-plugin marketplace):

### dodojo-guards (Phase 1 — this PR)

| Files | Role |
|-------|------|
| `hooks/secret-guard.sh` | Block secrets in Write/Edit/Bash payloads |
| `hooks/force-push-guard.sh` | Block force-push to main/master |
| `hooks/cost-guard.py` | Block runaway Bash + huge file Reads |
| `hooks/inject-git-context.sh` | UserPromptSubmit: current branch + dirty flag |

Pure PreToolUse + UserPromptSubmit assertive hooks. **Zero shared state** with the other subsystems — easiest split. Independent versioning lets safety patches ship without touching telemetry code.

### dodojo-core (Phase 2)

| Files | Role |
|-------|------|
| `bin/dj` + all `bin/*` | CLI |
| `hooks/dodojo-greet.{sh,py}`, `bin/greeter-lean.sh` | Greeter |
| `hooks/heartbeat-check.py` | Telemetry health |
| `hooks/log-session-{start,stop}.sh`, `hooks/session-summary.py` | Session telemetry |
| `hooks/smart-context.py`, `hooks/skill-suggest.py`, `hooks/model-route.py`, `hooks/memory-trigger.py` | Context injectors |
| `skills/audit-context, archive-orphans, memory-curator, surgical-edit, recall, hook-health, route-tune, companions, repro-this, pr-describe, new-skill` | Maintenance skills |
| `lib/*` | Shared helpers |

Owns `~/.claude/plugins/data/dodojo-core/` for telemetry (was `dodojo-dodojo`).

### dodojo-sensei (Phase 3)

| Files | Role |
|-------|------|
| `hooks/sensei-greet.{sh,sh,py}`, `hooks/sensei-telemetry.sh`, `hooks/sensei-2week-report.sh` | Sensei greeter + telemetry |
| `skills/sensei` | Sensei skill |
| `routing/*` (sensei-specific) | Route hint authoring |

Depends on `dodojo-core` telemetry. Reads from `DODOJO_TELEMETRY_HOME` (cross-plugin contract — already env-var addressable since v0.4.5).

## Cross-plugin contract

The single env var **`DODOJO_TELEMETRY_HOME`** (introduced in v0.4.5) is the data interface. Plugins:

- **dodojo-core** WRITES to `$DODOJO_TELEMETRY_HOME/{sessions,hooks}/`
- **dodojo-sensei** READS from same paths for ROI analysis
- **dodojo-guards** writes NOTHING — pure stateless blockers

If `DODOJO_TELEMETRY_HOME` is unset, default = `~/.claude/plugins/data/dodojo-core/` (renamed from `dodojo-dodojo`).

## Migration for existing users

| Currently installed | After split |
|--------------------|-------------|
| `dodojo` 0.4.5 | Install `dodojo-core` + `dodojo-guards`; sensei optional |
| Just want guards | Install `dodojo-guards` only — drops ~3K tokens of skill descriptions |
| Just want greeter, no telemetry | Install `dodojo-core` with `DODOJO_TELEMETRY_DISABLED=1` |

A `dodojo` meta-package (this repo's existing manifest) will continue to install all three plugins together for one session, so existing users see no disruption.

## Rollout

1. **Phase 1** ✅ — Extracted `dodojo-guards` at `plugins/dodojo-guards/`. Marketplace exposes two plugins. Existing `dodojo` plugin keeps guard hooks for compat.
2. **Phase 2** ✅ — Extracted `dodojo-core` at `plugins/dodojo-core/`. Telemetry dir name kept as `dodojo-dodojo` for now (rename to `dodojo-core` deferred to Phase 4 to avoid mid-split data move). Marketplace exposes three plugins.
3. **Phase 3** — Extract `dodojo-sensei` at `plugins/dodojo-sensei/`. Move sensei skill + greet/telemetry hooks. Remove sensei from `dodojo` manifest.
4. **Phase 4** — `dodojo` becomes a meta manifest that pulls in core + guards + sensei. Rename telemetry to `dodojo-core/`. Deprecate the meta-package after 2-3 weeks.

Each phase is independently shippable + reversible.
