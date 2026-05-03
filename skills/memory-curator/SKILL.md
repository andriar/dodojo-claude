---
name: memory-curator
description: Audit & prune memory files at ~/.claude/memory/ + ~/.claude/projects/*/memory/. Detects duplicates, stale refs, oversized INDEX (>200 lines), orphans, and expired (`expires:` frontmatter past today — auto-archive supported). Use when memory tumbuh besar, sebelum re-assessment, atau periodic audit.
domain: meta
category: ops
---

# Memory Curator

Audit memory files cross-repo + project-scoped. Bersih + dedupe.

## Scope

- Cross-repo: `~/.claude/memory/*.md` + `INDEX.md`
- Project: `~/.claude/projects/*/memory/*.md` + `MEMORY.md`

## Subcommands

### `audit`
Output per-file tabel:
- file path
- lines
- type (frontmatter `type:`)
- last modified
- referenced from INDEX/MEMORY? (yes/no)
- duplicate signal (overlapping `name:` atau topik di body)
- stale signal (grep refs ke fungsi/file yg tidak ada di codebase)

```bash
# 1. List all memory + INDEX coverage
find ~/.claude/memory ~/.claude/projects/*/memory -name "*.md" -not -name "INDEX.md" -not -name "MEMORY.md"
# 2. Check INDEX coverage
grep -rohE '\[.*\]\(([a-z_]+\.md)\)' ~/.claude/memory/INDEX.md ~/.claude/projects/*/memory/MEMORY.md | sort -u
# 3. Diff: orphans = files not in INDEX
```

### `dedupe`
Cari memory dengan topik overlap:
- compare `name:` + `description:` frontmatter, output cluster similarity
- compare body (key terms), highlight pasangan likely-merge
- pasangan diusulkan: `[a.md, b.md] → suggest merge into a.md, delete b.md`

### `stale-check`
Untuk memory yang nyebut nama file/fungsi/flag spesifik:
```bash
# Extract refs (e.g., `path/to/file.ts`, `functionName(`)
grep -hE '`[a-zA-Z0-9_/.-]+\.(ts|tsx|js|jsx|py|rb|go|sh)`' <memory.md>
# Verify each exists. Missing refs → stale.
```

### `index-budget`
Cek `INDEX.md` size:
- > 150 baris → warning
- > 200 baris → over budget, must prune

```bash
wc -l ~/.claude/memory/INDEX.md ~/.claude/projects/*/memory/MEMORY.md
```

### `expiry`
Scan memory frontmatter for `expires: YYYY-MM-DD`. Report expired + soon-to-expire. Auto-archive expired with `--archive` (moves file to `_archive/<YYYY-MM>/`, prunes INDEX entry).

```bash
# Report only
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory-expiry.py
# Archive expired + prune INDEX
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory-expiry.py --archive
# Widen warning window (default 7 days)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory-expiry.py --warn-days 30
```

**When to add `expires:`** — time-bound facts: deadlines, freezes, "remove once X" TODOs, staged rollouts, temp workarounds, scheduled migrations. Skip for durable lessons (feedback rules, user profile).

Frontmatter example:
```yaml
---
name: Mobile release freeze
description: Non-critical merges blocked through 2026-05-15
type: project
expires: 2026-05-15
---
```

### `prune <file>`
Hapus file + remove pointer dari INDEX/MEMORY. Konfirmasi user dulu. Backup ke `~/.claude/.memory-trash/$(date +%Y%m%d)/<file>` sebelum hapus.

## Output Format

```markdown
# Memory Audit Report — YYYY-MM-DD

## Summary
- Total files: N
- Cross-repo: X | Project-scoped: Y
- Orphans (not in INDEX): Z
- Likely duplicates: K pairs
- Stale refs detected: M files

## Orphans
- file.md (no INDEX entry) — last modified YYYY-MM-DD

## Duplicate Candidates
- a.md ↔ b.md — overlap on "topic X" → merge into a.md
- ...

## Stale References
- foo.md — refs `src/oldfile.ts` not found

## INDEX Budget
- ~/.claude/memory/INDEX.md: 24 / 200 lines ✓
- project/X/MEMORY.md: 5 / 200 lines ✓

## Recommended Actions
1. Merge a.md → b.md (delete a.md)
2. Update foo.md or delete (stale)
3. Add INDEX entry for orphan.md
```

## Boundaries

- **JANGAN auto-delete** — selalu output candidates, user approve.
- **Backup sebelum hapus** ke `.memory-trash/`.
- **Hormati per-project scope** — jangan campur cross-repo lessons dengan project-specific facts.
- **`MEMORY.md`/`INDEX.md` = index, bukan memory** — jangan delete.

## Why

Memory drift natural seiring waktu: duplikat muncul saat konteks lupa, stale saat code refactored. Tanpa audit periodik → INDEX bloat, recall melambat, signal kabur. Goal: keep INDEX < 200 baris, body < 30 baris per memory, zero stale refs.

## How to Apply

Run sebelum re-assessment, atau `/schedule` 2-4 minggu sekali. Output report ke `~/Downloads/memory-audit-YYYY-MM-DD.md` untuk review santai.
