# Audit — context budget + bloat detection

`/dodojo:audit` measures how many tokens load into every Claude Code session and flags bloat. Backed by the [`audit-context` skill](../skills/audit-context/SKILL.md).

## What it counts

- **CLAUDE.md** at every level (`~/.claude/CLAUDE.md` + project root + parent dirs)
- **`@-references`** inside CLAUDE.md (recursive — `@RTK.md` pulls another file)
- **`MEMORY.md`** index files in `~/.claude/memory/` and project memory dirs
- **Skills index** — bundled + custom

## Output

| Section | What you see |
|---------|-------------|
| Total tokens | Combined load per session start |
| Top files by size | Which file contributes most — pruning candidates |
| Orphan memories | Memory files with **zero matches** in smart-context telemetry (last 30d) |
| Bloated INDEX.md | Index files past 200-line budget |
| Stale entries | Memories with `expires:` frontmatter past today |

## When to run

- Session feels slow (>2s before first prompt)
- After importing memory from another machine
- Monthly hygiene
- Before sharing CLAUDE.md to teammates

## Companion commands

- `/dodojo:prune` — actually archive the orphans
- `/dodojo:status` — quick stat without full audit
- `dodojo:memory-curator` skill — interactive curator with merge/dedupe

## Telemetry source

Audit reads smart-context match logs at `~/.claude/hooks/smart-context.log`. Needs ≥7 days of usage to give meaningful orphan signal. Prune refuses to `--apply` if telemetry too thin.

## Related

- [prune.md](prune.md) — apply the orphan candidates audit surfaces
- [health.md](health.md) — companion smoke-test for hooks (audit covers memory, health covers hooks)
- [sensei.md](sensei.md) — Sensei mines what audit measures
- [status.md](status.md) — greeter shows audit summary every session
