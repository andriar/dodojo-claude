# Hook taxonomy

Dodojo registers hooks across four Claude Code events. They split into two roles:

## Assertive (can block — exit 2)

| Hook | Event | Blocks on |
|------|-------|-----------|
| `cost-guard.py` | PreToolUse(Bash\|Read) | `find /`, `rm -rf $HOME`, big-file Read without offset+limit |
| `secret-guard.sh` | PreToolUse(Bash\|Write\|Edit\|MultiEdit) | Realistic-looking secrets in payload |
| `force-push-guard.sh` | PreToolUse(Bash) | `git push --force` to main/master |

Exit 2 sends the stderr message back to the model so it can adjust and retry.
These hooks have a contract: refuse the dangerous thing, explain why.

## Passive (additive — always exit 0)

| Hook | Event | Writes to |
|------|-------|-----------|
| `dodojo-greet.{sh,py}` | SessionStart | stdout (additionalContext) — banner + pulse |
| `sensei-greet.sh` | SessionStart | stdout — pending recommendations |
| `log-session-start.sh` | SessionStart | `dodojo/telemetry/sessions.jsonl` |
| `heartbeat-check.py` | SessionStart | `alerts.jsonl` (one entry per outage) |
| `greeter-lean.sh` | SessionStart | stdout — statusline-style summary |
| `inject-git-context.sh` | UserPromptSubmit | stdout — current branch + dirty flag |
| `smart-context.py` | UserPromptSubmit | stdout — top-N memory matches + `hooks/smart-context.log` |
| `skill-suggest.py` | UserPromptSubmit | stdout — matched skill names |
| `memory-trigger.py` | UserPromptSubmit | stdout — context expansion |
| `model-route.py` | UserPromptSubmit | stdout — verdict + `hooks/model-route.log` |
| `session-summary.py` | Stop | `sessions/<day>.jsonl` + frontmatter of injected memory files |
| `log-session-stop.sh` | Stop | `dodojo/telemetry/session-summary.jsonl` |

Passive hooks only observe or inject context. They never refuse a tool call.

## Why this split matters

Blocking is a strong commitment: every PreToolUse(Bash) call pays cost-guard
latency. Adding more assertive hooks raises that floor for every shell command.
Reserve `exit 2` for clear footguns. Use passive hooks for everything else.

If a passive hook is silent-failing the user won't notice in real time, but
`heartbeat-check.py` catches the Stop-hook case by comparing transcript mtime
against sessions log mtime.

## Per-hook opt-outs

Each hook honors at least one env var (set in `~/.claude/settings.json`'s
`env` block, or shell-exported before launch). Common ones:

| Var | Effect |
|-----|--------|
| `DODOJO_GREETER_MODE=off` | Disable both heavy and lean greeters |
| `DODOJO_TELEMETRY_DISABLED=1` | Skip session-start/stop loggers |
| `DODOJO_SKIP_HEARTBEAT=1` | Skip heartbeat outage check |
| `ORCHESTRATOR_LOG_DISABLED=1` | Skip skill-invocation logger |

Run `dj profile-hooks` to see per-hook ms overhead. SessionStart cold start
is typically 200-300ms total across all four hooks.

```
$ dj profile-hooks SessionStart
EVENT              HOOK                                  MS
SessionStart       dodojo-greet.sh                        3
SessionStart       sensei-greet.sh                       81
SessionStart       log-session-start.sh                  11
SessionStart       heartbeat-check.py                    29
SessionStart       greeter-lean.sh                      103
```
