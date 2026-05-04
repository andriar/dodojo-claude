# Roadmap

Project goals + completion estimate. Single-source for "what's left".

## End goal

> **Quiet workflow discipline for Claude Code, deployable in one command, useful for any indie dev within 5 minutes of install.**

Three readiness milestones below. v1.0 = M2 done.

---

## M1 — Feature complete (~90% done)

Six core layers shipped. Last gaps:

- [x] **Mirror** (Kagami) — memory + auto-reflect
- [x] **Coach** (Sensei) — pattern miner + ROI advisor
- [x] **Context** — smart-context retrieval
- [x] **Audit** — orphan + memory pruning
- [x] **Route** — model picker (v0.3.23)
- [x] **Meter** — token-saved counter
- [ ] Sensei default-on (currently opt-in; needs vault auto-detect proven across 10+ users — done in v0.3.25)

## M2 — Shareable v1.0 (~78% done)

Indie dev should install + understand in 5 min.

- [x] CHANGELOG.md
- [x] CI (pytest + shellcheck + version-sync)
- [x] `/dodojo:init` wizard with sensible defaults
- [x] `docs/positioning.md` — vs caveman, vs claude-mem
- [x] `docs/sensei.md` — opt-in rationale + setup + roadmap
- [x] `docs/quickstart.md` — install → first ROI rec in 5 min
- [x] Demo screencast / asciinema (docs/demo.cast + docs/demo.md)
- [x] Honest metrics (removed false token savings claim, added reuse tracking)
- [x] Context optimization (cap injection to top 2, save 60% tokens)
- [ ] At least 3 external users dogfooding
- [ ] Issue templates + contribution guide

## M3 — Mature ecosystem (~10% done)

Beyond single-author. Optional.

- [ ] Per-shell history adapters (bash, fish)
- [ ] Built-in cron registration (`/sensei cron-install`)
- [ ] Web dashboard for Sensei accept/reject
- [ ] Cross-machine sync via dotfiles
- [ ] Plugin marketplace listing on official Claude Code registry
- [ ] First external contributor PR merged

---

## Status snapshot (2026-05-04)

| Milestone | Done | Total | % |
|-----------|------|-------|---|
| M1 — Feature complete | 6 | 7 | **86%** |
| M2 — Shareable v1.0 | 9 | 11 | **82%** |
| M3 — Mature ecosystem | 0 | 6 | **0%** |
| **Overall to v1.0 (M1+M2)** | 15 | 18 | **83%** |

**M2 ready to ship.** Remaining: 3 external users + contrib guide (can happen post-launch).

Updated when items toggle. Maintain alongside CHANGELOG.
