# Phase 4 — Maintenance Infrastructure (in progress)

Automatic archival of stale memories. Prevents unbounded growth as memory count scales.

---

## Problem

After Phase 5 (smart categorization), memory system becomes highly effective. Users accumulate memories over months/years:
- 36 memories → 100+ → 500+ → search becomes slow again
- Dead memories clutter rankings (low reuse but still scored)
- No feedback loop: unused memories never removed

**Solution:** Auto-archive stale + unused memories. Reversible (archived in manifest).

---

## What's done

### Infrastructure
- ✅ `scripts/archive-stale-memories.py` — stale detection + archival
  - Finds: unused 6mo+ OR never reused after 30 days
  - Moves files to `~/.claude/memory/_archive/<category>/`
  - Logs manifest for recovery: `~/.claude/memory/_archive/manifest.jsonl`
  - Dry-run by default; `--commit` executes

### Integration points (Phase 4b+)
- [ ] Sensei weekly recommendations (surface memories eligible for archive)
- [ ] SessionStart hook option (ask user before archiving on threshold)
- [ ] Auto-run on Phase 5c metadata updates (detect newly-stale automatically)

---

## Usage

### Manual archive (safe)

```bash
# Dry-run: see what would be archived
python3 scripts/archive-stale-memories.py

# Commit: actually archive
python3 scripts/archive-stale-memories.py --commit
```

### Restore from archive

```bash
# Find archived file
grep "filename.md" ~/.claude/memory/_archive/manifest.jsonl

# Move back to original category
mv ~/.claude/memory/_archive/category/filename.md ~/.claude/memory/category/
```

---

## Stale thresholds

| Condition | Action | Days |
|-----------|--------|------|
| Unused | Archive if `last_used > 180d ago` | 6 mo |
| Never reused | Archive if `reuses=0 AND created>30d ago` | 30 d |

Conservative defaults (favor keeping over archiving). Can tighten:
- `STALE_MONTHS=3` — aggressive cleanup
- `NEVER_REUSED_DAYS=14` — archive experimental memories faster

---

## Impact

**Current state (36 memories, all recently created):**
- Archive rate: ~0% (everything is new + used)
- Search space: 8 category files (fixed by Phase 5a)

**Projected (500+ memories at scale):**
- Archive rate: ~20-40% (memories naturally decay with age)
- Cleanup: removes ~100 stale memories/year
- Search speed: constant (still 8 files per category, dead ones removed)

---

## Timeline

- **Phase 4a** (archive infrastructure): ✅ Done (this doc)
- **Phase 4b** (Sensei integration): 1 hour
- **Phase 4c** (SessionStart automation): 1 hour

**Total: ~2 hours for full automation.**

---

## Related

- Phase 5: Smart categorization (provides reuse tracking data)
- Phase 2: Memory compression (orthogonal: per-memory optimization)
- Sensei: Pattern mining + ROI advice (can surface archive candidates)

---

## Known limitations

- Manifest-only: no automatic restore (user decision)
- Archive threshold static: no per-memory decay rates (future: per-category thresholds)
- No expiry field support yet (Phase 5: already in metadata, not used by archive)

---

## Go/no-go

**Ready for Phase 4b (Sensei integration)?**

- [ ] **Yes**: Integrate weekly recommendations
- [ ] **No**: Wait (Phase 4a archive script sufficient for now)
