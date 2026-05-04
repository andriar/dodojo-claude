# Quickstart — Install → ROI in 5 minutes

Get DoDojo working and see your first automation recommendation by end of this guide.

## 1. Install (1 min)

In Claude Code:

```bash
/plugin marketplace add andriar/dodojo-claude
/plugin install dodojo@dodojo
```

Restart Claude Code (⌘Q + reopen).

## 2. Setup wizard (2 min)

```bash
/dodojo:init
```

Wizard asks:
- **Theme** — `default` or `compact`
- **Icons** — `nerd` (fancy), `emoji` (portable), `unicode` (clean)
- **Colors** — `0` (off) or `1` (on)
- **Coach** — enable Sensei (pattern mining)? `y` (recommended) or `n`

Hit defaults if unsure. Takes ~90 sec.

## 3. See it work (2 min)

Next session, you'll see DoDojo greeter banner:

```
┌─────────────────────────────────────────┐
│ DoDojo · quiet workflow discipline       │
│                                          │
│ 🔄 Memory  ✓ clean                      │
│ 📊 Context  ✓ 3 matches                 │
│ 🎯 Route   trivial → haiku               │
│ 🧠 Sensei  next report: 2026-05-11      │
│ 🎮 Buddy   level 12 (2,430 XP)          │
│                                          │
│ 🚀 /dodojo:status  /dodojo:sensei        │
└─────────────────────────────────────────┘
```

Your first **Sensei weekly report** arrives May 11. It'll mine your last week's git commits + shell history, rank work by ROI (time saved / automation potential), and recommend what to automate next.

Example first rec: *"You manually repeated `git status → git add → git commit` 47× this week. Consider a commit hook that auto-stages changes to watched files."*

## 4. See Sensei report

Run once Coach is enabled:

```bash
/dodojo:sensei
```

Or wait for next Monday 9am (default cron in docs/sensei.md).

Report lands at `~/.claude/dodojo/sensei/reports/` as markdown. Open in editor or Obsidian (if configured).

## 5. Next steps

- **Full docs** → [docs/README.md](README.md)
- **Memory + auto-reflect** → [docs/positioning.md](positioning.md) (how DoDojo fits with caveman + claude-mem)
- **Sensei privacy/setup** → [docs/sensei.md](sensei.md)
- **Routing rules** → [docs/routing/](routing/) (control which Claude model each task uses)

## Troubleshooting

**Greeter doesn't show?**
- Check `DODOJO_DATA` env var is set (should be `~/.claude` by default)
- Run `/dodojo:health` to diagnose

**Sensei not mining?**
- First report takes 7–14 days (needs history data). Run manually: `/dodojo:sensei`
- Make sure `SENSEI_VAULT` or `SENSEI_HISTORY` env is set (setup wizard does this)

**Want to tweak?**
- `KAGAMI_SILENT=1` skips context injection (saves ~400 tokens/session if you prefer terse mode)
- Colors: `KAGAMI_COLOR=1` for ANSI
- Icons: `KAGAMI_ICONS=unicode` for plain text
- All env vars in `~/.claude/settings.json` → `env` block

## Why this works

DoDojo stays invisible until it finds *your* pattern. Sensei doesn't recommend automation—it *mines* what you've already done and suggests what to codify. First rec is often an eye-opener: "Oh, I really do that 40× a week."

Once you automate one pattern, you see the compounding effect. By month 2, you've clawed back 2–4 hours/month just from one or two hooks.

Next: [docs/README.md](README.md) for all commands, or [docs/sensei.md](sensei.md) for deeper setup.
