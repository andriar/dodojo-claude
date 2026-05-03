# Positioning — DoDojo in the Claude Code stack

DoDojo is one of three orthogonal token-optimization plugins. None overlap; pair freely.

## At a glance

| Plugin | Layer | Optimizes | Scope |
|--------|-------|-----------|-------|
| **caveman** | Output style | Token *spent* per response (~75% cut) | Per-turn compression |
| **claude-mem** | Session digest | Token *recall* across sessions (auto-summarize long chats) | Per-session → cross-session |
| **DoDojo** | Workflow discipline | Token *budget* + memory hygiene + routing + audit | Cross-session, cross-project |

## Mental model

- **caveman** decides *how* Claude talks (form). Strips articles, fragments OK, code untouched.
- **claude-mem** decides *what* Claude remembers (raw facts). Auto-summarizes long sessions into searchable timeline.
- **DoDojo** decides *when + why* a memory is recalled (curation). Routes prompts, prunes orphans, mines patterns, audits context.

Diagram:

```
prompt
  │
  ▼
[ DoDojo: route + smart-context inject ]   ← picks model, injects relevant memory
  │
  ▼
[ Claude responds ]
  │
  ▼
[ caveman: compress output ]               ← shrinks the response itself
  │
  ▼
session ends
  │
  ▼
[ claude-mem: digest into timeline ]       ← raw fact dump for next session
  │
  ▼
[ DoDojo: Sensei mines timeline ]          ← turns facts into ROI recommendations
```

## When to install which

| Symptom | Pick |
|---------|------|
| Responses too verbose, tokens drain mid-session | **caveman** |
| Re-explaining project context every new session | **claude-mem** |
| `~/.claude/CLAUDE.md` bloated, memory rotting, hooks unaudited | **DoDojo** |
| All three above | Install all — they don't overlap |

## How DoDojo respects the others

- **caveman compatibility**: DoDojo greeter + Sensei reports written in normal prose. caveman compresses output regardless. Code and commit messages stay literal in both.
- **claude-mem integration**: Sensei reads `claude-mem` timeline as a pattern source (auto-skipped if not installed). DoDojo's `mem-search` skill is namespace-aware.
- **No state collision**: caveman state in `~/.claude/caveman/`, claude-mem in `~/.claude/claude-mem/`, DoDojo in `~/.claude/dodojo/`.

## What DoDojo will NOT do

- Compress your responses → use caveman
- Auto-summarize long chats → use claude-mem
- Replace your IDE's linter → use IDE plugins

DoDojo focuses on **the boring discipline** that compounds over months: pruning, routing, auditing, mining. The other two handle real-time token shape.

## Related

- [sensei.md](sensei.md) — the pattern-mining subsystem inside DoDojo
- [audit.md](audit.md) + [prune.md](prune.md) — the discipline tools mentioned above
- [status.md](status.md) — what the greeter shows you each session
