---
description: DoDojo control panel — status, audit, prune, configure
---

# /dodojo

Show DoDojo status. Optional subcommands:

- `/dodojo status` — current config, hooks active, memory count
- `/dodojo audit` — invoke the `audit-context` skill
- `/dodojo prune` — invoke the `archive-orphans` skill (dry-run)
- `/dodojo health` — invoke the `hook-health` skill
- `/dodojo theme [name]` — switch greeter theme
- `/dodojo icons [nerd|unicode|emoji]` — switch icon mode

## Behavior

When invoked without args: print current state — theme, icon mode, `DODOJO_DATA` path, hook count, memory file count, last session token-saved estimate.

When invoked with subcommand: route to the matching skill or run the inline action.
