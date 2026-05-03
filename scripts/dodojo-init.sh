#!/usr/bin/env bash
# Interactive setup wizard for DoDojo. Writes env vars to ~/.claude/settings.json.
# Same vars are presented by /dodojo:init slash command (Claude AskUserQuestion).
#
# Usage:
#   scripts/dodojo-init.sh          # interactive
#   scripts/dodojo-init.sh --print  # show resolved values + exit (no write)
#   scripts/dodojo-init.sh --reset  # remove all DODOJO_* and KAGAMI_* and SENSEI_* env keys

set -euo pipefail

SETTINGS="${HOME}/.claude/settings.json"
PRINT_ONLY=0
RESET=0
[ "${1:-}" = "--print" ] && PRINT_ONLY=1
[ "${1:-}" = "--reset" ] && RESET=1

cyan() { printf '\033[36m%s\033[0m\n' "$*"; }
dim()  { printf '\033[2m%s\033[0m\n' "$*"; }
warn() { printf '\033[33m%s\033[0m\n' "$*" >&2; }

ensure_settings() {
  mkdir -p "$(dirname "$SETTINGS")"
  [ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
}

# Merge a single key=value into settings.json env block
write_env() {
  local key="$1"; local val="$2"
  python3 - "$SETTINGS" "$key" "$val" <<'PY'
import json, sys
path, key, val = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f: s = json.load(f)
s.setdefault("env", {})[key] = val
with open(path, "w") as f: json.dump(s, f, indent=2)
PY
}

reset_env() {
  python3 - "$SETTINGS" <<'PY'
import json, sys
path = sys.argv[1]
with open(path) as f: s = json.load(f)
env = s.get("env", {})
removed = [k for k in list(env) if k.startswith(("DODOJO_", "KAGAMI_", "SENSEI_"))]
for k in removed: env.pop(k, None)
s["env"] = env
with open(path, "w") as f: json.dump(s, f, indent=2)
print("Removed:", removed)
PY
}

print_current() {
  python3 - "$SETTINGS" <<'PY'
import json, sys
with open(sys.argv[1]) as f: s = json.load(f)
env = s.get("env", {})
keys = sorted(k for k in env if k.startswith(("DODOJO_", "KAGAMI_", "SENSEI_")))
if not keys: print("(no DoDojo env set)"); sys.exit()
for k in keys: print(f"{k}={env[k]}")
PY
}

# Interactive picker: $1=label, $2=default, $3=help, rest=options
pick() {
  local label="$1"; local default="$2"; local help="$3"; shift 3
  local options=("$@")
  echo
  cyan "▸ $label"
  dim  "  $help"
  PS3="  Choose [default=$default]: "
  select opt in "${options[@]}" "(custom)" "(skip / keep default)"; do
    case "$opt" in
      "")              warn "Invalid choice"; continue ;;
      "(skip / keep default)") echo "$default"; return ;;
      "(custom)")      read -rp "  Enter custom value: " custom; echo "$custom"; return ;;
      *)               echo "$opt"; return ;;
    esac
  done
}

# Yes/no prompt with help text
yn() {
  local label="$1"; local default="$2"; local help="$3"
  local prompt="[Y/n]"; [ "$default" = "0" ] && prompt="[y/N]"
  echo
  cyan "▸ $label"
  dim  "  $help"
  read -rp "  $prompt " ans
  case "${ans:-x}" in
    [Yy]*) echo 1 ;;
    [Nn]*) echo 0 ;;
    *) echo "$default" ;;
  esac
}

read_path() {
  local label="$1"; local default="$2"; local help="$3"
  echo
  cyan "▸ $label"
  dim  "  $help"
  read -rp "  [$default]: " val
  echo "${val:-$default}"
}

ensure_settings

if [ "$RESET" -eq 1 ]; then
  reset_env
  INSTALLER="$(dirname "$0")/dodojo-greeter-install.sh"
  [ -x "$INSTALLER" ] && "$INSTALLER" uninstall >/dev/null 2>&1 || true
  exit 0
fi

if [ "$PRINT_ONLY" -eq 1 ]; then
  print_current; exit 0
fi

cyan "DoDojo setup — writes to $SETTINGS"
dim "Press Enter at any prompt to keep default. Ctrl-C to abort."

# 1. Theme
THEME=$(pick "KAGAMI_THEME — greeter banner color palette" "default" \
  "Affects: SessionStart banner colors only (divider, accent, success/warn/crit). Code/tool output unaffected. 20 themes total — popular ones first, type any other name via (custom)." \
  "default" "dracula" "catppuccin" "nord" "gruvbox" "monokai" \
  "pastel" "sakura" "kawaii" "frieren" \
  "neon" "retro" "mono" \
  "shounen" "ghibli" "mecha" "evangelion" "jjk" "aot" "madoka")
[ -n "$THEME" ] && write_env "KAGAMI_THEME" "$THEME"

# 2. Icons
ICONS=$(pick "KAGAMI_ICONS — icon set used in greeter sections" "nerd" \
  "Affects: SessionStart banner icons only (memory/sensei/xp/alerts markers). nerd = Nerd Font glyphs (best look, needs patched font). unicode = box-drawing fallback. emoji = full-width emoji (wide terminals)." \
  "nerd" "unicode" "emoji")
[ -n "$ICONS" ] && write_env "KAGAMI_ICONS" "$ICONS"

# 3. Color
COLOR=$(yn "KAGAMI_COLOR — ANSI color codes in greeter?" "1" \
  "Affects: SessionStart banner only. Disable (0) for narrow terminals or terminals without true-color. Code, diffs, prompt UI use Claude Code's own coloring regardless.")
write_env "KAGAMI_COLOR" "$COLOR"

# 4. Greeter mode (replaces legacy KAGAMI_SILENT)
GREETER_MODE=$(pick "DODOJO_GREETER_MODE — when/where the greeter renders" "terminal" \
  "Affects: token cost + when banner shows. terminal = paint terminal BEFORE Claude launches via shell wrapper (zero Claude tokens, full ANSI colors, recommended). inline = SessionStart hook injects banner into Claude's context (~400 tok/session, monochrome, Claude can reference your state). off = no banner anywhere." \
  "terminal" "inline" "off")
write_env "DODOJO_GREETER_MODE" "$GREETER_MODE"

# Install/uninstall the shell wrapper to match chosen mode.
INSTALLER="$(dirname "$0")/dodojo-greeter-install.sh"
if [ -x "$INSTALLER" ]; then
  if [ "$GREETER_MODE" = "terminal" ]; then
    "$INSTALLER" install || warn "Greeter wrapper install failed — paint banner manually with: python3 $(dirname "$0")/../hooks/dodojo-greet.py"
  else
    "$INSTALLER" uninstall >/dev/null 2>&1 || true
  fi
fi

# 5. Sensei (opt-in)
echo
cyan "═══ Coach (Sensei) — pattern miner + ROI advisor ═══"
dim  "Sensei reads your shell history + git log to detect repetitive work, scores by ROI,"
dim  "writes weekly markdown report. Disabled if you skip env setup. State (weights, decisions)"
dim  "lives at ~/.claude/dodojo/sensei/ — never in plugin cache."
ENABLE_SENSEI=$(yn "Enable Sensei?" "1" "If no, the /sensei command stays available but reports nothing useful until env vars set later.")
if [ "$ENABLE_SENSEI" = "1" ]; then
  VAULT=$(read_path "SENSEI_VAULT — output dir for weekly markdown" "$HOME/Documents/Obsidian Vault/Sensei" \
    "Affects: where weekly-YYYY-MM-DD.md files land. Use Obsidian vault path for auto-indexed notes, OR any plain folder if you don't use Obsidian.")
  write_env "SENSEI_VAULT" "$VAULT"
  mkdir -p "$VAULT" && dim "  created $VAULT"

  REPOS=$(read_path "SENSEI_REPOS — repo roots to scan with git log" "$HOME/Development" \
    "Affects: which git repos feed commit-pattern + repo-focus + PR-gap detectors. Multiple roots = colon-separated (e.g. ~/Development:/warehouse/server/compose). Sensei walks maxdepth 4 to find .git dirs.")
  write_env "SENSEI_REPOS" "$REPOS"

  HISTORY=$(read_path "SENSEI_HISTORY — shell history file for command-frequency mining" "$HOME/.zsh_history" \
    "Affects: which file feeds the zsh-command detector. Point to ~/.bash_history if you use bash. Missing file = zsh detector silently skipped.")
  [ -f "$HISTORY" ] || warn "  Warning: $HISTORY does not exist (Sensei skips shell-cmd detector until you set this)"
  write_env "SENSEI_HISTORY" "$HISTORY"
fi

# 6. DODOJO_DATA (rarely changed)
echo
cyan "▸ DODOJO_DATA — root for memory/sessions/alerts/xp data"
dim  "  Affects: where greeter + hooks read/write state (memory dir, sessions JSONL, alerts.jsonl,"
dim  "  buddy-xp queue). Default = ~/.claude (shared with Claude Code). Override only if you want"
dim  "  DoDojo state isolated to a different dir (e.g. portable install on USB)."
read -rp "  Override path? (leave blank to keep ~/.claude default): " DD
[ -n "$DD" ] && write_env "DODOJO_DATA" "$DD"

echo
cyan "✓ Wrote env to $SETTINGS"
print_current

# 7. Companion plugins audit (read-only, advisory)
AUDIT="$(dirname "$0")/companions-audit.py"
if [ -x "$AUDIT" ] || [ -f "$AUDIT" ]; then
  echo
  python3 "$AUDIT" || true
fi

echo
dim "Restart Claude Code to load new settings."
