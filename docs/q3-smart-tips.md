# Q3: Smart Tips System (Context-Aware + Sensei-Driven + Feedback)

> Expand from 9 hardcoded tips → adaptive system that learns from user + context + Sensei patterns

## Architecture

### Tier 1: Tip Pool (Expanded + Categorized)

**Categories:**
- `code-review` — /simplify, caveman-review, etc (triggered by review prompts)
- `search` — /smart-explore, /dodojo:recall, grep patterns (triggered by searches)
- `memory` — /dodojo:recall, create memory, save patterns (triggered by repeated reads)
- `workflow` — /loop, /schedule, batch operations (triggered by repetitive patterns)
- `sensei` — optimization-specific (triggered by Sensei pattern detection)
- `general` — skill discovery, project setup, help (always available)

**Tip Count:** 40-50 tips (vs 9 current)

**Data Structure:**
```json
{
  "id": "tip_001",
  "text": "Use /simplify for terse code reviews. Saves tokens + time.",
  "link": "/simplify",
  "category": "code-review",
  "keywords": ["review", "code", "simplify"],
  "helpfulness": 0.8,  // User feedback: 1.0=loved, 0.5=neutral, 0.1=unhelpful
  "times_shown": 5,
  "times_helpful": 4
}
```

### Tier 2: Context Detection

**Triggers:**
```python
if "review" in prompt or "check" in prompt:
  category = "code-review"
  
if "find" in prompt or "search" in prompt or "grep" in prompt:
  category = "search"
  
if file_reads > 2 and memory_gaps detected:
  category = "memory"
  
if sensei_pattern == "repeated-reads":
  category = "sensei"
  
# etc.
```

**Selection Algorithm:**
```python
1. Filter tips by detected category
2. Exclude recently_shown (avoid repetition)
3. Weight by user_feedback (helpfulness score)
4. Pick highest-scoring tip
```

### Tier 3: Sensei Integration

**Direct Pattern → Tip Mapping:**

| Sensei Pattern | Tip Category | Example Tip |
|---|---|---|
| `repeated-file-reads` | `memory` | "File read 4×? Try `/dodojo:recall` next time" |
| `follow-up-chain` | `workflow` | "3 clarifications per task? Use prompt template [link]" |
| `tool-misuse` | `search` | "Searching files? Use `grep` not Read tool" |
| `memory-gap` | `memory` | "Asked X before? Save answer to memory" |
| `token-waste` | `workflow` | "5000 tokens input → 300 output? Narrow context first" |

**Display:**
```
Instead of:
  💡 TIP: Use /simplify for code reviews

Show:
  🔴 SENSEI TIP: Your file was read 4× this week
     → Try /dodojo:recall next time (save 285 tokens/week)
```

### Tier 4: Feedback Loop

**Tracking:**
```json
{
  "timestamp": "2026-05-05T10:00:00Z",
  "tip_id": "tip_001",
  "shown": true,
  "rating": "👍",  // null = not rated, "👍" = helpful, "👎" = not helpful
  "context": "code-review"
}
```

**Storage:** `~/.claude/dodojo/tips-feedback.jsonl`

**Learning:**
```python
# After each rating
helpful_rate = tip.times_helpful / tip.times_shown

# Weight future selection
if helpful_rate > 0.7:
  weight *= 1.5  # Boost helpful tips
elif helpful_rate < 0.3:
  weight *= 0.5  # Reduce unhelpful tips
```

**Display Feedback Prompt:**
```
💡 TIP: Use /simplify for code reviews. [👍 helpful] [👎 not helpful]
```

---

## Implementation Plan

### Phase 1: Expand Tip Pool + Categorization
- [ ] Create `tips.json` with 40-50 tips (4 categories)
- [ ] Tip selection by category (simple deterministic)
- [ ] Load tips from file instead of hardcode

### Phase 2: Context Detection
- [ ] Add context detection logic to greeter hook
- [ ] Map prompt/activity → category
- [ ] Filter tip pool by category
- [ ] Weight by helpfulness (start with all 0.5)

### Phase 3: Sensei Integration
- [ ] Read Sensei pattern from analysis.json
- [ ] Map pattern → sensei tip
- [ ] Override normal tip if pattern detected
- [ ] Show "SENSEI TIP" variant

### Phase 4: Feedback Loop
- [ ] Add `[👍 helpful] [👎 not helpful]` buttons to tip display
- [ ] Track clicks in tips-feedback.jsonl
- [ ] Update tip.helpfulness scores
- [ ] Weight selection by feedback

---

## Example Flow

### Day 1 (no data)
```
User starts session
→ Context: general (no specific trigger)
→ Pick: random general tip
→ Show: "💡 TIP: Use /simplify for code reviews. [👍] [👎]"
→ User clicks 👍
→ Save: tip_001 rating=helpful
```

### Day 2 (context detection)
```
User starts session, searches for code
→ Context: "search" detected
→ Pick: search category tip (helpful_rate > 0.5)
→ Show: "💡 TIP: /smart-explore indexes codebase, faster than grep. [👍] [👎]"
```

### Day 3 (Sensei pattern)
```
User starts session
→ Sensei detects: "repeated-file-reads: docs/routing.md 5×"
→ Override: show Sensei tip instead
→ Show: "🔴 SENSEI TIP: docs/routing.md read 5× this week
          → Create memory file, use /dodojo:recall. [👍] [👎]"
```

### Day 10 (feedback weighted)
```
User has clicked 👍 on memory tips 6x, 👎 on workflow tips 2x
→ Context: memory detected
→ Weight: memory tips boosted 1.5×, workflow tips reduced 0.5×
→ Pick: highly-weighted memory tip
→ Show: "💡 TIP: /dodojo:recall finds reusable patterns fast. [👍] [👎]"
```

---

## Files to Create/Modify

**New:**
- `tips.json` (40-50 tips with metadata)
- `scripts/tips-selector.py` (context detection + selection)
- `scripts/tips-feedback.py` (track ratings, update weights)

**Modify:**
- `hooks/dodojo-greet.sh` (call tips-selector instead of hardcode)
- `docs/q3-tips-guide.md` (user guide)

---

## Success Metrics

✅ Tips expand from 9 → 40+
✅ System adapts to user feedback (helpful tips shown more)
✅ Sensei patterns directly surface relevant tips
✅ User finds tips more useful (target: 70%+ helpful rating)
✅ Tips reduce friction (shorter learning curve for new features)
