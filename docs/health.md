# Hook health — smoke-test registered hooks

`/dodojo:health` verifies every hook in `~/.claude/settings.json` actually works. Backed by the [`hook-health` skill](../skills/hook-health/SKILL.md).

## What it checks

For each registered hook:

| Check | Pass criteria |
|-------|--------------|
| **File exists** | Path resolves to a real file |
| **Executable bit** | `chmod +x` set (or `.py` runnable via shebang) |
| **Sample stdin** | Feeds matcher-appropriate JSON, expects exit 0 or 2 |
| **No stale lock** | No `.lock` files left behind |
| **Reasonable runtime** | Exits within 10s |

## Output format

```
✓ rtk-rewrite.sh           PreToolUse:Bash       12ms
✓ pre-commit-gate.sh       PreToolUse:Bash       890ms
✗ slack-write-whitelist.sh PreToolUse:slack_*    NOT EXECUTABLE
⚠ alerts-greet.sh          SessionStart          3.2s (slow)
✓ buddy-xp-greet.sh        SessionStart          45ms
```

## Common failures

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `NOT FOUND` | Path renamed but settings.json stale | `chmod +x` + update settings |
| `NOT EXECUTABLE` | New hook without `chmod` | `chmod +x ~/.claude/hooks/<name>.sh` |
| `EXIT 1` (silent) | `set -e` + grep no-match | Use `\|\| true` after grep |
| `SLOW` (>2s) | Hook scans whole filesystem | Add cutoff or cache |
| `STDOUT EMPTY` on block | Hook wrote to stdout instead of stderr | Switch to stderr (model only sees stderr on exit 2) |

## Orphan detection

Any executable in `~/.claude/hooks/` **not registered** in settings.json gets flagged as orphan. Either:
1. Register it (add to `hooks.<event>` block in settings.json)
2. Move to `~/.claude/hooks/_archive/`
3. Delete

## When to run

- After adding/editing any hook
- After Claude Code update (manifest format may shift)
- When session start feels slower than usual
- Weekly hygiene (Sensei flags via telemetry)

## Related

- [audit.md](audit.md) — companion: health checks hooks, audit checks memory + context
- [sensei.md](sensei.md) — silent-failing hooks surface in Sensei pattern detector
- [status.md](status.md) — greeter "Pulse" section reflects hook tool counts
