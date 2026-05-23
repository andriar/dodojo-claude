# dodojo-guards

Assertive guard hooks for Claude Code. **Stateless**, no telemetry, no greeter, no skills loaded into the system reminder. Standalone counterpart to the full `dodojo` plugin — if you only want the safety blockers, install this alone.

## What it blocks

| Hook | Event / matcher | Blocks on |
|------|-----------------|-----------|
| `secret-guard.sh` | PreToolUse · `Bash` `Write` `Edit` `MultiEdit` | Realistic-looking secret patterns (AWS keys, GitHub tokens, private keys, etc.) in the tool payload |
| `force-push-guard.sh` | PreToolUse · `Bash` | `git push --force` (and `-f`) when the target branch is `main` or `master` |
| `cost-guard.py` | PreToolUse · `Bash` `Read` | `find /`, `du /`, `grep -r ... /`, `rm -rf /` or `rm -rf $HOME`; Read of >5K-line / >300KB files without `offset`+`limit` |

## What it observes (UserPromptSubmit)

| Hook | Adds to context |
|------|-----------------|
| `inject-git-context.sh` | Current branch name + dirty/clean flag |

## Install

```sh
/plugin marketplace add andriar/dodojo-claude
/plugin install dodojo-guards@dodojo
```

## Token cost

- **Per session**: ~0 (no skill descriptions, no greeter banner)
- **Per Bash/Read/Write tool call**: a few ms of script execution (no model round-trip)

Run `dj profile-hooks PreToolUse` (in the full `dodojo` plugin) to measure on your machine.

## Opt-out per hook

Each hook honors a per-name env var. Set in `~/.claude/settings.json` under `env`:

```jsonc
{
  "env": {
    "DODOJO_SKIP_COST_GUARD": "1",     // disable cost-guard only
    "DODOJO_SKIP_FORCE_PUSH": "1",     // disable force-push guard
    "DODOJO_SKIP_SECRET_GUARD": "1"    // disable secret-guard
  }
}
```

## Relation to other dodojo plugins

- **dodojo-core** (planned) — greeter, telemetry, CLI. Has overlapping guard hooks during transition.
- **dodojo-sensei** (planned) — ROI advisor + weekly digest.
- **dodojo** (legacy meta) — currently bundles all of the above; will become a meta-package that pulls in the three split plugins.
