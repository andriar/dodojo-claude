# DoDojo Phases: From M0 to M2+

> Evolution of DoDojo from basic memory to complete workflow optimization

## Overview

```
M0: Memory basics
  └─ Phase 1: Session memory capture
  └─ Phase 2: Auto-archival infrastructure
  └─ Phase 3: Smart context by category (advanced)

M1: Sensei workflow coach
  └─ Phase 4: Memory maintenance
  └─ Phase 5: Smart categorization
  └─ Sensei: Pattern detection + recommendations

M2: Complete system (shipped)
  └─ Phase 5c: Categorized memory v2
  └─ Sensei Phase 2: Workflow optimization
  └─ Q3: Smart tips system
  └─ Q4: Orphan detection + auto-archive

M3+: Expansion (lain kali)
  └─ Phase 2b: Memory compression
  └─ Sensei Phase 3: Git + Slack integration
  └─ Smart Tips v2: User-defined tip categories
```

---

## Phase 1: Session Memory Capture

**Goal:** Persist knowledge across sessions

**What it does:**
- User creates `.md` files in `~/.claude/memory/`
- Files auto-inject into Claude's context
- Memories survive between prompts

**Files:**
- `~/.claude/memory/` — user's notes
- `/dodojo:recall` — manual search

**Shipped in:** v0.1

---

## Phase 2: Auto-Archival Infrastructure

**Goal:** Prevent unbounded memory growth

**What it does:**
- Tracks when memories are created + last used
- Marks dormant memories (unused >30 days)
- Optional auto-archive to prevent bloat

**Files:**
- Archive manifest: `_archive/manifest.json`
- Scripts: `archive-stale-memories.py`

**Shipped in:** v0.3.24

---

## Phase 3: Smart Context by Category

**Goal:** Search only relevant domain (not all 100 memories)

**What it does:**
- Memories organized by category (frontend, backend, devops, etc)
- Searches filter by current context
- Result: 85% smaller search space

**Status:** Planned (M3+)

---

## Phase 4: Memory Maintenance

**Goal:** Integrate archival into workflow, add monitoring

**What it does:**
- Sensei detects stale memories
- User gets weekly recommendations
- Auto-archive with reversible manifest

**Files:**
- `orphan-detector.py` — Q4 answer
- `archive-manifest.json` — tracks restores

**Shipped in:** v0.3.26 (M2)

---

## Phase 5: Smart Categorization

**Goal:** Organize memories for intelligent search + ranking

**What it does:**
- Auto-detect category on save (frontend vs backend vs devops)
- Add metadata: reuses, last_used, tags
- Rank by: reuse frequency + recency + cwd match

**Status:**
- Phase 5a: Categorized search ✅ (v0.3.26)
- Phase 5b: Auto-update metadata ✅ (v0.3.26)
- Phase 5c: Categorized v2 structure ✅ (v0.3.27, M2)

**Files:**
- `memory_categorizer.py` — auto-detection
- Memory metadata: `id`, `category`, `created`, `reuses`, `last_used`, `tags`

---

## Phase 5c: Categorized Memory v2

**Goal:** Production-ready memory system with metadata

**What it does:**
- Memories in subdirectories by category
- Each has frontmatter: name, description, type, category, etc
- Smart search knows domain
- Ranking considers all signals

**Shipped in:** v0.3.27 (M2)

**Example:**
```yaml
---
name: React Hooks Patterns
description: Common hooks usage + gotchas
type: reference
category: frontend
created: 2026-04-01
reuses: 12
last_used: 2026-05-05
tags: [react, hooks]
---
```

---

## Sensei: Workflow Coach

**Goal:** Detect friction → suggest optimizations

**What it does:**
- Mines work patterns (git, shell, Claude sessions)
- Detects 5 friction types (repeated reads, follow-ups, tool misuse, etc)
- Shows weekly recommendations

**Shipped in:** v0.3.25

---

## Sensei Phase 2: Workflow Optimization

**Goal:** Telemetry-driven optimization with adoption tracking

**What it does:**
- Captures session telemetry (prompts, tokens, tools)
- Analyzes patterns (what's slowing you down)
- Shows greeter tip + full report
- Tracks adoption (did you fix it?)

**Files:**
- `sensei-analyzer.py` — pattern detection
- `sensei-summary.py` — display formatting
- `telemetry.jsonl` — session data

**Shipped in:** v0.3.27 (M2)

---

## Q3: Smart Tips System

**Goal:** Daily actionable tips that adapt to what you're doing

**What it does:**
- 25+ tips categorized (code-review, search, memory, etc)
- Context-aware (detects activity)
- Sensei-driven (shows pattern-specific tips)
- Learns from feedback (helpful tips boosted)

**Files:**
- `tips.json` — tip database
- `tips-selector.py` — context + feedback weighting
- `tips-feedback.jsonl` — user ratings

**Shipped in:** v0.3.28 (Q3 + M2)

---

## Q4: Orphan Detection + Auto-Archive

**Goal:** Intelligently archive stale memories (reversible)

**What it does:**
- Scores memories (reuses × recency × size)
- Categorizes: active / dormant / orphan
- Auto-archives high-confidence orphans
- Reversible (manifest tracks all moves)

**Files:**
- `orphan-detector.py` — detection engine
- `archive-manifest.json` — tracks moves

**Shipped in:** v0.3.28 (Q4 + M2)

---

## M2 Milestone: Complete

**Shipped features:**
- ✅ Smart categorized memory (Phase 5c)
- ✅ Context optimization (Phase 5)
- ✅ Auto-archival (Phase 4)
- ✅ Sensei Phase 2 (workflow optimizer)
- ✅ Smart Tips (Q3)
- ✅ Orphan Detection (Q4)
- ✅ Complete documentation

**Status:** Ready for external dogfooding

---

## M3+ Roadmap (lain kali)

### Phase 2b: Memory Compression

Compress old memories to reduce token injection:
- One-time: compress on save → saves 150 tokens per memory
- Per-use: inject compressed version (2K → 400 tokens)
- Impact: 78% per-reuse token savings

### Sensei Phase 3: Git + Slack Integration

Expand pattern detection to:
- Git: commit quality (missing tests, unclear messages)
- Slack: blockers (waiting on X 10× per week)
- Output: cross-functional recommendations (not just code)

### Smart Tips v2: User Templates

Let users define custom tips:
- Create `.tip` files in memory
- System suggests when pattern detected
- Example: "Add test case when class created"

---

## Feature Matrix

| Feature | Phase | Shipped | Status |
|---------|-------|---------|--------|
| Memory capture | 1 | v0.1 | ✅ Stable |
| Auto-archive | 2 | v0.3.24 | ✅ Stable |
| Categorized search | 3 | TBD | 📋 Planned |
| Maintenance infra | 4 | v0.3.26 | ✅ Stable |
| Smart categorization | 5 | v0.3.27 | ✅ Stable |
| Sensei workflow coach | — | v0.3.25 | ✅ Stable |
| Sensei Phase 2 | — | v0.3.27 | ✅ Stable |
| Smart Tips | Q3 | v0.3.28 | ✅ Stable |
| Orphan Detection | Q4 | v0.3.28 | ✅ Stable |
| Memory compression | 2b | TBD | 📋 Planned |
| Git + Slack mining | 3 | TBD | 📋 Planned |

---

## How to Read This

- **Using DoDojo?** Start with [mental-model.md](mental-model.md)
- **Want to know what's shipped?** See M2 Milestone above
- **Curious about future?** See M3+ Roadmap
- **Understanding architecture?** This page is it
