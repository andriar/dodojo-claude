---
name: archive-orphans
description: Archive orphan memory files (zero matches in smart-context telemetry) to ~/.claude/memory/_archive/ and prune INDEX.md row. Dry-run by default; --apply required to actually move. Refuses to apply if telemetry below threshold. Use when user asks "prune memory", "archive unused memories", or after sufficient telemetry accumulated.
domain: meta
category: ops
---

# archive-orphans

Move global memory files never matched by `smart-context` to
`~/.claude/memory/_archive/`, prune corresponding row in INDEX.md.
Closes the loop opened by smart-context telemetry.

## When to invoke

- User asks "prune memory", "archive unused", "clean up memory"
- Sensei weekly report flags persistent orphans
- Triggered after 2026-05-16 systemd report once telemetry ≥ 50
- NOT for first-pass cleanup — needs real session usage data first

## Procedure

**Always dry-run first:**

```bash
python3 ~/.claude/scripts/archive-orphans.py
```

Review output WITH user. If user agrees:

```bash
python3 ~/.claude/scripts/archive-orphans.py --apply
```

Recommended whitelist (always pass these `--keep` flags):

```bash
python3 ~/.claude/scripts/archive-orphans.py \
  --keep identity_kagami \
  --keep respect_mode \
  --keep pokemon_plugin \
  --apply
```

## Safety rails

- Default = dry-run. `--apply` is the only way to actually move files.
- Refuses `--apply` if telemetry < 50 invocations.
- Files moved (not deleted) — `_archive/` is recoverable.
- Each archived file gets sibling `<name>.archived.txt` audit note.
- INDEX.md rows pruned by exact `(filename.md)` link match.
- Only scans top-level `~/.claude/memory/*.md` — NOT project-specific memories.

## After applying

```bash
python3 ~/.claude/hooks/context-audit.py   # verify INDEX.md shrank
python3 ~/.claude/hooks/smart-context-stats.py --orphans  # confirm cleared
```

## Edge cases

- Some "orphans" are intentionally low-traffic but vital (incident runbooks, identity, mode directives) — always whitelist via `--keep`.
- Telemetry log corrupted → script treats as 0 invocations, refuses apply.
- File in `_archive/` already → script skips silently.
- Restore: `mv ~/.claude/memory/_archive/<file>.md ~/.claude/memory/` and re-add INDEX row manually.
