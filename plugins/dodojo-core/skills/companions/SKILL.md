---
name: companions
description: Audit which DoDojo companion plugins (caveman, claude-mem, pokemon-buddy) are installed; print install command + role for any missing. Read-only — never writes settings. Use when user asks "what plugins should I install with dodojo", "companion check", "audit my plugin stack", or after fresh dodojo install.
domain: meta
category: ops
---

# companions

Audit companion plugins recommended alongside DoDojo. DoDojo runs standalone — these are
optional but each unlocks workflow lo'd otherwise hand-roll.

## When to invoke

- After `/plugin install dodojo@dodojo` — surface useful neighbours
- During `/dodojo:init` — appended as final step automatically
- Periodic stack hygiene
- Onboarding new contributor / fresh machine

## Procedure

```bash
python3 ~/.claude/plugins/cache/dodojo/dodojo/<ver>/scripts/companions-audit.py
```

Or just invoke the skill — wrapper resolves `${CLAUDE_PLUGIN_ROOT}`.

## What's checked

For each of 3 recommended companions, lookup `~/.claude/plugins/installed_plugins.json`:

| Companion | Role | Why pair with DoDojo |
|-----------|------|----------------------|
| `caveman` | Output compression ~75% token saving | DoDojo greeter + Sensei output is verbose; caveman trims |
| `claude-mem` | Cross-session deep recall + AST code nav + multi-phase planner | DoDojo smart-context is top-5 fresh; claude-mem covers historic depth |
| `poke` (pokemon-buddy-claude) | Gamification — XP, badges, raids on dev work | DoDojo `session-summary` + buddy-xp-pending hook integrate; greeter shows XP |

## Output

```
DoDojo companion plugins audit
============================================================
  ✓ caveman        installed (caveman@caveman)
  ✗ claude-mem     missing — Cross-session deep recall + AST code nav...
       /plugin install claude-mem@thedotmack
  ✓ poke           installed (poke@pokemon-buddy-claude)

2/3 recommended companions present
Optional — DoDojo works fully standalone.
```

## Design notes

- **Read-only**: never modifies `installed_plugins.json` or `settings.json`. Prints install command — user invokes manually.
- **Not auto-install**: Claude Code plugin install needs interactive `/plugin` prompt; cannot be triggered from script safely.
- **Detection is by name prefix** (e.g. `caveman@*` matches any marketplace fork). Alias support for `poke` ↔ `pokemon-buddy-claude`.

## Related

- `/dodojo:init` — calls this skill at final step
- `/dodojo:status` — shows DoDojo state but not companions
- `~/.claude/plugins/installed_plugins.json` — source of truth for installed plugins
