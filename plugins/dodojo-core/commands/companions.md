---
description: Audit companion plugins (caveman, claude-mem, pokemon-buddy) — read-only, advisory
---

# /dodojo:companions

Invoke the `companions` skill. Checks `~/.claude/plugins/installed_plugins.json` for three recommended companion plugins and prints install commands for any missing.

Run command:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/companions-audit.py
```

DoDojo runs fully standalone — companions are optional but each unlocks workflow you'd otherwise hand-roll. Read-only: never modifies settings.
