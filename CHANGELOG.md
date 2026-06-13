# Changelog

All notable changes documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely; versions follow SemVer.

## [Unreleased]

## [0.6.0] - 2026-06-13

### Added — memory-graph (dodojo-core) + multi-agent collaboration

- **`memory-graph` skill** (`plugins/dodojo-core/skills/memory-graph/`) — turns the flat memory store into a maintained relation graph. Engine `memory_graph.py` (pure stdlib, also exposed as `dj mg <cmd>`):
  - `report` / `resolve` — canonical `[[wikilink]]` resolution (kebab/snake/path-agnostic, matches stem | `id:` | slugified `name:`), rot + island + duplicate detection.
  - `fix-rot`, `backlink`, `suggest`, `mermaid` — graph maintenance (all mutations need `--apply`).
  - `semantic` / `semantic-dup` — Ollama embedding pass (`OLLAMA_HOST`, default `nomic-embed-text`) for paraphrase-level link/dedup; cached under `~/.claude/.cache/memory-graph/` (NOT the plugin dir), graceful keyword fallback when the daemon is down.
- **memory-dedup-gate hook (default-ON, PreToolUse/Write)** — blocks creating a NEW memory file ≥0.35 similar to an existing one, advising an update instead. Opt out with `MEMGRAPH_GATE_DISABLED=1`. Fail-open if the engine is missing.
- **Multi-agent layer** — `agent/scope/kind/from/run` frontmatter + `retrieve` (scoped semantic lens), `emit` (write a node with provenance + same-kind dedup-gate + embed-cache), `run-graph` (provenance DAG), `set-status`/`--supersede` (lifecycle). Collaboration happens *through the graph*, not inline prompt passing.
- **Role agents** (`plugins/dodojo-core/agents/`): `pm`, `eng`, `qa`, `arbiter` + `DRIVER.md`. Each follows a retrieve→reason→emit→handoff contract via `dj mg`. Validated end-to-end (PM decision → ENG design → QA verdict → arbiter conflict resolution → supersede → accept).
- Design spec: `plugins/dodojo-core/skills/memory-graph/MULTI_AGENT_DESIGN.md`.
- **All plugins bumped 0.5.0 → 0.6.0** (lockstep).

## [0.5.0] - 2026-05-23

### Changed — plugin split Phase 4 (legacy retire + telemetry rename)
- **`dodojo` plugin → v0.5.0, deprecated.** `hooks.json` is now empty (no hooks fire); manifest description carries a deprecation banner pointing users to the three-way split. Marketplace metadata bumped to 0.5.0. No data is lost — telemetry readers merge legacy locations.
- **`DODOJO_TELEMETRY_HOME` default migrated**: `plugins/data/dodojo-dodojo/` → `plugins/data/dodojo-core/`. Readers (`dodojo-greet.py`, `heartbeat-check.py`) now check **three** locations in order: dodojo-core/ → dodojo-dodojo/ → `~/.claude/sessions,hooks/`. Writers always target dodojo-core/.
- **`scripts/migrate-telemetry.sh`** extended with a second pass for `dodojo-dodojo/ → dodojo-core/`. Existing dry-run / `--move` flags unchanged.
- **README** carries a Phase 4 deprecation banner; `docs/architecture/plugin-split-plan.md` marked complete.

Repo-root duplicate files (`hooks/`, `bin/`, `lib/`, `skills/`, `commands/`) intentionally retained for one more grace cycle. They're inert under the deprecated `dodojo` plugin (empty hooks.json) but remain on disk so anyone who pinned a pre-Phase-4 commit can still operate. Removal scheduled for a follow-up PR after telemetry confirms no active v0.4.x installs remain.

### Added — plugin split Phase 3
- **`dodojo-sensei` (new plugin, v0.1.0)** at `plugins/dodojo-sensei/`. Bundles the `sensei` skill, `sensei-greet.sh` SessionStart hook, and `/dodojo:sensei` command. `sensei-telemetry.sh` (Stop hook) and `sensei-2week-report.sh` (systemd one-shot) remain user-installed because they require manual wiring outside the plugin manifest. Pairs with `dodojo-core` — Sensei reads telemetry, recommends ROI automations.
- Marketplace now exposes four plugins: legacy `dodojo` + the three-way split (`dodojo-core`, `dodojo-guards`, `dodojo-sensei`).

### Added — plugin split Phase 2
- **`dodojo-core` (new plugin, v0.1.0)** at `plugins/dodojo-core/`. Full mirror of the current dodojo functionality minus guards (already split as `dodojo-guards`) and sensei (Phase 3). Contains: greeter, heartbeat, session telemetry, smart-context, skill-suggest, model-route, memory-trigger hooks; `dj` CLI; 11 maintenance skills (audit-context, archive-orphans, memory-curator, surgical-edit, recall, hook-health, route-tune, companions, new-skill, pr-describe, repro-this); 11 commands. Installable separately via `/plugin install dodojo-core@dodojo`.
- Marketplace now exposes three plugins. Existing `dodojo` plugin remains functional during transition.

### Added — plugin split Phase 1
- **`dodojo-guards` (new plugin, v0.1.0)** — standalone safety blockers: `secret-guard`, `force-push-guard`, `cost-guard`, plus `inject-git-context`. Zero telemetry, zero skill descriptions, zero shared state. Installable separately via `/plugin install dodojo-guards@dodojo`. Lives at `plugins/dodojo-guards/` in this monorepo.
- **`docs/architecture/plugin-split-plan.md`** — target three-plugin architecture: `dodojo-core`, `dodojo-sensei`, `dodojo-guards`. Rollout in phases; Phase 1 (guards) ships here. Cross-plugin contract = `DODOJO_TELEMETRY_HOME` env var (from v0.4.5).

The existing `dodojo` plugin keeps the same guard hooks during transition — users who only update the marketplace don't lose protection. Reinstall to swap to the standalone `dodojo-guards` when ready.

## [0.4.5] - 2026-05-23

### Added
- **`lib/paths.py`** — canonical path helper that separates user-owned data (`~/.claude/memory/`, themes, alerts) from plugin telemetry (`~/.claude/plugins/data/dodojo-dodojo/sessions/`, `…/hooks/`). Override via `DODOJO_TELEMETRY_HOME`.
- **`scripts/migrate-telemetry.sh`** — one-shot copy/move of historical `sessions/*.jsonl` and known plugin hook logs from `~/.claude/` to `plugins/data/dodojo-dodojo/`. Safe (copy by default), `--move` to relocate, `--dry-run` to preview.
- **`bin/profile-hooks.sh`** + **`dj profile-hooks`** — time each registered hook with a synthetic payload. Surfaces SessionStart cold-start budget.
- **`DODOJO_SKIP_HEARTBEAT=1`** env opt-out for the heartbeat hook.
- **`DODOJO_POKEMON_XP_QUEUE`** env var — explicit path to the pokemon-buddy XP queue. Most explicit way to wire the bridge; takes precedence over `POKEMON_BUDDY_HOME`.

### Changed
- **Namespace migration with compat shim.** Writers (`session-summary.py`, `smart-context.py`) now write to `plugins/data/dodojo-dodojo/{sessions,hooks}/`. Readers (`dodojo-greet.py`, `heartbeat-check.py`) merge both the new canonical location and the legacy `~/.claude/{sessions,hooks}/` location so historical data is not lost. No env-var changes required.
- **Pokemon-buddy XP bridge is opt-in.** `session-summary.py` no longer falls back to `~/.claude/` when pokemon-buddy is not installed — it requires either `DODOJO_POKEMON_XP_QUEUE` or a sentinel `buddy-pokemon.md` file under a known candidate dir. Previously, the bridge wrote `buddy-xp-pending.jsonl` to a ghost location when buddy was uninstalled. Bypass entirely with `DODOJO_SKIP_BUDDY_XP=1`.

## [0.4.4] - 2026-05-23

### Added
- **Heartbeat alert** (`hooks/heartbeat-check.py`, SessionStart). Detects silent Stop-hook outage by comparing latest `sessions/*.jsonl` mtime vs latest `projects/**/*.jsonl` mtime. Writes one warn-level entry to `alerts.jsonl` per outage window (idempotent). Threshold via `DODOJO_HEARTBEAT_STALE_HOURS` (default 12).
- **Cache GC** (`scripts/cache-gc.sh`). Dry-run by default, `--apply` to delete. Keeps `KEEP` newest semver versions in `~/.claude/plugins/cache/dodojo/dodojo/`.
- **Schema version** `"v": 2` on records emitted by `session-summary.py` and `bin/log-session-stop.sh`. Greeter aggregators already use `.get(key, default)` so v1 records remain readable.

### Changed
- **Turn identity by `session_id`** (not wall clock). `smart-context.py` now records `session_id` on each telemetry entry; `session-summary.py` matches `memories_injected` by ID with a `±600s` fallback for legacy v1 records. Eliminates cross-session attribution noise.
- **Atomic memory metadata write**. `lib/memory_categorizer.update_memory_metadata` writes via sibling `.tmp` + `os.replace`. Prevents truncation on crash and removes the race window when parallel Stop hooks update the same memory file.
- **Disambiguation docs** (`docs/command-disambiguation.md`, `docs/hook-taxonomy.md`). Maps `audit` / `audit-memory` / `prune` / `prune-memory` to their actual domains; documents which hooks are assertive (block on exit 2) vs passive (additive only).
- **Command title typos** fixed in `commands/audit-memory.md` and `commands/prune-memory.md` (both rendered as `/dodojo:audit` / `/dodojo:prune` regardless of file name).

### Fixed
- **Double-registered Stop hook**. Documentation reminder: `log-session-stop.sh` should only be registered via plugin `hooks.json` — duplicate entries in user `~/.claude/settings.json` cause every Stop record to be written twice. Migration users: remove the manual entry.

## [0.4.3] - 2026-05-23

### Fixed — race condition between greeter and refresh

**Bug**: `greeter-lean.sh` read state from disk before the backgrounded
`refresh-audit.sh` finished writing it. Greeter consistently showed stale
data from the previous session.

**Fix**: greeter now refreshes state inline (synchronously) when stale,
then reads. Smart caching avoids the cost when state is recent:

- State < 5 min old → reuse (24ms total)
- State stale or missing → run audit synchronously (93ms total)

### Changed

- Removed `refresh-audit.sh` from `hooks.json` SessionStart — greeter handles
  refresh now. (Script file kept in `bin/` for users who still reference it
  in their own settings.)
- Greeter hook timeout raised 2000ms → 5000ms to accommodate inline audit.

## [0.4.2] - 2026-05-23

### Changed

- **`bin/statusline.sh` — clearer default rendering.** The bar now shows labeled output by default:
  ```
  🪙 7.5K passive · ↑64K session · 2🪓 to prune
  🪙 7.5K passive · ✓ clean
  ```
  Previously the segments were unlabeled (`dj 7.5K ↑64K · 2🪓`) and required the user to know what each number meant. The new default explains itself.

### Added

- **`DJ_STATUSLINE_MODE=compact`** — opt-in short form for narrow terminals:
  ```
  dj 7.5K ↑64K · 2🪓
  dj 7.5K ✓
  ```
- **`DJ_STATUSLINE_NOICONS=1`** — text fallbacks (`$`, `x`, `^`, `ok`) for terminals without emoji rendering
- **Clean-state indicator** — when `prune_candidates == 0`, statusline shows `✓ clean` instead of `0🪓` — meaningful absence instead of meaningless zero

## [0.4.1] - 2026-05-23

### Added

- **`bin/greeter-lean.sh`** + **SessionStart hook** — minimal greeter that prints **one line** only when there's actionable info (prune candidates ≥1, or passive load ≥12K tokens). Silent when stack is clean (0 tokens). Costs ~15 tokens when speaking. Reads pre-computed state from `~/.claude/dodojo/state/audit-stack.json` — no scanning at hook time.

Designed as the lean alternative to `dodojo-greet.sh`. The two can coexist:
- `dodojo-greet.sh` (heavy, themed) — already terminal-only by default via `DODOJO_GREETER_MODE=terminal`, so adds 0 Claude tokens
- `greeter-lean.sh` (one-liner alert) — fires as `additionalContext`, but silent until something needs attention

Together they support the philosophy: visibility ≠ passive context. The terminal greeter is shell visibility (free); the lean greeter is sparse Claude visibility (cheap, only when warranted).

## [0.4.0] - 2026-05-23

### Added — Lean architecture pivot

The plugin now leads with **scripts-first, skills-as-escalation**. New tagline: *Free until you ask.*

- **`bin/dj` CLI** — single shell entrypoint for zero-token operations
  - `dj audit` — plugin stack token audit
  - `dj prune` — interactive plugin cleanup (`--dry-run`, `-y`, `q` to quit)
  - `dj report` — open latest report in `$EDITOR`
  - `dj sessions` — per-session token cost (parsed from transcript)
  - `dj stats` — telemetry file sizes
- **`bin/audit-stack.py`** — measures passive load per session: base layer (CLAUDE.md, @-refs, INDEX.md) + project layer + plugin layer (skill descriptions in system reminder). Cross-references `enabledPlugins` and skill-usage telemetry. Writes Markdown report to `~/.claude/dodojo/reports/`.
- **`bin/prune.py`** — interactive plugin cleanup with safety guards. Defaults to No, shows full `rm -rf` path, warns on enabled plugins, supports dry-run.
- **`bin/statusline.sh`** — always-visible passive cost in your status bar. Color-coded (green/yellow/red). Cumulative session tokens shown as `↑X.XM`. Reads from JSON state file; 0 tokens per render.
- **`bin/statusline-composed.sh`** — composes dj segment with pokemon-buddy or any other statusline. Version-agnostic poke detection.
- **`bin/refresh-audit.sh`** — SessionStart hook that backgrounds `dj audit` so the statusline always shows fresh numbers without blocking startup.
- **`bin/log-session-start.sh`** + **`bin/log-session-stop.sh`** — local-only telemetry: session count (denominator), per-session token spend (input + output + cache read + cache write), tool/skill/plugin invocation counts.
- **`/dodojo:dj-install` command** + `scripts/dj-install.sh` — bootstraps `dj` symlink to `~/.local/bin/dj`. Idempotent.
- **`docs/lean-architecture.md`** — design philosophy: scripts own data, Claude owns judgment; reports are artifacts not conversations; statuslines > daemons.

### Changed

- **`/dodojo:audit`** — now invokes `bin/audit-stack.py` (zero tokens). The old skill-based memory audit is preserved as **`/dodojo:audit-memory`**.
- **`/dodojo:prune`** — now invokes `bin/prune.py` (zero tokens, plugin cleanup). The old orphan-memory pruner is preserved as **`/dodojo:prune-memory`**.
- **`hooks.json`** — adds 3 new entries under SessionStart and Stop for telemetry + audit refresh.
- **`README.md`** — rewritten to lead with the lean positioning. Old README's feature taxonomy archived in git history.
- **Plugin description** — updated in `plugin.json` and `marketplace.json` to reflect new positioning.

### The big finding

While auditing a typical stack, discovered that `"enabled": false` in `~/.claude/settings.json` does NOT prevent skill descriptions from loading into the system reminder. Disabled plugins still cost tokens per session. Removing one "disabled" plugin saved exactly the predicted passive tokens (587) and 198MB of disk on the test machine. Reproducibility steps in README.

### Notes for upgraders

- All existing skills (memory-curator, recall, sensei, archive-orphans, audit-context, etc.) remain unchanged and accessible.
- Memory-focused commands are renamed with `-memory` suffix to make room for the new lean commands.
- Run `/dodojo:dj-install` after upgrading to bootstrap the `dj` CLI on your PATH.

## [0.3.36] - 2026-05-13

### Changed
- `cost-guard` hook now enforces `dodojo:surgical-edit` protocol: blocks `Read` calls on files >5K lines / >300KB unless `offset`+`limit` are set. Stops the model from token-bombing on huge blade/generated files. Tested against a real 14,992-line / 785KB blade — blocked with ~209K-token estimate and surgical-edit guidance, while small files and windowed Reads pass clean.

## [0.3.35] - 2026-05-13

### Added
- `dodojo:surgical-edit` skill — runtime token-saver for big files (>5K lines / >300KB). Protocol: grep+offset Read, no full-file reload, no re-Read on same file. Auto-triggers when user touches files like `inbox.blade.php` (15K lines) or flags a file as "gede"/"huge". Real case: prior session burned ~1M tokens on 15× full Reads of one 800KB blade — surgical-edit cuts that to ~10K tokens (~100× savings).

## [0.3.34] - 2026-05-11

## [0.3.33] - 2026-05-11

## [0.3.32] - 2026-05-11

## [0.3.31] - 2026-05-11

### Added
- `/dodojo:theme` interactive picker — call without arg → `AskUserQuestion` drill-down (group → theme) instead of requiring name upfront

## [0.3.30] - 2026-05-05

## [0.3.29] - 2026-05-05

## [0.3.27] - 2026-05-05

### Added
- **Sensei Phase 2: Workflow Optimization** — Smart advisor that detects friction patterns and recommends improvements
  - `scripts/sensei-analyzer.py` — mines session telemetry, detects 5 pattern types (repeated reads, follow-ups, tool misuse, memory gaps, token waste), ranks by impact
  - `scripts/sensei-summary.py` — formats analysis for greeter (1 pattern) + full report (5 patterns)
  - `scripts/sensei-adoption.py` — tracks if user implemented recommendations
  - `hooks/sensei-telemetry.sh` — Stop hook captures prompts, tokens, tools, files per session → `~/.claude/sensei/telemetry.jsonl`
  - `hooks/sensei-greeter.sh` — SessionStart hook runs analyzer, displays top pattern in greeter
  - `docs/sensei-optimization.md` — user guide (patterns, examples, privacy, usage)
  - `docs/sensei-phase2-telemetry.md` — technical spec (schema, detection rules, output format)
- Sensei shows 1 optimization recommendation in greeter automatically
- `/sensei-report` script displays all patterns + adoption tracking + token savings estimate

### How It Works
1. **Collect**: Stop hook captures prompts, tokens, tools, files per session
2. **Analyze**: Analyzer detects patterns (repeated reads, follow-ups, tool misuse, etc)
3. **Recommend**: Greeter shows top pattern + specific suggestion + savings estimate
4. **Track**: User marks recommendation as adopted, next report shows progress

### Example Pattern
```
🟡 Follow Up Chain (clarification loops: 3.0 prompts/task)
   → Structure prompts: [goal]. Context: [X]. Format: [Y]. Examples: [Z]
   💰 428 tokens/week savings
```

### M2 + Sensei Phase 2 Complete
- ✅ Smart categorized memory (Phase 5c)
- ✅ Context optimization (Phase 5)
- ✅ Auto-archival infrastructure (Phase 4)
- ✅ **Sensei Phase 2: workflow optimization** (NEW)
- ✅ All documentation + guides
- Ready for external dogfooding + feedback loop

## [0.3.26] - 2026-05-04

### Added
- **Phase 5: Smart Categorization** — Memory system now auto-detects domain (frontend/backend/devops/infra/patterns/setup/general), searches only relevant category (78% smaller search space), and auto-ranks by reuse frequency + recency + cwd match
  - `lib/memory_categorizer.py` — core functions: auto-detection, ranking, metadata management
  - `scripts/migrate-memories-to-v2.py` — migrates flat memory structure to categorized subdirs with metadata
  - All memories auto-populated with `id`, `category`, `created`, `reuses`, `last_used` fields
- **Phase 4: Maintenance Infrastructure** — Auto-archive stale memories (unused 6mo+ or never-reused after 30d) to prevent unbounded growth
  - `scripts/archive-stale-memories.py` — dry-run/commit modes, reversible manifest
  - `hooks/memory-archive-candidates.py` — Sensei weekly recommendations for cleanup
  - `docs/phase4-maintenance.md` — usage guide + thresholds
- `docs/phase5-smart-categories.md` — smart categorization architecture + performance impact
- `PHASE5_MIGRATION.md` — step-by-step migration checklist with verification + rollback

### Changed
- Smart-context hook now uses categorized search (Phase 5a integration)
- Session-summary hook auto-updates memory `reuses` and `last_used` on injection (Phase 5b)
- INDEX.md links updated to point to categorized memory paths

### M2 Milestone Complete
- ✅ Honest metrics (real reuse stats, no estimation)
- ✅ Context optimization (cap injection to top 2, save 60% tokens)
- ✅ Smart categorization (categorized search + auto-ranking)
- ✅ Maintenance infrastructure (auto-archive stale)
- ✅ Documentation (quickstart + positioning + roadmap + demo)

Ready for external dogfooding (3 users post-launch).

## [0.3.25] - 2026-05-03

### Added
- `docs/positioning.md` — DoDojo vs caveman vs claude-mem (orthogonal layers)
- `docs/sensei.md` — opt-in rationale, setup cascade, privacy modes, roadmap
- `docs/theme.md`, `docs/icons.md`, `docs/audit.md`, `docs/prune.md`, `docs/health.md`, `docs/status.md` — fill in 6 broken index links
- `docs/assets/image-1.png` — greeter hero screenshot, embedded in README + status.md
- `ROADMAP.md` — M1/M2/M3 milestones with completion %
- `SENSEI_FULL_HISTORY` env var — opt-in to scrape full command + args
- `tests/test_sensei_config.py` — vault detection cascade coverage

### Changed
- Sensei vault detection now cascades: explicit env > auto-detect Obsidian (4 paths) > fallback `~/.claude/dodojo/sensei/reports/`
- `collect.sh` zsh scrape strips args + env-var prefix by default (privacy); full args opt-in via `SENSEI_FULL_HISTORY=1`
- `dodojo-init.sh` wizard suggests auto-detected vault, no longer hardcodes Obsidian path

## [0.3.24] - 2026-05-03

### Added
- `CHANGELOG.md` — release history file
- `scripts/bump.sh` auto-promotes `[Unreleased]` → `[NEW] - YYYY-MM-DD` and stages the file

## [0.3.23] - 2026-05-03

### Added
- `model-route` UserPromptSubmit hook — classifies each prompt → suggests model + effort (haiku/sonnet/opus) via additionalContext
- `routing/` plugin defaults (5 seed rules: refactor, security, lookup, scaffold, bugfix); user overrides at `~/.claude/memory/routing/`
- Greeter `Route` section — 7-day verdict mix + uncovered % nudge
- `route-tune` skill — audits log, flags mis-routes, proposes new rules

## [0.3.22] - 2026-05-03

### Fixed
- `scripts/collect.sh` SC2155: split `local` decl from `$(...)` assign
- `scripts/bump.sh` SC2115 + SC2155 safety
- CI shellcheck severity gate (info → warning+)
- `dodojo-greet` test mode-gating

### Changed
- CI coverage widened to scripts/skills py+sh, version-sync gate, JSON validity

## [0.3.21] - 2026-05-03

### Fixed
- `sensei-greet` missing on session start
- All-clear banner for zero-state visibility
- Wizard + docs sync
