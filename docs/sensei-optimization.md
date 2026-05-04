# Sensei Phase 2: Workflow Optimization

> Smart optimization advisor that learns from your patterns and suggests improvements

## What is Sensei?

Sensei analyzes your session data (prompts, tools, files, memory usage) to find **friction points** where you're wasting time or tokens. Then recommends specific improvements you can make immediately.

**Example patterns Sensei detects:**
- You read the same file 4+ times → "Create memory file, use `/dodojo:recall` next time"
- Your prompts need 3 clarifications to resolve → "Use this prompt template instead"
- You're using the wrong tool → "Use `grep` instead of reading full file"
- You've asked this question before → "Save answer to memory, avoid re-asking"

**Output:** Specific, actionable suggestions + token savings estimates

---

## How It Works

### 1. **Telemetry Collection**

Each session captures:
- Prompts you write (category + length)
- Tokens used (input/output)
- Tools called (Bash, Read, Agent, etc)
- Files accessed (path + how many times)
- Follow-up patterns (Q→clarify→Q chains)

**Storage:** `~/.claude/sensei/telemetry.jsonl` (one record per prompt)

### 2. **Pattern Analysis**

On each SessionStart:
- Sensei analyzer parses telemetry from last 7 days
- Detects 5 pattern types (repeated reads, follow-ups, tool misuse, memory gaps, token waste)
- Ranks by severity + impact
- Saves top recommendations to `~/.claude/sensei/analysis.json`

### 3. **Display**

**In greeter (automatic):**
```
🔍 SENSEI OPTIMIZATION (last 7 sessions)

🟡 Follow Up Chain
   Clarification loops: 3.0 prompts per task
   → Structure prompts: [goal]. Context: [X]. Format: [Y]. Examples: [Z]
   💰 428 tokens/week
```

**Full report (on demand):**
```bash
python3 ~/.claude/scripts/sensei-report
```

Shows all patterns + adoption tracking.

---

## Patterns Sensei Detects

### 1. Repeated File Reads
**Signal:** Same file read 3+ times per week

**Recommendation:** Create memory file for that content

**Example:**
```
🔴 Repeated File Reads
   File: docs/routing.md (read 4× this week)
   → Create memory file for 'docs/routing.md' patterns
   💰 285 tokens/week saved
```

### 2. Follow-Up Chains
**Signal:** Prompts that need 2+ clarifications to resolve

**Recommendation:** Use better prompt structure

**Example:**
```
🟡 Follow Up Chain
   Clarification loops: 3.0 prompts per task
   → Structure: [goal]. Context: [X]. Format: [Y]. Examples: [Z]
   💰 428 tokens/week saved
```

### 3. Tool Misuse
**Signal:** Using expensive tool when cheaper alternative exists

**Recommendation:** Switch tools

**Example:**
```
🟢 Tool Misuse
   Using Read for text search
   → Use `grep` or `awk` instead
   💰 100 tokens/search saved
```

### 4. Memory Gaps
**Signal:** Asking the same question multiple times

**Recommendation:** Persist answer to memory

**Example:**
```
🟢 Memory Gap
   Question: "how do I configure routing?"
   → Save answer to memory file, reuse next time
   💰 Avoid future re-asking
```

### 5. Token Waste
**Signal:** Large prompts with small output

**Recommendation:** Narrow context or clarify ask

**Example:**
```
🟡 Token Waste
   5000 tokens input → 300 output
   → Use grep to narrow context, or clarify goal
   💰 ~80% reduction possible
```

---

## Running Sensei

### Automatic (via greeter)
Sensei runs on every SessionStart. You'll see the top pattern in your greeter output.

### Manual (full report)
```bash
python3 ~/.claude/scripts/sensei-report
```

Shows all patterns + adoption tracking (what you've fixed).

### Mark Recommendation as Adopted
When you implement a suggestion:
```bash
python3 ~/.claude/scripts/sensei-adoption.py --mark "repeated-file-reads"
```

Next report will show:
```
✅ Adopted: 1/5
```

---

## Data Collection & Privacy

**What Sensei tracks:**
- Your prompt text (first 200 chars)
- Tools you use
- File paths you access
- Token counts
- Timestamps

**What it does NOT track:**
- API keys, secrets
- Full file contents
- Authentication tokens
- Actual LLM responses

**Storage:** All data stored locally in `~/.claude/sensei/` (never uploaded)

**Control:**
- Disable by commenting out `sensei-greeter.sh` in `~/.claude/settings.json`
- Delete `~/.claude/sensei/` to clear history

---

## Integration with DoDojo + Claude Memory

Sensei complements your memory system:

| Component | Purpose | Data |
|-----------|---------|------|
| **Claude Memory** | Persistent knowledge base | Your notes, learnings, patterns |
| **Smart Context** | Injects relevant memories | Categorized memory searches |
| **Sensei** | Workflow optimization | Usage patterns → suggestions |

**Example:**
- You create memory file "Routing system" (Claude Memory)
- Smart context injects it when relevant (Smart Context)
- Sensei notices you read it 4 times → suggests using search instead (Sensei)

---

## Future: Sensei v3 (Post-M2)

Planned expansions:

1. **Git Commit Optimization**
   - Detect commits missing tests
   - Suggest test-first workflow
   - Track test coverage trends

2. **Slack Pattern Mining**
   - Detect blockers ("waiting on X" mentioned 10×/week)
   - Suggest process improvements
   - Track team velocity

3. **Cross-Role Optimization** (if multi-user)
   - PM: cycle time + blocker signals
   - QA: test flakiness + coverage gaps
   - Dev: tool usage + test habits

4. **Adoption Tracking Dashboard**
   - Visualize improvements over time
   - Compare week-over-week token savings
   - Celebrate milestones

---

## Troubleshooting

### Sensei shows "No analysis available"
- Telemetry needs time to collect (run a few sessions first)
- Check `~/.claude/sensei/telemetry.jsonl` exists

### Patterns seem off
- Sensei uses heuristics, not perfect
- Patterns improve as you gather more data
- Manual review of suggestions recommended

### Want to disable?
Edit `~/.claude/settings.json`:
```json
"SessionStart": [
  // Comment out:
  // { "command": "~/.claude/hooks/sensei-greeter.sh" }
]
```

---

## Examples: Real Sensei Sessions

### Session 1: Repeated Reads
```
User reads docs/routing.md three times in one session

Analysis:
  🟡 Repeated File Reads: docs/routing.md (3×)
     → Create memory file for routing patterns
     💰 500 tokens/week

User action:
  Creates ~/.claude/memory/routing-config.md
  Runs /dodojo:recall next time instead of re-reading

Result:
  3 × 500 tokens = 1500 tokens saved per week
```

### Session 2: Follow-Up Chains
```
User asks: "How do I implement X?"
Claude clarifies: "What framework?"
User: "React"
Claude clarifies: "Server-side or client?"
User: "Client"
(3 prompts for 1 request)

Analysis:
  🟡 Follow Up Chain: avg 3.0 prompts per task
     → Use template: [goal]. Context: [X]. Format: [Y]
     💰 400 tokens/week

User action:
  Next time: "Implement X in React client. Use hooks. Return [Y]"
  Claude answers in 1 prompt

Result:
  Saves 2 extra prompts × 500 tokens = 1000 tokens/week
```

---

## Contributing to Sensei

Found a pattern we should detect? File an issue or PR:
- Add pattern detector in `sensei-analyzer.py`
- Update `docs/sensei-optimization.md`
- Self-test on your own data
