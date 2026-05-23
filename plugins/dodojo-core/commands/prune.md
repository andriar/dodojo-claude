---
description: Interactive cleanup of unused/disabled plugins from stack — zero tokens
---

# /dodojo:prune

Run the **interactive plugin pruner**. Zero Claude tokens — executes `${CLAUDE_PLUGIN_ROOT}/bin/prune.py` and walks each candidate with y/N/q prompts.

Safety:
- Defaults to **No** for every prompt
- Shows full `rm -rf` path before action
- Warns explicitly when target is `enabled: true`
- `--dry-run` flag previews without deleting
- Re-runs `dj audit` after if anything was deleted

For the old **memory orphan pruner**, see `/dodojo:prune-memory`.

Run from terminal: `dj prune` · `dj prune --dry-run` · `dj prune -y`.
