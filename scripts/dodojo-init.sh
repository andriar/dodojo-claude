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

# Interactive picker: $1=label, $2=default, rest=options
pick() {
  local label="$1"; local default="$2"; shift 2
  local options=("$@")
  echo
  cyan "▸ $label"
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

# Yes/no prompt
yn() {
  local label="$1"; local default="$2"  # default = 0 or 1
  local prompt="[Y/n]"; [ "$default" = "0" ] && prompt="[y/N]"
  read -rp "▸ $label $prompt " ans
  case "${ans:-x}" in
    [Yy]*) echo 1 ;;
    [Nn]*) echo 0 ;;
    *) echo "$default" ;;
  esac
}

read_path() {
  local label="$1"; local default="$2"
  read -rp "▸ $label [$default]: " val
  echo "${val:-$default}"
}

ensure_settings

if [ "$RESET" -eq 1 ]; then
  reset_env; exit 0
fi

if [ "$PRINT_ONLY" -eq 1 ]; then
  print_current; exit 0
fi

cyan "DoDojo setup — writes to $SETTINGS"
dim "Press Enter at any prompt to keep default. Ctrl-C to abort."

# 1. Theme
THEME=$(pick "Greeter theme (banner colors)" "default" \
  "default" "dracula" "catppuccin" "nord" "gruvbox" "monokai" \
  "pastel" "sakura" "kawaii" "frieren" \
  "neon" "retro" "mono" \
  "shounen" "ghibli" "mecha" "evangelion" "jjk" "aot" "madoka")
[ -n "$THEME" ] && write_env "KAGAMI_THEME" "$THEME"

# 2. Icons
ICONS=$(pick "Icon set" "nerd" "nerd" "unicode" "emoji")
[ -n "$ICONS" ] && write_env "KAGAMI_ICONS" "$ICONS"

# 3. Color
COLOR=$(yn "ANSI colors in greeter?" "1")
write_env "KAGAMI_COLOR" "$COLOR"

# 4. Silent (skip injecting greeter into Claude context)
SILENT=$(yn "Silent mode? (greeter shows in terminal but NOT injected to Claude — saves ~400 tok/session)" "0")
write_env "KAGAMI_SILENT" "$SILENT"

# 5. Sensei (opt-in)
echo
cyan "▸ Coach (Sensei) — pattern miner + ROI advisor"
ENABLE_SENSEI=$(yn "Enable Sensei?" "1")
if [ "$ENABLE_SENSEI" = "1" ]; then
  VAULT=$(read_path "Vault dir for weekly markdown report" "$HOME/Documents/Obsidian Vault/Sensei")
  write_env "SENSEI_VAULT" "$VAULT"
  mkdir -p "$VAULT" && dim "  created $VAULT"

  REPOS=$(read_path "Repo roots to scan (colon-separated for multiple)" "$HOME/Development")
  write_env "SENSEI_REPOS" "$REPOS"

  HISTORY=$(read_path "Shell history file" "$HOME/.zsh_history")
  [ -f "$HISTORY" ] || warn "  Warning: $HISTORY does not exist (Sensei skips zsh detector)"
  write_env "SENSEI_HISTORY" "$HISTORY"
fi

# 6. DODOJO_DATA (rarely changed)
echo
read -rp "▸ Override DODOJO_DATA? (default ~/.claude — leave blank to skip) " DD
[ -n "$DD" ] && write_env "DODOJO_DATA" "$DD"

echo
cyan "✓ Wrote env to $SETTINGS"
print_current
echo
dim "Restart Claude Code to load new settings."
