# DoDojo

**The plugin that audits your plugins.**
*Free until you ask.*

A Claude Code plugin built on one rule: **scripts do the work, Claude is only invoked for judgment.** Most operations cost zero tokens. The few that need Claude tell you up front.

---

## Why this exists

Every Claude Code plugin you install loads its skill descriptions into your context — every single session, before you type a thing. Most users have no idea how much that costs.

Run `dj audit` on a typical stack and you'll see something like:

```
DoDojo Stack Audit · 9,186 passive tokens/session
  base: 4,889  plugins: 2,857
  prune candidates: 6
```

That's **~$50/month on Opus** burned before any actual work. The leak compounds the more plugins you install. Worse — `"enabled": false` in your settings does **not** prevent skill descriptions from loading. Disabled plugins keep costing.

DoDojo measures it, tells you what to prune, and stays out of your context while doing so.

---

## What you get

### The `dj` CLI — zero-token ops

```bash
dj audit       # Stack audit. Writes a Markdown report. 0 tokens.
dj prune       # Interactive cleanup with safety guards. 0 tokens.
dj report      # Open latest report in $EDITOR.
dj sessions    # Per-session token cost (parsed from transcript).
dj stats       # Telemetry file sizes.
dj help        # All commands.
```

All shell + Python scripts. They never touch your Claude context.

### Always-visible statusline

```
dj 8.6K ↑2.1M · 4🪓
```

- `8.6K` — total passive load per session (green/yellow/red by threshold)
- `↑2.1M` — cumulative tokens this conversation
- `4🪓` — prune candidates available

Reads from a JSON state file. Zero Claude tokens, every keystroke.

### Auto-refresh telemetry

Three lightweight hooks log session metadata + real token spend + skill invocations to local JSONL files. The audit reads from those files. No telemetry leaves your machine.

### Skills (the escalation layer)

When you actually want Claude's judgment — `memory-curator`, `recall`, `sensei`, `pr-describe`, `repro-this`, `archive-orphans`, `audit-context` — skills exist. **They cost tokens by design**, but only when you invoke them. Default state is silent.

---

## The big finding

While auditing my own machine, I discovered:

> **Six "disabled" plugins were still costing me 2,712 tokens per session.**

Uninstalled them. Got the predicted savings to the token. Got back 212MB of disk. Most users don't know this is happening to them.

`dj audit` will show you the same on your machine. `dj prune` will help you fix it — interactively, never automatically, with `rm -rf` paths shown before action.

---

## Install

```bash
# In Claude Code
/plugin marketplace add andriar/DoDojo-claude
/plugin install dodojo

# Bootstrap the dj CLI on your PATH
/dodojo:dj-install
```

Then:

```bash
dj audit
```

Optional — wire the statusline:

```jsonc
// ~/.claude/settings.json
"statusLine": {
  "type": "command",
  "command": "/home/<you>/.claude/plugins/cache/dodojo/dodojo/<version>/bin/statusline.sh"
}
```

Or compose with another existing statusline (e.g. poke):

```jsonc
"statusLine": {
  "type": "command",
  "command": ".../bin/statusline-composed.sh"
}
```

---

## How it stays cheap

Three principles. Full breakdown in [`docs/lean-architecture.md`](docs/lean-architecture.md).

### 1. Scripts own data, Claude owns judgment

Anything that's *pure analysis* (read files, count tokens, detect duplicates) is a Python or Bash script. Only the *fuzzy decisions* (is this memory still relevant? rewrite this tighter?) escalate to a skill.

Most plugins wrap every operation in a skill. We wrap none of the script-able ones.

### 2. Reports are artifacts, not conversations

`dj audit` writes `~/.claude/dodojo/reports/audit-stack-latest.md`. You read it in your editor. You decide what to prune. Claude isn't in the loop.

### 3. Statusline > daemons

No background services. No web dashboard. The statusline reads a JSON state file refreshed by a SessionStart hook. Total passive cost: zero processes, zero tokens.

---

## Where this fits in the token-saver ecosystem

DoDojo is *complementary*, not a replacement:

| Tool | What it saves | Where it acts |
|---|---|---|
| [caveman](https://github.com/JuliusBrussee/caveman) | Output verbosity | Response compression |
| [claude-mem](https://github.com/thedotmack/claude-mem) | History context | Session compaction |
| **DoDojo** | **Plugin overhead + memory hygiene** | **Stack audit + lean ops** |

Stack them. They don't conflict.

---

## Slash commands at a glance

| Command | What it does | Cost |
|---|---|---|
| `/dodojo:audit` | Plugin stack audit (the lean one) | 0 tokens |
| `/dodojo:prune` | Interactive plugin cleanup | 0 tokens |
| `/dodojo:dj-install` | Bootstrap `dj` CLI on PATH | 0 tokens |
| `/dodojo:audit-memory` | Memory/context audit (legacy, invokes skill) | tokens |
| `/dodojo:prune-memory` | Orphan memory archival (legacy, invokes skill) | tokens |
| `/dodojo:sensei` | Pattern-coach analysis | tokens |
| `/dodojo:companions` | Companion file scan | tokens |
| `/dodojo:health` | Skill+hook health check | tokens |

For zero-token operations, prefer the `dj` CLI directly or the lean slash commands.

---

## What DoDojo is NOT

Honest scope:

- **Not a productivity gimmick.** No XP, no badges, no streaks.
- **Not for teams.** Single-maintainer tool. No central server.
- **Not magic.** Claude Code still loads memory eagerly. We help you keep what loads tight.
- **Not a replacement for thinking.** It's a janitor, not a librarian.
- **Not a silver bullet.** Saves ~30% passive cost on a typical stack. The rest is on you.

---

## File layout

```
plugin-root/
├── bin/                       # zero-token CLI tools (NEW in v0.4)
│   ├── dj                     # CLI entry
│   ├── audit-stack.py         # plugin stack audit
│   ├── prune.py               # interactive cleanup
│   ├── statusline.sh          # always-visible cost
│   ├── statusline-composed.sh # composable statusline
│   ├── refresh-audit.sh       # SessionStart auto-refresh
│   ├── log-session-start.sh   # telemetry
│   └── log-session-stop.sh    # telemetry (token capture)
├── skills/                    # Claude-judgment escalation layer
├── hooks/                     # legacy hooks (greet, smart-context, etc.)
├── commands/                  # slash command definitions
├── scripts/                   # utility scripts (memory, install, sensei)
└── docs/
    └── lean-architecture.md   # design philosophy
```

User data (telemetry, reports, state) lives in `~/.claude/dodojo/` — survives plugin updates.

---

## Verifying the claims

Reproducibility matters for a cost-focused tool. Anyone can verify:

```bash
# Snapshot your current passive load
dj audit
cat ~/.claude/dodojo/state/audit-stack.json

# Uninstall a "disabled" plugin
rm -rf ~/.claude/plugins/cache/<plugin>

# Re-audit
dj audit
cat ~/.claude/dodojo/state/audit-stack.json
```

The `total_passive_tokens` should drop by exactly the predicted amount. If it doesn't, file an issue.

---

## Roadmap

What's shipped (v0.4):
- ✅ `dj audit` — stack token audit
- ✅ `dj prune` — interactive cleanup
- ✅ Statusline with always-visible passive cost
- ✅ Session telemetry (sessions, summaries, skill usage)
- ✅ Auto-refresh on SessionStart

What's next:
- `dj memory` — INDEX.md auditor (find duplicates, expired entries) without invoking Claude
- `dj benchmark` — measure DoDojo's own token cost vs comparable plugins, with receipts
- `dj friday` — composes audit + memory + sensei into a Friday review ritual

What's permanently *not* shipping:
- Web dashboard (use the Markdown report)
- Background daemons (stateless by design)
- Auto-prune (you decide, every time)

---

## License

MIT. See [LICENSE](LICENSE).

---

## A note on the design

DoDojo started as a multi-feature meta-toolkit. It grew. Then I measured its own token cost and was embarrassed by what I found.

This README is the v0.4 of the rebuilt project: **one focused job, done at zero passive cost.** Everything else is escalation.

If you're paying for Claude Code and feeling the bill, run `dj audit`. If you have ideas for what `dj` should do next, open an issue — but be ready to defend why the answer isn't "just read the report yourself."
