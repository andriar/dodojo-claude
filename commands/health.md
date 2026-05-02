---
description: Smoke-test all hooks registered in settings.json
---

# /dodojo:health

Invoke the `hook-health` skill. Verifies every hook registered in `~/.claude/settings.json`:
- file exists
- is executable
- exits cleanly with sample stdin
- is not stale

Run after editing settings.json or adding new hooks.
