# Phase 5 — Smart Categorization (in progress)

Upgrade memory system from flat to smart: IDs + categories + intelligent ranking.

---

## What's done

### Infrastructure
- ✅ `lib/memory_categorizer.py` — core functions
  - `generate_memory_id()` — unique ID generation
  - `auto_detect_category()` — domain keyword matching + confidence
  - `rank_memories()` — multi-factor ranking
  - `ensure_memory_has_metadata()` — auto-populate metadata

- ✅ `scripts/migrate-memories-to-v2.py` — migration tool
  - Categorizes 36 existing memories (dry-run: shows plan)
  - Adds ID + metadata to all files
  - Moves files to category subdirs

### Metadata format
```yaml
---
id: mem_2026_05_04_001
name: React hook cleanup
description: useEffect cleanup prevents memory leaks
category: frontend
tags: [react, performance, hooks]
created: 2026-05-04
reuses: 0
last_used: null
expires: null
category_confidence: 0.85
---
```

---

## What's next

### Phase 5a: Integrate with smart-context.py
- [ ] Update smart-context to import `memory_categorizer`
- [ ] Classify prompt domain (0 tokens)
- [ ] Search only relevant category directory
- [ ] Score using `rank_memories()` (reuse + recency + cwd)
- [ ] Inject top 2 from that category (was top 5 from all)

**Impact:** 85% smaller search space + smarter ranking.

### Phase 5b: Auto-update memory metadata on session end
- [ ] Track when memories are injected (already in session logs)
- [ ] Update `reuses` count when memory is used
- [ ] Update `last_used` timestamp
- [ ] Detect and flag expired memories

**Impact:** Real reuse stats, automatic expiry.

### Phase 5c: Migration + cleanup
- [ ] Run `scripts/migrate-memories-to-v2.py --commit`
- [ ] Archive memories that are >6 months old + never reused
- [ ] Verify all memories have valid `category`
- [ ] Test categorized smart-context search

**Impact:** Clean slate, better ranking.

---

## Architecture

```
Memory system (before):
  ~/.claude/memory/
    ├─ bug_fix.md (plain text, no structure)
    ├─ api_spec.md
    └─ INDEX.md

Memory system (after):
  ~/.claude/memory/
    ├─ INDEX.md (pointers only)
    ├─ frontend/
    │  └─ react_patterns.md (ID + metadata)
    ├─ backend/
    │  └─ auth_flows.md
    ├─ devops/
    │  └─ docker_tips.md
    ├─ patterns/
    │  └─ error_recovery.md
    ├─ setup/
    │  └─ dev_environment.md
    └─ general/
       └─ miscellaneous.md

Smart-context search (before):
  1. Collect all 36 memories
  2. Score against prompt (slow, high token cost)
  3. Inject top 5 (noisy)

Smart-context search (after):
  1. Classify prompt domain ("React component fix" → frontend)
  2. Collect only frontend/ memories (~8 files)
  3. Score those + cross-repo memories (~2 files)
  4. Rank by relevance + reuse + recency + cwd
  5. Inject top 2 (signal > noise)
```

---

## Domains (auto-detect keywords)

| Domain | Keywords | Example memories |
|--------|----------|------------------|
| **frontend** | react, vue, css, component, ui, hooks, tailwind | react_patterns, css_tricks, form_validation |
| **backend** | api, auth, database, sql, orm, model, endpoint | auth_flows, db_optimization, api_versioning |
| **devops** | docker, k8s, ci, deploy, terraform, ansible | docker_tips, k8s_patterns, ci_workflows |
| **infra** | aws, gcp, azure, networking, security, terraform | vpc_setup, security_checklist, dns_config |
| **patterns** | decision, lesson, pattern, insight | error_recovery_loop, testing_strategy |
| **setup** | setup, config, install, environment | dev_environment, docker_local_setup |
| **general** | fallback (catch-all) | misc, uncategorized |

---

## Migration checklist

```bash
# 1. Verify dry-run
python3 scripts/migrate-memories-to-v2.py
# Should show: "36 memories to migrate" → categories

# 2. Commit migration
python3 scripts/migrate-memories-to-v2.py --commit

# 3. Verify structure
find ~/.claude/memory -type f -name "*.md" | head -20

# 4. Check metadata
grep "^id:" ~/.claude/memory/frontend/*.md | wc -l
# Should show: number of IDs added

# 5. Test smart-context
# (after Phase 5a integration)
```

---

## Performance impact

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Search space | 36 files | ~8 files | 78% |
| Scoring ops | 36 × 2 | 8 × 2 | 78% |
| Ranking factors | keyword only | keyword + 4 factors | ← smarter |
| Injected | top 5 (noisy) | top 2 (signal) | ← better |

---

## Known limitations

- Auto-detect not perfect (some memories misclassified)
- Manual review recommended first run
- Multi-domain memories only get 1 category (use `tags` for cross-domain)
- Category names hardcoded (can add custom categories later)

---

## Timeline

- **Phase 5a** (integrate smart-context): 2 hours
- **Phase 5b** (auto-update metadata): 1 hour
- **Phase 5c** (migrate + verify): 30 min

**Total: ~3.5 hours for full smart categorization.**

Can run in parallel with other optimizations (Phase 2, 4).

---

## Related

- Phase 4: Maintenance infrastructure (prevents orphans)
- Phase 2: Memory compression (compresses per-memory)
- M2: Honest metrics (foundation for this phase)
