# Changelog

All notable changes documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely; versions follow SemVer.

## [Unreleased]

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
