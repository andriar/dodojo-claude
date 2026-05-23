---
name: DoDojo design priorities
description: Priority order for features — Smart > Light > Optimized > Efficient
type: project
---

## Priority order (top to bottom)

1. **SMART** — Intelligent, capable, correct. Works in edge cases. Mines real patterns. Makes good decisions.
2. **LIGHT** — Fewer tokens, smaller footprint. But not at cost of intelligence.
3. **OPTIMIZED** — Fast matching, quick responses. But not sacrificing accuracy.
4. **EFFICIENT** — Resource usage, disk space, network calls. Nice-to-have, not primary.

## Why this matters

- A smart feature that costs 2K tokens > dumb feature that costs 500 tokens
- Better to inject 3 relevant memories (3K tokens) than 1 irrelevant (500 tokens)
- Categorization adds complexity, but worth it if it catches real patterns

## Application to current work

**Categorize smart-context:**
- ✅ Add ID references to memories (smart)
- ✅ Auto-detect categories, suggest new ones (smart)
- ✅ Search only relevant categories (light + optimized)
- ⚠️ Don't over-optimize at cost of accuracy

**Greeter redesign:**
- ✅ Show meaningful summaries (smart)
- ✅ Reduce tokens (light)
- ⚠️ Not "just show nothing" (that's not smart)

**Memory compression:**
- ✅ Compress memories (light)
- ⚠️ But only if compression doesn't lose nuance (smart)
