---
description: Interactive DoDojo setup — pick theme, icons, color, Coach (Sensei) paths. Writes to ~/.claude/settings.json.
argument-hint: "[--quick | --reset | --print]"
---

# /dodojo:init

You are running the DoDojo setup wizard. Goal: collect 6 user preferences via `AskUserQuestion`, then write each to the user's `~/.claude/settings.json` `env` block.

## Behavior

If user passed `--quick`: run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/dodojo-init.sh --quick` and exit (writes all defaults silently, runs companions audit).
If user passed `--print`: run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/dodojo-init.sh --print` and exit.
If user passed `--reset`: run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/dodojo-init.sh --reset` and exit.

Otherwise, ask the questions below **one at a time** (or batched 2-3 at once where independent), then write the answers.

## Questions

For every AskUserQuestion call: write a clear `question` text that names the env var **and** what it affects. Write per-option `description` that says the consequence of picking it. Never present an option as a bare label.

1. **KAGAMI_THEME** — header "Theme"
   - Question: "KAGAMI_THEME — greeter banner color palette. Affects only the SessionStart banner colors (divider, accent, success/warn/crit). Code, diffs, tool output use Claude Code's own theme regardless. Pick a popular preset or 'Other' to type any of the 20 themes (default, pastel, neon, retro, mono, dracula, gruvbox, catppuccin, nord, monokai, sakura, shounen, ghibli, mecha, kawaii, evangelion, jjk, aot, frieren, madoka)."
   - Options: `default (Recommended)` description "Cyan/magenta — works on any terminal" | `dracula` description "Purple/pink — high contrast dark" | `catppuccin` description "Pastel mocha — soft on the eyes" | `nord` description "Cool blues — minimal palette"

2. **KAGAMI_ICONS** — header "Icons"
   - Question: "KAGAMI_ICONS — icon set for greeter section markers (memory/sensei/xp/alerts). Affects only the SessionStart banner. Pick based on your terminal font support."
   - Options: `nerd (Recommended)` description "Nerd Font glyphs — sharpest look, requires patched font installed" | `unicode` description "Box-drawing fallback — works on any unicode terminal" | `emoji` description "Full-width emoji — best on wide terminals, may misalign in narrow ones"

3. **KAGAMI_COLOR** — header "Color"
   - Question: "KAGAMI_COLOR — render ANSI colors in greeter? Affects only the SessionStart banner. Disable for narrow / low-color terminals; Claude Code's own UI coloring is unaffected either way."
   - Options: `Yes (Recommended)` description "Full color banner (most modern terminals)" | `No` description "Monochrome banner — for tmux without truecolor, dumb terminals, or accessibility"

4. **DODOJO_GREETER_MODE** — header "Greeter"
   - Question: "DODOJO_GREETER_MODE — when and where the greeter renders. Trade-off is token cost vs. Claude awareness. 'terminal' paints the banner in your shell BEFORE Claude launches via a `claude()` wrapper (zero Claude tokens, full ANSI colors, but Claude doesn't see your XP/Sensei state). 'inline' uses the SessionStart hook to inject the banner into Claude's context (~400 tok/session, monochrome since ANSI shows literal, Claude can reference your state). 'off' disables the banner everywhere."
   - Options: `terminal (Recommended)` description "Pre-launch shell wrapper — zero Claude tokens, full color. Auto-installs to ~/.zshrc / ~/.bashrc / fish config based on $SHELL." | `inline` description "SessionStart hook injection — costs ~400 tok/session but Claude sees your DoDojo state." | `off` description "No banner anywhere."

   After collecting the answer: if `terminal`, run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/dodojo-greeter-install.sh install` so the shell wrapper is added to the user's rc file. If `inline` or `off`, run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/dodojo-greeter-install.sh uninstall` to strip any prior wrapper. The hook itself reads `$DODOJO_GREETER_MODE` and self-gates — no further action needed.

5. **Enable Sensei?** — header "Coach"
   - Question: "Enable Coach (Sensei) — pattern miner that reads your shell history + git log, scores repetitive work by ROI, writes weekly markdown report. State lives at ~/.claude/dodojo/sensei/. Disable if you don't have zsh history or don't want git log mining."
   - Options: `Yes — set up paths` description "Ask follow-up questions for vault, repos, history" | `No — skip` description "Sensei stays installed but inert until env vars set later"

   If yes, follow up with three single-question prompts (each with its own `description`):

   5a. **SENSEI_VAULT** — header "Vault"
       - Question: "SENSEI_VAULT — directory where weekly-YYYY-MM-DD.md reports get written. Affects only Sensei output. Use an Obsidian vault path for auto-indexed notes, or any plain folder."
       - Options: `~/Documents/Obsidian Vault/Sensei (Recommended)` description "Standard Obsidian vault location — auto-indexed in Obsidian"
       - User picks Other to type custom path.

   5b. **SENSEI_REPOS** — header "Repos"
       - Question: "SENSEI_REPOS — repo roots to scan with `git log` for commit-pattern, repo-focus, and PR-gap detectors. Affects WHICH repos contribute to recommendations. Sensei walks maxdepth 4 inside each root to find `.git` dirs."
       - Options: `~/Development (Recommended)` description "Default — single root covers most personal projects"
       - User picks Other to type colon-separated list (e.g. `~/Development:~/work:/warehouse/server/compose`).

   5c. **SENSEI_HISTORY** — header "History"
       - Question: "SENSEI_HISTORY — shell history file for command-frequency mining. Affects the zsh-command detector. Point to ~/.bash_history if you use bash; missing file = detector silently skipped."
       - Options: `~/.zsh_history (Recommended)` description "Default — zsh extended history with timestamps"
       - User picks Other for custom path.

6. **DODOJO_DATA** — header "Data dir"
   - Question: "DODOJO_DATA — root directory where greeter + hooks read/write state (memory dir, sessions JSONL, alerts, XP queue). Affects ALL DoDojo data location. Override only if you want isolated state (portable install)."
   - Options: `Keep ~/.claude (Recommended)` description "Shared with Claude Code's standard dir — everything in one place" | `Custom path` description "Isolate DoDojo state to a different dir (e.g. ~/dodojo-data)"

## Writing answers

After collecting all answers, write to `~/.claude/settings.json` by running this Python via Bash:

```bash
python3 <<'PY'
import json, os
p = os.path.expanduser("~/.claude/settings.json")
with open(p) as f: s = json.load(f)
env = s.setdefault("env", {})
# replace the dict literal below with collected answers, omitting any user skipped
env.update({
  "KAGAMI_THEME": "...",
  "KAGAMI_ICONS": "...",
  "KAGAMI_COLOR": "...",
  "DODOJO_GREETER_MODE": "...",
  "SENSEI_VAULT": "...",
  "SENSEI_REPOS": "...",
  "SENSEI_HISTORY": "...",
})
with open(p, "w") as f: json.dump(s, f, indent=2)
print("Wrote env keys:", sorted(env))
PY
```

If user enabled Sensei: also `mkdir -p "$SENSEI_VAULT"`.

## Final output

Print resolved env block (`bash ${CLAUDE_PLUGIN_ROOT}/scripts/dodojo-init.sh --print`).

Then run companion plugin audit (read-only, advisory):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/companions-audit.py
```

This surfaces which of `caveman`, `claude-mem`, `pokemon-buddy-claude` are installed and prints `/plugin install ...` commands for any missing. DoDojo runs fine standalone — these are nice-to-haves.

Then remind:

> Restart Claude Code to load new settings.

## Parity with shell

`scripts/dodojo-init.sh` does the same thing without Claude (uses `select` menus + `read`). Same env vars, same target file. Use shell version for headless install / CI / scripting.
