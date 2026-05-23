---
name: audit-context
description: Audit Claude Code context budget — measure tokens loaded every session (CLAUDE.md + @-refs + project MEMORY.md), flag bloated files, cross-reference smart-context telemetry to surface orphan memories never matched. Use when user asks "audit context", "how much token is loaded", "context budget", "prune memory", or feels session feels heavy/slow.
domain: meta
category: ops
---

# audit-context

Run the context budget auditor. Reports token cost of every file Claude
Code loads on every session, plus prune candidates.

## When to invoke

- User asks: "audit context", "context budget", "how big is my CLAUDE.md", "prune memory"
- User notices session feels slow / heavy on tokens
- After adding many memories — verify INDEX.md still under budget
- Periodic hygiene (pair with Sensei weekly review)

## What to do

1. Run the auditor:

```bash
python3 ~/.claude/hooks/context-audit.py
```

2. If user wants prune candidates, add `--orphans`:

```bash
python3 ~/.claude/hooks/context-audit.py --orphans
```

3. If user wants top-N largest files:

```bash
python3 ~/.claude/hooks/context-audit.py --top 20
```

## Interpreting output

- **Total tokens**: sum of static context loaded every session. Target < 5,000 for snappy sessions.
- **% per file**: any single file > 30% is a refactor candidate.
- **Files > 8,000 tokens**: flagged automatically — split or trim.
- **Orphan memories**: zero hits in smart-context telemetry. Telemetry must have ≥20 invocations before pruning is reliable; below that, suggest waiting.

## Action recommendations to surface

- INDEX.md > 200 lines → prune entries unused 90+ days
- CLAUDE.md > 1,500 tokens → move sections to standalone @-referenced files
- README.md (skills/hooks) bloat → tighten table descriptions
- Orphan memories → improve `description:` frontmatter (so smart-context matches) or archive to `_archive/`

## Related tools

- `smart-context` hook (injects body of relevant memories on demand)
- `skill-suggest` hook (hints custom skills)
- Sensei weekly report (consume orphan list for prune recommendations)
