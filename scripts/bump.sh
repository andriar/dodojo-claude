#!/usr/bin/env bash
# bump version across plugin.json + marketplace.json (both `metadata.version`
# and `plugins[].version`), commit, and tag.
#
# Usage:  scripts/bump.sh <new-version>          # e.g. 0.2.4
#         scripts/bump.sh <new-version> --no-tag # skip git tag
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <new-version> [--no-tag]" >&2
  exit 1
fi

NEW="$1"
NO_TAG=0
[ "${2:-}" = "--no-tag" ] && NO_TAG=1

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
