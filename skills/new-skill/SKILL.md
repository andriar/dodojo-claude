---
name: new-skill
description: Scaffold a new custom Claude Code skill — generates SKILL.md with required frontmatter (domain + category), creates the skill folder, and auto-registers in skills/README.md index. Use when user asks "buat skill baru", "create a new skill", "scaffold skill <name>", or wants to extract a recurring workflow into a reusable skill.
domain: meta
category: generate
---

# new-skill

Scaffold a new custom skill with valid taxonomy + auto-registration. Removes
friction so user actually creates skills instead of putting it off.

## When to invoke

- User asks "buat skill baru", "create skill", "scaffold a skill", "tambah skill"
- User describes a recurring workflow worth packaging ("I keep doing X, make a skill")
- After session where same task pattern repeated 3+ times

## Inputs required

Before running, gather from user:

1. **Name** (kebab-case, will be slugified) — what to call it
2. **Domain** — pick one: `frontend` | `backend` | `devops` | `ai-eng` | `meta` | `general`
3. **Category** — pick one: `review` | `generate` | `refactor` | `ops` | `research`
4. **Description** — one sentence ending with "Use when ..." trigger phrase
5. **Draft?** — if uncertain, scaffold under `_drafts/` (won't load until graduated)

If user vague about domain/category, infer from description and confirm with them.

## Procedure

```bash
python3 ~/.claude/scripts/new-skill.py <NAME> \
  --domain <DOMAIN> \
  --category <CATEGORY> \
  --description "<DESC>"

# Optional flags:
#   --draft        scaffold under _drafts/ (not registered, not loaded)
#   --force        overwrite if SKILL.md already exists
```

The script:
- Creates `~/.claude/skills/<name>/SKILL.md` with frontmatter + TODO template
- Inserts a row in the matching domain table in `~/.claude/skills/README.md`
- Refuses overwrite without `--force`

## Output

Path to new SKILL.md + confirmation registered. Then user fills in the TODO
sections (When to invoke, Inputs, Procedure, Output, Edge cases).

## Edge cases

- Domain not in fixed set → script rejects with valid choices listed
- Skill name collides with existing → script refuses (use `--force` only if user confirms)
- Description without "Use when ..." → still works but skill-suggest hook will be less accurate; suggest user add trigger phrases
- README missing the domain section → script warns; user adds section header manually then re-runs

## Related

- After scaffolding, edit SKILL.md to fill TODOs
- Test in fresh session: invoke via `/<name>` to confirm Claude picks it up
- Sensei detects gaps → suggest scaffolding new skills periodically
