# Changelog

All notable changes documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) loosely; versions follow SemVer.

## [Unreleased]

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
