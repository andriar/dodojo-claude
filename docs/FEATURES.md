# DoDojo Features — Complete Reference

> What DoDojo does + how to use each feature

## Quick Navigation

| Feature | Purpose | When to use |
|---------|---------|------------|
| [**Mirror (Memory)**](#mirror-memory) | Capture + recall lessons | Building institutional knowledge |
| [**Sensei Phase 2**](#sensei-phase-2-workflow-optimization) | Detect friction + suggest fixes | Optimizing your workflow |
| [**Smart Tips (Q3)**](#smart-tips-q3) | Daily actionable tips | Learning DoDojo features |
| [**Orphan Detection (Q4)**](#orphan-detection-q4) | Clean stale memories | Maintaining memory health |
| [**Smart Context (Phase 5)**](#smart-context-phase-5) | Inject relevant memories | Reusing knowledge automatically |
| [**Categorized Memory (Phase 5c)**](#categorized-memory-phase-5c) | Organize + search faster | Structuring knowledge by domain |
| [**Auto-Archival (Phase 4)**](#auto-archival-phase-4) | Cleanup stale files | Keeping system lean |

---

## Mirror (Memory)

**What:** Persistent note-taking system across sessions. Memories survive between prompts.

**How to use:**
```bash
# Create memory
/dodojo:init  # Setup wizard

# Search memory
/dodojo:recall "pattern to find"

# View health
/dodojo:status
```

**Files:** `~/.claude/memory/` (user owns, can edit directly)

**Features:**
- Categorized by domain (frontend, backend, devops, etc)
- Metadata tracked (reuses, last_used, tags)
- Smart searchable via `/dodojo:recall`
- Auto-archives stale memories (Phase 4)

**When to create:**
- Lessons learned ("Docker multi-stage builds reduce size by X%")
- Patterns discovered ("This codebase uses snake_case for variables")
- Decisions made ("Use React hooks, not class components")
- Recurring fixes ("Django ORM query optimization: use select_related()")

---

## Sensei Phase 2: Workflow Optimization

**What:** Detects friction patterns in your work → shows recommendations.

**How to use:**
```bash
# Auto (shows in greeter each session)
# Greeter displays: "🔴 SENSEI: Follow-up chains taking 3 prompts..."

# Manual (full report)
python3 ~/.claude/scripts/sensei-report
```

**Patterns detected:**
1. **Repeated file reads** — same file read 4+ times → suggest memory file
2. **Follow-up chains** — prompt needs 3+ clarifications → suggest template
3. **Tool misuse** — using expensive tool → suggest cheaper alternative
4. **Memory gaps** — asking same Q twice → save to memory
5. **Token waste** — large input → small output → narrow context

**Features:**
- Tracks adoption (mark recommendation as done)
- Estimates token savings
- Learns from your feedback (ratings)

**When to use:**
- Every session (greeter shows 1 tip automatically)
- Weekly deep-dive (`/sensei-report` for all patterns)

---

## Smart Tips (Q3)

**What:** Daily actionable tip that adapts to what you're doing.

**How to use:**
```bash
# Auto (shows in greeter, deterministic daily)
# Greeter shows: "💡 Use /simplify for code reviews. [👍 helpful] [👎 not helpful]"

# Rate tip
Click [👍 helpful] or [👎 not helpful]

# See all tips
cat ~/.claude/scripts/tips.json
```

**Features:**
- 25+ tips across 6 categories (code-review, search, memory, workflow, sensei, general)
- Context-aware (detects activity type)
- Sensei-driven (shows pattern-specific tips when issues detected)
- Learns from feedback (helpful tips boosted, unhelpful reduced)
- Deterministic daily selection (same tip per user per day)

**When to use:**
- Daily (part of greeter)
- Mark helpful/unhelpful to improve future recommendations

---

## Orphan Detection (Q4)

**What:** Finds stale memories, suggests cleanup.

**How to use:**
```bash
# Show health report
python3 ~/.claude/scripts/orphan-detector.py

# Dry-run (what would be archived?)
python3 ~/.claude/scripts/orphan-detector.py --archive

# Actually archive (reversible)
python3 ~/.claude/scripts/orphan-detector.py --archive --commit
```

**Scoring algorithm:**
- Reuses (40%): used more → active
- Recency (40%): used recently → active  
- Size (20%): larger files slightly penalized
- Result: score 0.0 (orphan) to 1.0 (active)

**Categories:**
- **Active** (>0.7): Use regularly
- **Dormant** (0.3-0.7): Used before, not recently
- **Orphan** (≤0.3): Unused or very old

**Features:**
- Smart scoring (combines signals)
- High-confidence only (won't delete memories with uncertain status)
- Reversible (archived to `_archive/`, manifest tracks all)

**When to use:**
- Monthly (review report)
- When system feels slow (archive orphans)

---

## Smart Context (Phase 5)

**What:** Auto-injects relevant memories into prompts.

**How to use:**
```bash
# Automatic (no action needed)
# Smart-context hook runs on each prompt, injects top 2 matching memories

# Force manual injection
/dodojo:recall "search term"
```

**Features:**
- Categorized search (only searches relevant domain)
- Ranked by reuse + recency + current working directory
- Caps at 2 results (saves 60% tokens)
- Hit/miss tracked (Sensei learns what works)

**When to use:**
- Automatic (always on)
- Manual when you want explicit memory search

---

## Categorized Memory (Phase 5c)

**What:** Memory files organized by domain with metadata.

**Structure:**
```
~/.claude/memory/
├── frontend/
│   ├── react-hooks.md
│   └── css-patterns.md
├── backend/
│   ├── database.md
│   └── api-design.md
├── devops/
│   ├── docker.md
│   └── ci-cd.md
└── patterns/
    ├── error-handling.md
    └── logging.md
```

**Metadata in each file:**
```yaml
---
name: React Hooks Patterns
description: Common hooks usage + gotchas
type: reference
category: frontend
created: 2026-04-01
reuses: 12
last_used: 2026-05-05
tags: [react, frontend, hooks]
---
```

**When to use:**
- Create memories in proper category (improves smart-context search)
- Add tags for cross-domain memories
- Let system track reuses automatically

---

## Auto-Archival (Phase 4)

**What:** Automatically moves unused memories to archive.

**How to use:**
```bash
# Check what would be archived
python3 ~/.claude/scripts/orphan-detector.py

# Archive (reversible)
python3 ~/.claude/scripts/orphan-detector.py --archive --commit

# Restore from archive
mv ~/.claude/memory/_archive/filename.md ~/.claude/memory/
```

**Features:**
- High-confidence only (95%+ certain before archiving)
- Reversible (manifest tracks all moves)
- Scheduled (can run weekly via /schedule)

**When to use:**
- Monthly cleanup
- When memory directory feels slow

---

## Integration Matrix

How features work together:

```
Your work
    ↓
Session start
    ├─→ Mirror: Load memories
    ├─→ Sensei: Analyze patterns
    ├─→ Smart Tips: Show daily tip
    └─→ Smart Context: Inject relevant memories
    
Your prompt
    ↓
Smart Context
    ├─→ Categorized search (by domain)
    ├─→ Ranked by reuse/recency
    └─→ Inject top 2 memories
    
Session end
    ↓
Auto-Archival (weekly)
    └─→ Find orphans via Q4 scoring
        └─→ Archive high-confidence
    
Feedback
    ↓
Sensei
    ├─→ Track patterns
    ├─→ Suggest optimizations
    └─→ Learn from adoption (lain kali)
```

---

## Command Reference

| Command | What it does |
|---------|------------|
| `/dodojo:init` | Setup wizard |
| `/dodojo:status` | System health |
| `/dodojo:recall "X"` | Search memories |
| `/dodojo:health` | Smoke-test hooks |
| `/dodojo:sensei` | Show Sensei report |
| `python3 ~/.claude/scripts/sensei-report` | Full Sensei analysis |
| `python3 ~/.claude/scripts/tips-selector.py` | Show daily tip |
| `python3 ~/.claude/scripts/orphan-detector.py` | Memory health |

---

## Next Steps

1. **New user:** Read [mental-model.md](guides/mental-model.md)
2. **Get started:** [quickstart.md](quickstart.md)
3. **Learn features:** This page
4. **Stuck?** [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
5. **Understand architecture:** [architecture/phases.md](architecture/phases.md)
