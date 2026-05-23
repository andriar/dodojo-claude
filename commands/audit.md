---
description: Audit plugin stack token cost — passive load per session, prune candidates, ranked report
---

# /dodojo:audit

Run the **plugin stack auditor**. Zero Claude tokens — executes `${CLAUDE_PLUGIN_ROOT}/bin/audit-stack.py` and prints the result.

Measures:
- Base layer cost (CLAUDE.md, @-refs, INDEX.md)
- Project layer cost (in-repo CLAUDE.md/MEMORY.md)
- Per-plugin cost (skill descriptions in system reminder)
- Cross-references `enabledPlugins` and skill-usage telemetry
- Outputs prune candidates ranked by impact

The report is written to `~/.claude/dodojo/reports/audit-stack-latest.md`.

For the old **memory audit** (context budget, orphan memories), see `/dodojo:audit-memory`.

Run from terminal directly: `dj audit`.
