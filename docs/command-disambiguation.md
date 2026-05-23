# Command disambiguation

Several command names look similar but target different domains. Quick map:

| Command | Domain | What it does |
|---------|--------|--------------|
| `/dodojo:audit` | **Plugin stack** | Token cost per plugin, prune candidates. Runs `bin/audit-stack.py`. Zero Claude tokens. |
| `/dodojo:audit-memory` | **Memory files** | Context budget, orphan memories never matched. Invokes `audit-context` skill. |
| `/dodojo:prune` | **Plugin stack** | Interactive cleanup of unused plugins. `bin/prune.py`. Zero Claude tokens. |
| `/dodojo:prune-memory` | **Memory files** | Archive orphan memory entries to `_archive/`. Invokes `archive-orphans` skill. |
| `/dodojo:health` | **Hooks** | Smoke-test every registered hook. Invokes `hook-health` skill. |

## Related skills (no `/command` shortcut)

- `memory-curator` — periodic memory audit: duplicates, stale refs, oversized INDEX, expired (`expires:` past today). Broader than `archive-orphans`.
- `archive-orphans` — narrow: only orphans (zero smart-context matches). Stricter, telemetry-gated.
- `surgical-edit` — large-file edit protocol (used when cost-guard blocks a full Read).

## When the names trip you up

- "audit" alone → plugin stack (token cost). For memory, add `-memory`.
- "prune" alone → plugin stack (uninstall). For memory, add `-memory`.
- "memory" in the name → always memory file domain, never plugin stack.

If the dual naming keeps confusing, the long-term plan is to fold `audit-memory` and `prune-memory` into a single namespace like `/dodojo:memory <audit|prune>`. Not yet done — would break muscle memory.
