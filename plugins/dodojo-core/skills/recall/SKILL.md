---
name: recall
description: Cross-silo search across memory files, session telemetry, git logs, and Obsidian vault. Use when user asks "kapan terakhir gw kerja di X", "find anything about Y", "recall", "search across everything", or wants to recover context from past work.
domain: meta
category: research
---

# recall

Unified search across 4 data silos. Solves "kapan terakhir gw X" /
"apa aja yang ada tentang Y" without manually grepping each source.

## When to invoke

- User asks "kapan terakhir gw kerja di <topic>" / "when did I last work on X"
- User asks "find anything about <topic>" / "search everything for Y"
- User says "recall" / "ingat ga..."
- User wants to recover context from past sessions
- Before starting a related task — surface prior decisions

## Sources searched

| # | Source | What's mined |
|---|--------|--------------|
| 1 | 💾 Memory | `~/.claude/memory/*.md` + `~/.claude/projects/*/memory/*.md` |
| 2 | 📊 Sessions | `~/.claude/sessions/*.jsonl` — cwd + files touched |
| 3 | 🔧 Git | logs across `~/Development` + `/warehouse/server/compose` |
| 4 | 📝 Vault | `~/Documents/Obsidian Vault/**/*.md` (excludes `Kagami/`) |

## Procedure

```bash
# Default: 7 days, all sources
python3 ~/.claude/scripts/recall.py <query>

# Extended window
python3 ~/.claude/scripts/recall.py <query> --days 30

# Restrict to specific sources
python3 ~/.claude/scripts/recall.py <query> --sources mem,git
python3 ~/.claude/scripts/recall.py <query> --sources vault

# Limit result count
python3 ~/.claude/scripts/recall.py <query> --limit 10
```

## Output

Ranked list (score DESC, ts DESC):

```
🔍 Recall results for 'vaultwarden'  (last 30d, 4 hits)
──────────────────────────────────────────────────────────────────────
💾 [ 4] 2026-05-02 14:12  automation ideas
           Ideas brainstormed 2026-05-02 for automating homelab + workstation
           ~/.claude/projects/-home-andriar/memory/automation_ideas.md

📊 [ 3] 2026-05-02 03:00  file · vault.andriar.com.yml
           touched in session abc12345
           /warehouse/server/compose/prod-vault/

🔧 [ 3] 2026-05-01 19:44  homelab · a1b2c3d
           feat(vaultwarden): enable SMTP relay
           /warehouse/server/compose/prod-vault
```

## Scoring

- Memory: token overlap × 1 + substring boost × 3
- Vault: substring × 2 + filename × 5 + token overlap
- Sessions: cwd match = 2, file path match = 3
- Git: commit msg match (case-insensitive grep)

## Tips

- Use specific keywords ("vaultwarden", "qiscus", "auth middleware")
- For broad topics → bump `--days 30` or `60`
- For files only → `--sources sessions,git`
- For docs only → `--sources mem,vault`

## Edge cases

- Empty results → suggest user widen `--days` or use simpler keywords
- Git roots not yet existing → silently skipped
- Slow on large vaults → `--sources` to restrict
- `claude-mem` MCP search complementary — use `/claude-mem:mem-search` for full conversation history (recall is faster, narrower)
