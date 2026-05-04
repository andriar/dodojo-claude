# Changelog

All notable changes documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely; versions follow SemVer.

## [Unreleased]

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
