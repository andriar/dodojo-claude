# Routing rules (plugin defaults)

Consumed by `hooks/model-route.py` (UserPromptSubmit). Each `*.md` here is a default rule shipped with DoDojo.

User overrides live at `~/.claude/memory/routing/*.md` — same filename shadows the plugin default.

## Verdict map

| Verdict | Model  | Effort | When |
|---------|--------|--------|------|
| trivial | haiku  | light  | Lookup, rename, typo, single-fact Q |
| medium  | sonnet | normal | Default — most coding work |
| hard    | opus   | deep   | Refactor, architecture, security review, multi-file design |

## Frontmatter contract

```
---
name: <id>
description: <one-line>
type: routing
pattern: <python regex, case-insensitive>
verdict: trivial|medium|hard
why: <reason — past incident or pref>
---
```

First match wins. User rules load before plugin rules; same filename shadows.

## Tuning

Hook logs every decision to `~/.claude/hooks/model-route.log` (jsonl). The `route-tune` skill mines this log to:
- Detect mis-routes (user manually `/model opus`'d after a `trivial` verdict)
- Propose new rules from repeating prompt shapes
- Flag plugin rules that never fire (override candidates)
