---
name: bug fix → medium
description: Localized bug fix with clear repro/error
type: routing
pattern: \b(fix\b.*\b(bug|error|crash|regression|null|exception|undefined)|debug|why (is|does) .* (fail|break|crash)|stack trace|repro|null pointer|segfault)\b
verdict: medium
why: Bounded scope — sonnet handles. Escalate to opus only if user mentions "across multiple files" or "design issue".
---

If prompt also matches `refactor → hard` (e.g. "fix this design bug") → that rule wins (loaded later or alphabetically — first match wins, refine pattern if conflicts).
