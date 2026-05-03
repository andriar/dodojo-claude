#!/usr/bin/env bash
# Bump version across plugin.json + marketplace.json (metadata + plugins[]),
# commit, tag, AND sync the local Claude Code plugin install so the new
# version is immediately usable without `/plugin marketplace update`.
#
# Sync steps (skipped with --no-sync, or auto-skipped if dirs absent):
#   1. git -C ~/.claude/plugins/marketplaces/<mkt> fetch + reset --hard
#      origin/main      (origin should point to this repo for dev workflow)
#   2. Clone fresh cache dir at ~/.claude/plugins/cache/<mkt>/<plugin>/<NEW>/
#   3. Update installed_plugins.json pin (installPath + version)
#
# This kills the recurring "marketplace pin != installed pin → cache nuke
# at session start" trap during dev iteration.
#
# Usage:
#   scripts/bump.sh <new-version>            # bump + commit + tag + sync
#   scripts/bump.sh <new-version> --no-tag   # skip git tag
#   scripts/bump.sh <new-version> --no-sync  # skip plugin install sync
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <new-version> [--no-tag] [--no-sync]" >&2
  exit 1
fi

NEW="$1"; shift
NO_TAG=0; NO_SYNC=0
for arg in "$@"; do
  case "$arg" in
    --no-tag)  NO_TAG=1 ;;
    --no-sync) NO_SYNC=1 ;;
    *) echo "Unknown flag: $arg" >&2; exit 1 ;;
  esac
done

if ! [[ "$NEW" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must be semver MAJOR.MINOR.PATCH (got: $NEW)" >&2
  exit 1
fi

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$REPO/.claude-plugin/plugin.json"
MARKET="$REPO/.claude-plugin/marketplace.json"

OLD=$(python3 -c "import json; print(json.load(open('$PLUGIN'))['version'])")
echo "Bumping $OLD → $NEW"

python3 - "$NEW" "$PLUGIN" "$MARKET" <<'PY'
import json, sys
new, plugin_path, market_path = sys.argv[1], sys.argv[2], sys.argv[3]

with open(plugin_path) as f:
    p = json.load(f)
p["version"] = new
with open(plugin_path, "w") as f:
    json.dump(p, f, indent=2)
    f.write("\n")

with open(market_path) as f:
    m = json.load(f)
m.setdefault("metadata", {})["version"] = new
for plug in m.get("plugins", []):
    plug["version"] = new
with open(market_path, "w") as f:
    json.dump(m, f, indent=2)
    f.write("\n")
PY

cd "$REPO"
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "Release v$NEW"

if [ "$NO_TAG" -eq 0 ]; then
  git tag "v$NEW"
  echo "Tag v$NEW created. Push with: git push && git push --tags"
else
  echo "Skipped tag. Push with: git push"
fi

# ---------- Sync local Claude Code install ----------
if [ "$NO_SYNC" -eq 1 ]; then
  echo "Skipped plugin install sync (--no-sync)."
  exit 0
fi

MKT_NAME=$(python3 -c "import json; print(json.load(open('$MARKET'))['name'])")
PLUG_NAME=$(python3 -c "import json; print(json.load(open('$PLUGIN'))['name'])")
PLUG_BASE="$HOME/.claude/plugins"
MKT_DIR="$PLUG_BASE/marketplaces/$MKT_NAME"
CACHE_DIR="$PLUG_BASE/cache/$MKT_NAME/$PLUG_NAME"
INSTALLED="$PLUG_BASE/installed_plugins.json"

if [ ! -d "$MKT_DIR" ] && [ ! -d "$CACHE_DIR" ] && [ ! -f "$INSTALLED" ]; then
  echo "No local Claude Code install detected — skipping sync."
  exit 0
fi

echo
echo "═══ Syncing local Claude Code install to v$NEW ═══"

# 1. Sync marketplace clone
if [ -d "$MKT_DIR" ]; then
  if git -C "$MKT_DIR" remote get-url origin >/dev/null 2>&1; then
    git -C "$MKT_DIR" fetch origin --tags --quiet
    git -C "$MKT_DIR" reset --hard origin/main --quiet
    echo "✓ marketplace clone @ $(git -C "$MKT_DIR" rev-parse --short HEAD)"
  else
    echo "⚠ marketplace dir exists but no origin remote — skip"
  fi
else
  echo "· marketplace dir absent — skip"
fi

# 2. Rebuild cache dir at new version
if [ -d "$(dirname "$CACHE_DIR")" ] || [ -d "$MKT_DIR" ]; then
  mkdir -p "$CACHE_DIR"
  rm -rf "$CACHE_DIR/$NEW"
  SRC="${MKT_DIR:-$REPO}"
  [ -d "$MKT_DIR" ] || SRC="$REPO"
  git clone --quiet "$SRC" "$CACHE_DIR/$NEW"
  echo "✓ cache rebuilt: $CACHE_DIR/$NEW"
fi

# 3. Update installed_plugins.json pin
if [ -f "$INSTALLED" ]; then
  python3 - "$INSTALLED" "$MKT_NAME" "$PLUG_NAME" "$NEW" "$CACHE_DIR/$NEW" <<'PY'
import json, sys, datetime
inst, mkt, plug, new, path = sys.argv[1:6]
with open(inst) as f: s = json.load(f)
key = f"{plug}@{mkt}"
if key in s.get("plugins", {}):
    arr = s["plugins"][key]
    if arr:
        arr[0]["installPath"] = path
        arr[0]["version"] = new
        arr[0]["lastUpdated"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        with open(inst, "w") as f: json.dump(s, f, indent=2)
        print(f"✓ installed_plugins pin → {new} ({path})")
    else:
        print("⚠ installed_plugins entry empty — skip")
else:
    print(f"· {key} not in installed_plugins.json — skip")
PY
fi

echo
echo "Plugin synced. Reload in Claude Code: /reload-plugins"
