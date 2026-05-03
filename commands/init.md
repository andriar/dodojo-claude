---
description: Interactive DoDojo setup — pick theme, icons, color, Coach (Sensei) paths. Writes to ~/.claude/settings.json.
argument-hint: "[--reset | --print]"
---

# /dodojo:init

You are running the DoDojo setup wizard. Goal: collect 6 user preferences via `AskUserQuestion`, then write each to the user's `~/.claude/settings.json` `env` block.

## Behavior

If user passed `--print`: run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/dodojo-init.sh --print` and exit.
If user passed `--reset`: run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/dodojo-init.sh --reset` and exit.

Otherwise, ask the questions below **one at a time** (or batched 2-3 at once where independent), then write the answers.

## Questions

1. **Theme** (KAGAMI_THEME) — header "Theme"
   - Options (4 max per AskUserQuestion call): pick a popular default + offer "Other" for full list (20 themes total: default, pastel, neon, retro, mono, dracula, gruvbox, catppuccin, nord, monokai, sakura, shounen, ghibli, mecha, kawaii, evangelion, jjk, aot, frieren, madoka).
   - Recommended: `default` (Recommended) | `dracula` | `catppuccin` | `nord`
2. **Icons** (KAGAMI_ICONS) — header "Icons"
   - Recommended: `nerd` (Recommended) | `unicode` | `emoji`
3. **ANSI color** (KAGAMI_COLOR) — header "Color"
   - `Yes` (=1) | `No` (=0, recommended for narrow terminals)
4. **Silent mode** (KAGAMI_SILENT) — header "Silent"
   - `No, inject greeter context` (=0, default) | `Yes, terminal-only (save ~400 tok/session)` (=1)
5. **Enable Coach (Sensei)?** — header "Coach"
   - `Yes — set up paths now` | `No — skip, set later`
   - If yes, follow up with three free-text inputs (use AskUserQuestion with single-option "default" + "Other"):
     - SENSEI_VAULT (default: `~/Documents/Obsidian Vault/Sensei`)
     - SENSEI_REPOS (default: `~/Development`, colon-separated for multiple)
     - SENSEI_HISTORY (default: `~/.zsh_history`)
6. **Override DODOJO_DATA?** — header "Data dir"
   - `No — keep ~/.claude default` (recommended) | `Yes — pick custom`

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
  "KAGAMI_SILENT": "...",
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

Print resolved env block (`bash ${CLAUDE_PLUGIN_ROOT}/scripts/dodojo-init.sh --print`) and remind:

> Restart Claude Code to load new settings.

## Parity with shell

`scripts/dodojo-init.sh` does the same thing without Claude (uses `select` menus + `read`). Same env vars, same target file. Use shell version for headless install / CI / scripting.
