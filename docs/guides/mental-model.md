# DoDojo Mental Model — What it IS

> Understand the philosophy before using the features

## The Problem

Your Claude Code workflow bloats over time:
- You learn lessons → where do you save them?
- You discover patterns → how do you find them next time?
- You write CLAUDE.md → it grows to 500 lines
- You have 200 memory files → which ones matter?
- Your tokens drain → why?

**Without discipline:** Your setup becomes harder to maintain than the code you're building.

---

## The DoDojo Approach

**DoDojo = Discipline for your workflow**

Four core ideas:

### 1. **Mirror (Kagami) — capture what you learn**

Every session teaches you something:
- "This codebase uses X pattern"
- "This tool solves Y problem"
- "This mistake took me 3 hours to debug"

**Mirror captures these.**

Without Mirror: You re-learn the same lesson 6 months later.
With Mirror: One session, remembered forever.

**Implementation:** Files at `~/.claude/memory/` that Claude injects automatically.

---

### 2. **Coach (Sensei) — find your friction**

You have patterns:
- You ask the same question 3 times (could use memory)
- You read the same file 5 times (could use memory)
- Your prompts need 3 clarifications (could use template)
- You use the wrong tool (could use cheaper one)

**Sensei detects these patterns → suggests fixes.**

Without Sensei: You optimize blindly ("I think I should use grep").
With Sensei: You optimize by data ("You read this 5 times, try this instead").

**Implementation:** Analyzes your session history, shows recommendations.

---

### 3. **Context (Smart Retrieval) — inject what matters**

You have 100 memories. This prompt needs 2 of them.

**Smart Context finds those 2, injects them automatically.**

Without Smart Context: You copy-paste memories manually.
With Smart Context: Memories appear in your prompts transparently.

**Implementation:** Searches by domain, ranks by relevance, caps at 2 (saves tokens).

---

### 4. **Audit (Prune) — keep the system lean**

Your 100 memories have 10 you never use.

**Audit finds dead weight, archives it.**

Without Audit: System slows down, tokens wasted on irrelevant memories.
With Audit: Only useful memories remain.

**Implementation:** Scores memories (reuses + recency + size), archives low scorers.

---

## How They Work Together

```
Session 1: You discover a lesson
    ↓
Mirror: Save it (memory file)

Session 2: Similar problem appears
    ↓
Smart Context: Injects your memory automatically
    ↓
You solve it 10× faster

Session 100: You've saved 50 lessons
    ↓
Sensei: "You read docs/routing 5 times. Save it as memory?"
    ↓
Audit: "This memory not used in 3 months. Archive?"
    ↓
System stays lean, relevant memories stay, dead weight removed
```

---

## The Discipline Loop

```
Work → Learn → Remember → Optimize → Repeat
  ↑                                      ↓
  ←──────────────────────────────────────
```

1. **Work** — build something
2. **Learn** — discover a pattern
3. **Remember** — save it (Mirror)
4. **Optimize** — Sensei suggests improvements, Smart Context finds your memories
5. **Repeat** — system improves with each cycle

---

## What DoDojo is NOT

❌ **Not a replacement for documentation**
- Use memory for YOUR lessons
- Use docs for team knowledge

❌ **Not magical**
- You still write the code
- DoDojo just tracks + injects your learnings

❌ **Not a search engine**
- Smart Context injects only 2 memories
- For deep searches, use `/dodojo:recall "pattern"`

❌ **Not automated optimization**
- Sensei suggests, you decide
- You control what gets saved, archived, used

---

## Mental Model in One Sentence

> **DoDojo turns your work history into an automated knowledge system that learns from what you actually do.**

---

## Layers (Architecture)

```
Your Claude Code work
        ↓
    DoDojo
    ├─ Mirror (Memory)
    │  └─ Captures lessons automatically
    ├─ Coach (Sensei)
    │  └─ Detects friction patterns
    ├─ Context (Smart Retrieval)
    │  └─ Injects relevant knowledge
    └─ Audit (Prune)
       └─ Removes dead weight
        ↓
    Leaner, faster, smarter workflow
```

Each layer is optional:
- Use just Mirror (save lessons)
- Add Sensei (detect friction)
- Add Smart Context (auto-inject)
- Add Audit (keep lean)

---

## When You Need Each Feature

| Situation | Feature | Why |
|-----------|---------|-----|
| "I learned something important" | Mirror | Capture it |
| "I read this 5 times this week" | Sensei | Suggests memory |
| "I forgot how to do X" | Smart Context | Auto-injects your notes |
| "Why am I wasting so many tokens?" | Sensei | Detects inefficiencies |
| "This project has too many memories" | Audit | Cleans up |
| "What are my learnings?" | Mirror | Browse `~/.claude/memory/` |
| "What tool should I use?" | Smart Tips | Daily suggestions |

---

## Success Looks Like

✅ After 1 month:
- You have 20 memories (lessons captured)
- Sensei showed 3 optimization suggestions
- You adopted 1 (using memory instead of re-reading)

✅ After 3 months:
- You have 50 memories (organized by domain)
- Smart Context injects relevant memories automatically
- You're aware of your patterns (Sensei reports)

✅ After 6 months:
- New problems → you find your solution in memory
- Repeated processes → automated by Sensei suggestions
- Tokens saved → can use them for more ambitious work

---

## The DoDojo Philosophy

> **Better to have discipline and forget it than to have no discipline and remember it.**

DoDojo makes discipline automatic:
- You don't have to remember to save lessons (Mirror does)
- You don't have to manually search memories (Smart Context does)
- You don't have to decide what to optimize (Sensei suggests)
- You don't have to manually cleanup (Audit does)

---

## Next

- **Get started:** [quickstart.md](../quickstart.md)
- **All features:** [FEATURES.md](../FEATURES.md)
- **Architecture:** [phases.md](../architecture/phases.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
