# Prune — archive orphan memories

`/dodojo:prune` archives memory files that smart-context **never matched** in any prompt over the telemetry window. Backed by the [`archive-orphans` skill](../skills/archive-orphans/SKILL.md).

## What's an orphan

A memory file is orphan if:
- Lives in `~/.claude/memory/` or project memory dir
- Has **zero matches** in `~/.claude/hooks/smart-context.log` over last 30 days
- Not referenced by another loaded file (CLAUDE.md, INDEX.md, skill SKILL.md)
- Not in `_archive/` already

## Modes

```bash
/dodojo:prune              # dry-run — list candidates, no writes
/dodojo:prune --apply      # actually move to _archive/
/dodojo:prune --window 60  # custom telemetry window in days
```

## Safety gates

- **Telemetry threshold** — refuses `--apply` if smart-context log has <100 entries (signal too thin)
- **Index sync** — automatically removes the orphan's row from `INDEX.md` (no dangling links)
- **Reversible** — files moved to `_archive/`, not deleted. Restore via `mv` back

## Output

```
Orphan candidates (30-day window, 1,247 telemetry entries):

  ◦ docker_bind_mount_stale.md     last match: never  size: 1.1KB
  ◦ pnpm_env_brittle.md            last match: never  size: 0.8KB
  ◦ slowapi_headers_param.md       last match: 89d ago  size: 1.4KB

3 candidates · 3.3KB recoverable
Run /dodojo:prune --apply to archive
```

## When to run

- Quarterly hygiene
- After importing memories from another machine (many won't match your work)
- When `/dodojo:audit` flags >20 orphans

## Lifecycle interaction

- `dodojo:memory-curator` skill — interactive variant with merge proposals
- `expires:` frontmatter — `dodojo:memory-curator` auto-archives time-bound entries past their date (no telemetry needed)

## What it won't prune

- Files referenced by `@-syntax` in any loaded `.md`
- Files in `_drafts/` (assumed work-in-progress)
- `INDEX.md` itself (the index, not an entry)
- Files modified in last 7 days (assumed fresh)

## Related

- [audit.md](audit.md) — surfaces orphan candidates before you prune
- [sensei.md](sensei.md) — mines patterns from what survives pruning
- [status.md](status.md) — orphan count shown in greeter "Memory health" section
