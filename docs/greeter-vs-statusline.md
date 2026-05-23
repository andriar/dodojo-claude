# Greeter vs Statusline — pick the right channel

DoDojo gives you two ways to surface session info. They look similar but cost very different amounts. Choose deliberately.

## TL;DR

| Need | Use |
|---|---|
| "Show me always-current passive cost / prune candidates" | **Statusline** |
| "Run a rich welcome ritual when I open Claude Code" | **Greeter** (optional, opt-in) |
| "I want zero passive token cost" | **Statusline only** — disable the greeter |
| "I like the ritual and don't care about ~50 tokens/session" | Both |

If you're reading this because you adopted DoDojo for the lean positioning: **default to statusline only.**

---

## What each one is

### Statusline (`bin/statusline.sh`)

A one-line segment painted by your terminal in the status bar. Updates on every keystroke. Reads from a pre-computed JSON state file. **Lives outside Claude's context.**

```
dj 8.6K ↑6.8M · 4🪓
```

- Painted by your shell, not by Claude
- Claude never reads it
- Zero passive tokens, every render
- Always-current (refreshed by SessionStart hook in background)

### Greeter (`hooks/dodojo-greet.sh`)

A formatted block injected as `additionalContext` on SessionStart. Includes ASCII art, themed styling, pulse indicator, memory health, buddy XP, quick actions. **Lives inside Claude's context.**

```
⚡ DoDojo  ·  Mirror healthy  ·  Sensei: 3 patterns  ·  Buddy: Pidgey Lv.37
[themed ASCII art block]
[quick-actions menu]
```

- Painted into your conversation by a hook
- Claude *does* read it (it's input tokens)
- Costs ~30-150 tokens depending on theme + content
- Shown once per session

---

## The cost math

### Statusline
- **Per session**: 0 tokens
- **Per month** (assume 200 sessions): 0 tokens
- **Why**: terminal UI, not conversation input

### Greeter (typical 50-100 token block)
- **Per session**: ~75 tokens (median)
- **Per month** (200 sessions): ~15,000 tokens
- **Per year**: ~180,000 tokens
- **Cost on Opus** (~$15/M input): ~$2.70/year just to greet yourself

### Greeter (themed, with ASCII art + buddy)
- **Per session**: ~150-300 tokens
- **Per year**: ~360K-720K tokens
- **Cost on Opus**: ~$5.40-$10.80/year

Not catastrophic, but real. And it grows linearly with usage. The lean architecture argues: you can have the same information for free via statusline.

---

## When greeter actually earns its tokens

Honest pros for keeping the greeter on:

- **Ritual/mood**: opening Claude feels like sitting down at a workbench you've set up. Some users genuinely work better with a welcome cue.
- **Themed art**: a customization vector. If you've configured a theme you like (`/dodojo:theme`), the greeter is where it shows up.
- **One-time context**: the greeter can dump info that's *useful at session start but stale by mid-conversation* — current sensei pattern alerts, buddy XP grants, alert queue. Statusline can't show this volume.
- **Discoverability**: new users see "DoDojo is here, you can do X, Y, Z." Statusline alone is silent — you have to know to look at it.

Tradeoff: you pay for the ritual in tokens.

---

## When statusline is enough

Honest pros for going statusline-only:

- **You already know what DoDojo does**. The greeter's discoverability value is zero for veteran users.
- **You're cost-sensitive**. Even 15K tokens/month matters when you're on a tier limit.
- **You don't want startup noise** in the conversation. A clean transcript without a greeting block makes the conversation feel like a focused thread.
- **You believe in the lean philosophy**. The whole point of DoDojo v0.4 is "free until you ask." The statusline embodies that; the greeter contradicts it.

---

## How to choose

### Default for the lean adopter

**Statusline on, greeter off.** This is the configuration the v0.4 README assumes and the tagline ("Free until you ask") commits to.

### Default for the existing v0.3 user

Both on, until you decide otherwise. The pivot doesn't force anything on you.

### How to disable the greeter

Edit `~/.claude/settings.json`, find the `SessionStart` hooks array, remove or comment out the `dodojo-greet.sh` entry:

```jsonc
"SessionStart": [
  {
    "matcher": ".*",
    "hooks": [
      // { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/dodojo-greet.sh", "timeout": 5000 },   // disabled
      { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/sensei-greet.sh", "timeout": 5000 },
      { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/bin/log-session-start.sh", "timeout": 2000 },
      { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/bin/refresh-audit.sh", "timeout": 2000 }
    ]
  }
]
```

(`hooks.json` in the plugin lists the hooks; user `settings.json` controls which actually fire.)

### How to enable the statusline

Add or modify the `statusLine` block in `~/.claude/settings.json`:

```jsonc
"statusLine": {
  "type": "command",
  "command": "/absolute/path/to/.claude/plugins/cache/dodojo/dodojo/<version>/bin/statusline.sh",
  "padding": 0
}
```

For composition with another statusline (e.g., pokemon-buddy):

```jsonc
"statusLine": {
  "type": "command",
  "command": "/absolute/path/to/.../bin/statusline-composed.sh",
  "padding": 0
}
```

The composed version detects poke automatically (version-agnostic glob).

---

## Why this isn't "one or the other"

You can run both, just understand:

- The **statusline** is your *always-current dashboard* — passive cost, prune candidates, session token total. It's the lean primitive.
- The **greeter** is your *welcome ritual* — themed, festive, one-shot. It's a UX flourish.

They overlap in showing "DoDojo is alive" but otherwise serve different needs. Running both means you get the ritual AND the live cost monitor — for the price of the ritual.

The lean architecture position is: most users don't need the ritual. But if you do, own the cost transparently.

---

## Quick decision matrix

| You are... | Recommended config |
|---|---|
| New DoDojo user, lean-curious | Statusline only |
| Existing v0.3 user, happy with themes | Both |
| On a Claude Code tier limit, every token counts | Statusline only |
| Building DoDojo (i.e., me) | Statusline only — eat my own dog food |
| Solo dev who wants a "morning coffee" vibe | Both, accept ~$5/year |
| Posting screenshots / demo videos | Statusline only — it's visible in every frame |

---

## The principle this illustrates

Visibility ≠ passive context.

- **Visibility** = the user can see/find the info → statusline, `dj audit` output, dashboard, terminal report
- **Passive context** = Claude reads it every session → greeter, CLAUDE.md, INDEX.md, skill descriptions

Most plugin designs conflate the two. They think "I want users to see X" and reach for a greeter, hook output, or `additionalContext` injection — which costs tokens forever.

DoDojo's rule: **maximize visibility, minimize passive context.** Use the statusline (free, always-visible). Reserve greeters for genuinely valuable one-shot moments where the token cost is justified (alert escalation, first-time welcome, schedule digests).

If you find yourself wanting more "greeting", the right answer is usually: write a script, run it manually when you want the info, leave the conversation context clean.

This is the same logic behind the broader scripts-vs-skills split. See [`lean-architecture.md`](lean-architecture.md) for the deeper framing.
