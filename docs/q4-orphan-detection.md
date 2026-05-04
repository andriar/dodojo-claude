# Q4: Smart Orphan Detection + Auto-Archive

> Mine existing metadata (reuses, last_used, size) to categorize memories + intelligently archive stale ones

## Problem

Current orphan detection (Phase 4):
- Only counts smart-context matches (7 days)
- Misses "active but not matching" memories
- Binary: orphan or not (no spectrum)
- No scoring (all orphans treated equally)

## Solution: A + B + D

### A: Smart Orphan Scoring

**Combines 3 signals from existing metadata:**

```python
score = (reuses_weight × 0.4) + (recency_weight × 0.4) + (size_penalty × 0.2)

reuses_weight = min(reuses / 5, 1.0)      # 5+ reuses = max score
recency_weight = 1.0 - (days_since_used / 365)  # 1 year = 0 score
size_penalty = 1.0 if size < 50KB else 0.8  # Large files penalized

orphan_score = score  # 0.0 = definite orphan, 1.0 = active
```

**Interpretation:**
- `score > 0.7` = Active (use regularly)
- `0.3 < score <= 0.7` = Dormant (used before, not recently)
- `score <= 0.3` = Orphan (unused or very old)

### B: Orphan → Dormant → Active Spectrum

**Clear categories based on score:**

```json
{
  "file": "old-feature.md",
  "score": 0.15,
  "category": "orphan",
  "reuses": 0,
  "last_used": "2025-09-04",
  "size_kb": 3,
  "reason": "0 reuses + 240 days old"
}
```

vs

```json
{
  "file": "routing-config.md",
  "score": 0.8,
  "category": "active",
  "reuses": 12,
  "last_used": "2026-05-05",
  "size_kb": 2,
  "reason": "12 reuses + recently used"
}
```

### C: Auto-Archive with Confidence

**Confidence-based decisions (NOT blind deletion):**

```python
if score <= 0.2 AND reuses == 0 AND days_old > 60:
  confidence = 95%
  action = "auto-archive"  # Safe: never used
  
elif score <= 0.3 AND days_old > 90:
  confidence = 80%
  action = "auto-archive"  # Safe: old + unused long time
  
elif 0.3 < score <= 0.5 AND days_old > 60:
  confidence = 50%
  action = "flag for review"  # Uncertain: don't auto-archive
  
else:
  action = "keep"
```

**Archive = reversible:**
- Move to `~/.claude/memory/_archive/`
- Keep manifest: `archive-manifest.json`
- Users can restore anytime

## Implementation

### File: `scripts/orphan-detector.py`

```
Input:  Memory directory + metadata
Process: Score each file, categorize, detect orphans
Output: Report + auto-archive decisions
```

**Functions:**
- `load_memory_metadata()` — read all memory files + metadata
- `calculate_score()` — A: smart scoring formula
- `categorize()` — B: active/dormant/orphan spectrum
- `detect_orphans()` — find high-confidence candidates
- `archive_memory()` — move + manifest
- `show_report()` — display health + candidates

### File: `hooks/orphan-monitor.sh`

Runs weekly (via cron or /schedule):
- Detect orphans
- Auto-archive high-confidence (>90%)
- Flag medium-confidence (50-90%) for review
- Show summary

## Example Output

```
📊 MEMORY HEALTH REPORT
═══════════════════════════════════════════

Total files:      127
Active (>0.7):     89 (70%)
Dormant (0.3-0.7): 28 (22%)
Orphan (≤0.3):     10 (8%)

AUTO-ARCHIVED (95%+ confidence): 3 files
├─ old-experiment.md (0 reuses, 240d old, 2KB)
├─ temp-notes-2024.md (0 reuses, 180d old, 1KB)
└─ deprecated-flow.md (1 reuse, 200d old, 3KB)

REVIEW CANDIDATES (50-80% confidence): 5 files
├─ architecture-v1.md (2 reuses, 120d old, 5KB)
├─ old-project.md (1 reuse, 150d old, 4KB)
├─ scratch.md (0 reuses, 90d old, 6KB)
└─ ...

KEEP (active): 119 files
├─ routing-config.md (12 reuses, 1d old, 2KB)
├─ claude-mem-setup.md (8 reuses, 3d old, 1KB)
└─ ...

💾 ARCHIVE STATUS
Restored: 5 files (from 30 total archived)
Manifest: ~/.claude/memory/_archive/manifest.json
```

## Safety

✅ Never auto-archives score > 0.5
✅ Requires high confidence (95%+)
✅ Reversible (manifest tracks everything)
✅ User can whitelist files (never archive)
✅ Dry-run mode (show what would archive)

## Files

- `scripts/orphan-detector.py` — detector engine
- `hooks/orphan-monitor.sh` — weekly monitor hook
- `docs/q4-orphan-detection.md` — this guide
- `tests/test_q4_orphan.py` — unit tests

## Future Extensions (lain kali)

- Monitor claude-mem size (alert only)
- Compression for dormant memories (Phase 2 extended)
- User whitelist/exclude patterns
- Dashboard: memory health timeline
