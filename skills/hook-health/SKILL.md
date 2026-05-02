---
name: hook-health
description: Smoke-test every hook registered in settings.json — verifies file exists, is executable, exits cleanly with sample input, and is not stale. Use when user asks "check hooks", "are my hooks working", "hook health", or after editing settings.json / adding new hooks.
domain: meta
category: ops
---

# hook-health

Smoke-test every Claude Code hook. Catches broken, missing, non-executable,
or stale hooks before user notices odd session behavior.

## When to invoke

- User asks "are my hooks working", "check hooks", "hook status"
- After adding/editing hooks in `~/.claude/settings.json`
- After bulk-renaming hook scripts
- Periodic hygiene (pair with `audit-context` + `memory-curator`)

## Procedure

```bash
python3 ~/.claude/scripts/hook-health.py            # standard report
python3 ~/.claude/scripts/hook-health.py --verbose  # show stdout sizes per hook
```

Returns exit 1 if any hook fails (useful for CI / cron).

## What's checked

For every hook in `settings.json`:

1. **File exists** at the configured path
2. **Executable bit** set (chmod +x)
3. **Smoke test**: feeds realistic sample stdin (event-aware), expects exit 0 (allow) or 2 (block-with-message)
4. **Stale check**: warns if file unmodified > 90 days
5. **Stderr noise**: warns if exit 0 but wrote to stderr

## Output

```
Hook health check (N registered)
======================================================================
  ✓ [Event           ] hook-name.sh        clean exit 0
  ⚠ [Event           ] old-hook.sh         stale (95d > 90d)
  ✗ [Event           ] broken.sh           exit 1 — stderr: ...

Summary: X OK, Y WARN, Z FAIL
```

## Edge cases

- Event has no sample input → script falls back to minimal `{"session_id": ...}`. Add to `SAMPLE_INPUTS` dict in `hook-health.py` if needed.
- Hook has side effects (writes files, sends webhooks) → smoke test will trigger them. Consider adding a per-hook dry-run flag if this becomes a problem.
- Hook intentionally exits non-zero on real input but smoke gives dummy → `--verbose` to inspect.

## Related

- `~/.claude/hooks/README.md` — hook contract + trigger matrix
- `audit-context` — context budget audit (complementary)
- After adding hook: register in settings.json, then run this skill to verify
