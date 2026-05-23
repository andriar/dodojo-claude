---
description: Audit Claude Code context budget — token load, bloated files, orphan memories
---

# /dodojo:audit-memory

Invoke the `audit-context` skill. Measures session token load (CLAUDE.md + @-refs + project MEMORY.md), flags bloated files, cross-references smart-context telemetry to surface orphan memories never matched.

Use when session feels heavy/slow or before pruning memory.

For the **plugin stack** auditor (per-plugin token cost, prune candidates), see `/dodojo:audit`.
