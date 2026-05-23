---
description: Archive orphan memory files (zero matches in smart-context telemetry)
---

# /dodojo:prune

Invoke the `archive-orphans` skill (dry-run by default). Moves orphan memory files (zero matches in smart-context telemetry) to `~/.claude/memory/_archive/` and prunes the INDEX.md row.

Pass `--apply` to actually move; otherwise reports candidates only. Refuses to apply if telemetry below threshold.
