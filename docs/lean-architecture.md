# Lean architecture

DoDojo's design rule: **scripts do the work, Claude is only invoked for judgment.**

## The problem this solves

Every Claude Code plugin loads its skill descriptions into your context on session start. That's a per-session token tax you pay before you type a single character. Multiply by sessions/day, multiply by 30 days, and the bill adds up.

Most plugins make it worse by wrapping every operation in a `Skill`, even when the operation is pure data analysis. A "memory audit" that could be a shell script becomes a 2,000-token conversation.

DoDojo flips this.

## Three layers

```
┌─────────────────────────────────────────────────────────┐
│ Layer 3: Skills (escalation)                            │
│  - memory-curator, recall, sensei, pr-describe, ...     │
│  - Cost: tokens, only when invoked                      │
│  - Use case: fuzzy judgment, language tasks             │
└─────────────────────────────────────────────────────────┘
          ↑ invoked only when judgment needed
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Reports (artifacts)                            │
│  - Markdown files in ~/.claude/dodojo/reports/          │
│  - JSON state in ~/.claude/dodojo/state/                │
│  - Read in your editor — no Claude involvement          │
└─────────────────────────────────────────────────────────┘
          ↑ written by
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Scripts (the engine)                           │
│  - Python + Bash in bin/                                │
│  - Run in shell, zero Claude tokens                     │
│  - Output: JSON + Markdown                              │
└─────────────────────────────────────────────────────────┘
```

## How a typical operation flows

### Audit your plugin stack

```
You type:  dj audit
           ↓
Shell runs:  bin/audit-stack.py
           ↓
Script reads: ~/.claude/plugins/cache/* (file system)
              ~/.claude/settings.json (text file)
              ~/.claude/dodojo/telemetry/*.jsonl (text files)
           ↓
Script writes: reports/audit-stack-latest.md
               state/audit-stack.json
           ↓
You read:  the Markdown report in your editor

Total Claude tokens spent: 0
```

### When Claude does enter

```
You type:  /dodojo:memory-curator
           ↓
Skill loaded: reads pre-flagged report from state/
           ↓
Claude reads: only the candidates the script flagged ambiguous
           ↓
You + Claude: discuss, decide, Claude rewrites memory entries

Total Claude tokens: ~2K (vs ~50K if Claude scanned all memories itself)
```

The escalation is **explicit and bounded**. You always know when tokens are being spent.

## Rules of thumb

When designing a new DoDojo capability, ask:

1. **Can a script return the same answer?**
   If yes → script. No skill.

2. **If Claude is involved, is it reading flagged candidates or scanning everything?**
   Flagged → keep skill. Scanning everything → move the scan to a script, have Claude read the flag list.

3. **Is the script usable outside Claude Code?**
   If yes → ✓ (this is the tell that you've separated data from judgment)

4. **Does the output need to be a conversation, or is it an artifact?**
   Artifact → write a Markdown report. Conversation → skill.

## What this rules out

- **No background daemons.** Stateless scripts, fired on demand or by hooks.
- **No web dashboards.** Static Markdown + JSON files; viewable in any editor.
- **No auto-actions.** Everything destructive (prune, archive, delete) requires explicit user confirmation via terminal prompt.
- **No telemetry exfiltration.** All session data stays in `~/.claude/dodojo/telemetry/` on your machine.

## Data layout

```
~/.claude/dodojo/                  # USER DATA (survives plugin updates)
├── telemetry/
│   ├── sessions.jsonl             # one line per session start
│   ├── session-summary.jsonl      # per-session token + tool breakdown
│   └── skill-usage.jsonl          # which skills you invoked
├── reports/
│   ├── audit-stack-latest.md      # symlink-equivalent to today's
│   └── audit-stack-YYYY-MM-DD.md  # dated history
└── state/
    └── audit-stack.json           # for statusline to read

~/.claude/plugins/cache/dodojo/dodojo/<version>/   # PLUGIN CODE (nuked on update)
├── bin/                           # scripts (this is what dj invokes)
├── skills/                        # Claude-judgment layer
├── hooks/                         # event hooks
└── commands/                      # slash command definitions
```

User data never lives in the plugin cache — that would lose all telemetry on each plugin update.

## Why this approach scales

A plugin author optimizing for the lean model writes:
- Many small scripts (cheap to maintain, easy to compose)
- Few skills (only where judgment is non-script-able)
- Plain data artifacts (Markdown, JSON) instead of stateful services

The end user gets:
- Predictable token costs (zero by default, opt-in for skills)
- Visibility into what's costing them (`dj audit`)
- Reproducible reports (commit them, diff them, share them)
- A fast statusline (reads pre-computed state, no live work)

The plugin ecosystem benefits if more authors adopt this. DoDojo aims to be the reference implementation.

## Related

- [`greeter-vs-statusline.md`](greeter-vs-statusline.md) — concrete application of the "visibility ≠ passive context" principle to a real design choice users have to make.
