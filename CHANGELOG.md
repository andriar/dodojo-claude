# Changelog

All notable changes documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely; versions follow SemVer.

## [Unreleased]

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
