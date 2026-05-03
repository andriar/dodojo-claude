---
name: lookup → trivial
description: File location, symbol search, fact retrieval
type: routing
pattern: \b(where is|find (the|file|function)|locate|grep|show me (the|file)|what does .* do|list (all|files))\b
verdict: trivial
why: Pure search — Explore subagent + haiku is faster + cheaper than main thread reasoning.
---

Suggest spawning `Agent(subagent_type=Explore, model=haiku)` instead of main-thread search.
