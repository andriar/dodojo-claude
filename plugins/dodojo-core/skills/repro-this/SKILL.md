---
name: repro-this
description: Convert error stack trace + payload + env into minimal reproduction test file at test/repro/<bug-id>.test.ts. Auto-detect framework (vitest/jest), identify failing function from stack, generate minimal arrange-act-assert. Use when user pastes stack trace, says "repro this bug", "buatkan test untuk error ini", or has a Sentry/log error to investigate.
domain: general
category: generate
---

# Repro This

Bug → minimal reproduction test. Tools: bukan dokumentasi, bukan fix — capture aja jadi test failing.

## Inputs (yg user bisa kasih)

1. **Stack trace** — dari error message / Sentry / logs
2. **Payload** — request body / function args / state snapshot
3. **Env** — node version, dependency versions, browser (kalau frontend)
4. **Expected vs actual** — apa yg user expect vs apa yang terjadi

## Steps

### 1. Parse stack trace
- Extract top frame (terdekat ke source code, ignore node_modules)
- Identify file + line + function name
- Read 20 baris surrounding context

### 2. Detect test framework
```bash
grep -lE '"(vitest|jest|mocha|tape)"' package.json
test -f vitest.config.ts && echo vitest
test -f jest.config.* && echo jest
```

### 3. Find existing test for affected file
```bash
# convention: foo.ts → foo.test.ts / foo.spec.ts / __tests__/foo.test.ts
find . -name "$(basename $file .ts).test.*" -o -name "$(basename $file .ts).spec.*"
```

### 4. Generate repro test
File: `test/repro/<short-bug-id>-<date>.test.ts` (atau `__tests__/repro/...`)
Template:

```ts
import { describe, it, expect } from 'vitest'
import { <fn> } from '<module>'

// Repro: <one-line summary>
// Stack: <top frame>
// Reported: YYYY-MM-DD by <user>
// Expected: <expected behavior>
// Actual: <actual behavior + error message>
//
// Payload (sanitized):
const payload = { /* ... */ }
const env = { /* node v, deps */ }

describe.skip('repro: <bug-id>', () => {
  it('should not throw on <input shape>', () => {
    // Arrange
    const input = payload
    // Act
    const act = () => <fn>(input)
    // Assert (currently failing — keep skip until fix)
    expect(act).not.toThrow()
  })
})
```

### 5. Sanitize payload
Strip sensitive fields: email, token, password, phone, credit card. Replace dengan placeholder (`<email>`, `<token>`).

### 6. Output
- Write file ke `test/repro/...`
- Print path + 1 baris cmd untuk verify: `npx vitest run test/repro/<file>`
- Suggest: rename to descriptive name once fixed, remove `.skip`

## Boundaries

- **`describe.skip` default** — bug tidak di-fix di sini, hanya captured. Unblock test suite.
- **Sanitize sensitive data** — refuse generate kalau payload mengandung credit card / live token.
- **Tidak fix bug** — explicit scope: capture only. User invoke fix flow terpisah.
- **Repo format match**: cek apakah pakai `vitest` / `jest` / lainnya. Generate sesuai.

## Why

Bug datang acak: kadang dari Sentry, kadang dari user report, kadang dari production log. Tanpa repro, debug = guessing. Dengan repro test:
- 1x capture, replay infinite (regression covered)
- AI/manusia bisa bisect dengan deterministic input
- Fix verifiable: skip → unskip = green

## How to Apply

User paste stack trace → invoke skill → file dibuat → verify failing → tinggal fix di branch terpisah, hapus `.skip`. Reduce: "wah error apa ya?" → struktur kerja yg jelas.
