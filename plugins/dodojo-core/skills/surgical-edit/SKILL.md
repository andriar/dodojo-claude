---
name: surgical-edit
description: Edit huge files (>5K lines / >300KB) without burning tokens. Locate target via grep first, Read only the offset window around match, Edit in place. Avoid full-file reads and re-reads. Use when touching files like inbox.blade.php (15K lines), generated bundles, large views, or any file the user flags as "gede"/"huge".
domain: general
category: ops
---

# surgical-edit

Stop re-reading 800KB blade files every turn. Locate, window, edit.

## When to activate

- File > 5,000 lines OR > 300KB
- User says: "edit X" where X is known big file (blade, generated, fixture)
- About to call Read on file already seen this session
- About to make 2nd Edit on same big file

## Protocol

### Step 1 — Locate (Bash, not Read)

```bash
grep -n "<target>" <file>           # exact symbol/string
grep -n -A2 -B2 "<target>" <file>   # with context
```

Get line number. Skip Read entirely if grep result enough (e.g. confirming presence).

### Step 2 — Window Read

```
Read file_path=<file> offset=<line-20> limit=60
```

60 lines almost always enough. Never Read without `offset`+`limit` for big files.

### Step 3 — Edit

Edit normally. `old_string` must be unique — if grep showed 1 match, safe.

### Step 4 — Subsequent edits same file

- Same session, file untouched externally → DO NOT Read again. Edit directly using context from step 2.
- File changed externally (git pull, format-on-save) → re-Read only the changed window.
- Multiple edits scattered → batch grep first (`grep -n` all targets), then Read each window once.

## Anti-patterns (the trap that cost 1M tokens)

| Bad | Good |
|-----|------|
| `Read inbox.blade.php` (full 15K lines) | `grep -n "newMessagesCallback" → Read offset=N-20 limit=60` |
| Read full file before each Edit (15x same file) | Read window once, Edit many |
| `/clear` then resume same task | Continue session; cache stays warm |
| Edit 69x with retry-on-fail Re-read | Get unique `old_string` first try via grep context |
| One blade file 15K lines | Refactor → `@include` partials per-section (separate task) |

## Bulk operations

For mass remove/replace across big file: use `sed`/`awk` via Bash, not 50× Edit.

```bash
sed -i '/^.*debug-console.*$/d' inbox.blade.php   # remove all matching lines
sed -i 's/old-class/new-class/g' inbox.blade.php  # bulk rename
```

Verify with `git diff` after.

## Token math (why this matters)

- inbox.blade.php = 200K tokens single Read
- 15× Read same file = 3M tokens (cache_read, but still billable on creation + each turn carries it)
- Window Read (60 lines) = ~2K tokens. **100× cheaper.**

## Refactor escape hatch

If file > 10K lines AND edited >3× per week → propose splitting into partials. One-time cost, permanent savings.
