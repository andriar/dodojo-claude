---
name: security → hard
description: Security review / threat modeling / auth flow design
type: routing
pattern: \b(security review|threat model|auth flow|authz|cryptograph|exploit|vulnerab|sql injection|xss|csrf|owasp)\b
verdict: hard
why: Security gaps compound. Worth opus's reasoning depth + slower output. Cheap-model misses are expensive in prod.
---

Does NOT match casual "is this safe?" — only explicit security-domain language.
