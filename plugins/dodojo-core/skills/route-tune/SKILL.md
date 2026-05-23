---
name: route-tune
description: Audit model-route hook decisions and tune routing rules. Mines ~/.claude/hooks/model-route.log to find mis-routes, dead rules, and missing patterns. Use when user asks "tune routing", "audit model-route", "why did route pick X", "review routing rules", or after a few weeks of hook usage.
domain: meta
category: ops
---

# route-tune

Audit + refine routing rules consumed by the `model-route` hook.

## When to invoke

- User asks "tune model routing", "audit model-route", "review routing rules"
- After 1-2 weeks of `model-route` log accumulation
- User notices wrong verdict ("this was trivial but got hard")
- Sensei weekly review surfaces routing as a tuning candidate

## What to do

### 1. Pull the log

```bash
LOG=~/.claude/hooks/model-route.log
[ -f "$LOG" ] || { echo "no log yet — hook not fired"; exit 0; }
wc -l "$LOG"
```

If <50 lines: not enough signal, ask user to come back later.

### 2. Verdict distribution

```bash
jq -r '.verdict' "$LOG" | sort | uniq -c | sort -rn
jq -r '.source'  "$LOG" | sort | uniq -c | sort -rn
```

Healthy distribution (rough): 30-50% medium, 20-40% trivial, 10-30% hard. Lots of `len-default` / `default` → rules under-cover the user's actual prompt shapes.

### 3. Find dead rules (plugin defaults that never fire)

```bash
ls ${CLAUDE_PLUGIN_ROOT}/routing/*.md | xargs -n1 basename
jq -r '.source' "$LOG" | grep -oE '[a-z_]+\.md' | sort -u
# diff: rules in plugin not in log = dead
```

If a plugin rule has zero matches in 60 days → propose archiving (don't auto-delete; user might rely on it sporadically).

### 4. Detect mis-routes

Cross-reference with claude-mem timeline + git log:

- Prompt classified `trivial` but session ended with a multi-file commit → likely under-routed
- Prompt classified `hard` but only 1 file touched, <5 tool calls → over-routed

Output: top 5 mis-route candidates with prompt heads. Ask user to confirm before writing new rules.

### 5. Propose new rules

For repeating prompt shapes that hit `len-default` / `default`:

1. Cluster by 2-3-gram overlap on `prompt_head`
2. For each cluster ≥5 hits, draft a rule:

```markdown
---
name: <auto-id>
description: <inferred from cluster>
type: routing
pattern: <regex from common tokens>
verdict: <inferred from work pattern>
why: Auto-mined from N hits in last M days
---
```

3. Write to `~/.claude/memory/routing/` (user override, never plugin defaults).

### 6. Show user the diff

Always print proposed rules + ask confirmation before writing. Routing changes affect every prompt — user should approve.

## Output format

```
Route-tune report (logfile: N entries, M days)

Verdict mix: trivial=X% medium=Y% hard=Z%
Top sources:
  - rule_a.md  120 hits
  - len-default 80 hits ⚠ under-covered
  ...

Mis-routes (need review):
  - "<prompt head>"  verdict=trivial, but 6 files touched
  ...

Dead rules (zero hits, 60+ days):
  - foo_bar.md ⚠ archive candidate

Proposed new rules:
  [diff blocks]

Apply? (y/N)
```

## Pair with

- `dodojo:sensei` — weekly mining, surfaces routing as a tuning track
- `dodojo:memory-curator` — archives stale rules
- `claude-mem:timeline-report` — cross-reference outcomes per verdict
