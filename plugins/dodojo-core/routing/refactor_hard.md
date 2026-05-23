---
name: refactor → hard
description: Refactor / architecture / redesign work needs deep reasoning
type: routing
pattern: \b(refactor|re-architect|architect|redesign|untangle|migrate.*(schema|db|api)|extract.*(module|service))\b
verdict: hard
why: Cross-file reasoning, side-effect tracking, abstraction trade-offs benefit from opus. Sonnet often misses second-order effects.
---

Triggers on architecture-shaped verbs. If user just renames a symbol → won't match (good); that's `trivial`.
