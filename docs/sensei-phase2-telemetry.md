# Sensei Phase 2: Telemetry Schema & Pattern Analysis

## Telemetry Data Collection

**Location:** `~/.claude/sensei/telemetry.jsonl`

Each line = one prompt + response cycle.

### Schema

```json
{
  "timestamp": "2026-05-04T16:30:00Z",
  "session_id": "0177e4aa-dd5a-44c2-8400-4c7cba656879",
  "prompt": {
    "text": "find all usages of X function",
    "text_length": 32,
    "category": "code-search"  // inferred: code-search, refactor, debug, explain, etc
  },
  "response": {
    "tokens_input": 2500,
    "tokens_output": 1200,
    "tokens_cache_read": 8400,
    "tokens_cache_write": 0,
    "total_cost": 0.15
  },
  "tools_used": [
    { "name": "Bash", "count": 1, "type": "search" },
    { "name": "Read", "count": 0, "type": "read" }
  ],
  "files_accessed": [
    { "path": "src/components/X.tsx", "operation": "read", "line_range": "1-50" },
    { "path": "docs/API.md", "operation": "read", "line_range": null }
  ],
  "follow_up": {
    "is_followup": false,
    "parent_prompt_id": null,
    "chain_length": 1,
    "time_since_parent_ms": null
  },
  "memory_interaction": {
    "searches": 0,
    "recall_used": false,
    "memory_created": false
  }
}
```

## Pattern Detection Rules

### 1. Repeated File Reads
```
IF file X read >3 times in same session
  AND file size > 100 lines
  AND no memory exists for X
THEN suggest: "Create memory file for X pattern, use /dodojo:recall next time"
```

**Signal:** Token waste (reading same 500-line file 3x = 1500 tokens)

---

### 2. Follow-Up Chains
```
IF prompt[N] followed by prompt[N+1] within 30s
  AND prompt[N+1] contains clarification keywords
     (what do you mean, can you explain, like this, etc)
THEN chain_length++

IF chain_length > 2 (3+ prompts to resolve)
THEN suggest: "Reframe initial prompt + provide example. Template: [X]"
```

**Signal:** Inefficient communication (could be 1 clear ask)

---

### 3. Tool Misuse
```
FOR each prompt that used tool X:
  IF equivalent cheaper tool Y exists:
    - Read file: use Bash + grep instead
    - Manual task: use existing /skill instead
    - Repeated query: use /dodojo:recall instead
THEN suggest: "Use Y instead of X. Saves ~[tokens]"
```

**Signal:** Wrong tool = extra tokens

---

### 4. Memory Gaps
```
IF prompt[N] asks "how do I X?"
  AND memory search history shows X asked before (>30d ago)
  AND no memory file created after first ask
THEN suggest: "Save answer to memory file. Reuse instead of re-asking"
```

**Signal:** Knowledge not persisted

---

### 5. Token Waste in Prompts
```
IF prompt tokens > 5000 AND output <500:
  - Likely over-context (bringing too much file)
  - Or vague prompt (needs clarification)
THEN suggest: 
  - "Use grep/search to narrow context (this prompt = 5000t, could be 500t)"
  - OR "Clarify what you need (5 follow-ups wasted 10000t total)"
```

**Signal:** Context bloat or unclear ask

---

### 6. Tool Underuse
```
IF "code review" prompt detected:
  AND /simplify skill not used in last 30d
THEN suggest: "/simplify does terse review auto. Saves time + tokens"

IF repeated explanations of same codebase:
  AND /dodojo:smart-explore not used
THEN suggest: "/smart-explore indexes codebase, reduces repeats"
```

**Signal:** Skill exists but user unaware or forgot

---

## Analysis Engine Output

**File:** `~/.claude/sensei/analysis.json` (regenerated daily)

```json
{
  "generated_at": "2026-05-04T16:30:00Z",
  "session_count": 47,
  "total_tokens_7d": 250000,
  "patterns": [
    {
      "rank": 1,
      "type": "repeated-file-reads",
      "severity": "high",
      "file": "docs/routing.md",
      "reads_count": 8,
      "tokens_wasted": 2400,
      "suggestion": "Create memory: 'DoDojo routing rules' + use /dodojo:recall instead of re-reading",
      "estimate_savings": "2400 tokens/week"
    },
    {
      "rank": 2,
      "type": "follow-up-chain",
      "severity": "medium",
      "avg_chain_length": 3.2,
      "chains_count": 12,
      "tokens_wasted": 15000,
      "suggestion": "Prompt template: 'I want to [goal]. Context: [X]. Expected format: [Y]. Examples: [Z]'",
      "estimate_savings": "~5000 tokens/week (fewer clarifications)"
    },
    {
      "rank": 3,
      "type": "tool-misuse",
      "severity": "low",
      "tool_used": "Read",
      "alternative": "Bash (grep)",
      "instances": 6,
      "tokens_wasted": 800,
      "suggestion": "For text search: use `grep` or `awk` instead of reading full file",
      "estimate_savings": "~200 tokens/week"
    }
  ],
  "adoption_tracking": {
    "previous_suggestions": [
      {
        "pattern": "memory-gap",
        "suggested": "2026-04-20",
        "user_action": "created memory file X",
        "adoption_date": "2026-04-22",
        "time_to_adopt": "2d",
        "estimated_savings": "500 tokens"
      }
    ]
  }
}
```

---

## Greeter Output (Sensei Phase 2)

Shows **1 high-severity pattern** + suggested action:

```
🔴 OPTIMIZATION: "docs/routing.md" read 8× this week
   Suggestion: Create memory file `/dodojo:recall` next time
   Savings: ~2400 tokens/week
```

---

## Command: `/dodojo:sensei`

Deep-dive report:
```
📊 SENSEI ANALYSIS (7-day window)
   Sessions: 47 | Total tokens: 250K

🔴 HIGH PRIORITY
   1. Repeated file reads (docs/routing.md × 8)
      → Create memory, save 2400t/week
   
   2. Follow-up chains (avg 3.2 prompts per task)
      → Use prompt template, save 5000t/week

🟡 MEDIUM PRIORITY
   3. Tool misuse (Read vs Bash grep)
      → Use grep for searches, save 200t/week

✅ ADOPTED (previous suggestions)
   • Memory file created (2026-04-22)
   • Savings: 500t confirmed
```

---

## Implementation Roadmap

**Phase 1 (this task):** Define schema ✓
**Phase 2:** Build telemetry hook (capture data)
**Phase 3:** Build pattern analyzer (mine patterns)
**Phase 4:** Integrate into greeter + `/dodojo:sensei`
**Phase 5:** Self-test on DoDojo sessions
