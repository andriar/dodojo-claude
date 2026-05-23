---
name: pr-describe
description: Generate Pull Request title + Summary + Test plan from current branch's git diff vs base branch. Auto-detect tests touched, infer Conventional Commits prefix from changed paths/types. Use when user asks "buatkan PR description", "draft PR body", "gh pr create" tanpa body, or finished a feature ready for PR.
domain: general
category: generate
---

# PR Describe

Bangun PR title + body dari diff branch sekarang vs base.

## Steps

### 1. Detect base branch
```bash
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
# fallback: main, master, develop (urut)
```

### 2. Collect data
```bash
BASE=$(detect_base)
git log --pretty=format:"- %s" "$BASE..HEAD"
git diff --stat "$BASE..HEAD"
git diff --name-only "$BASE..HEAD"
```

### 3. Infer Conventional Commits type
Mapping dari paths/files changed:
- `*.test.*`, `*.spec.*`, `__tests__/` → `test:`
- `*.md`, `docs/` → `docs:`
- `package.json`, `package-lock.json`, `Dockerfile`, `compose*.yml` → `chore:` or `build:`
- `.github/`, `.gitlab-ci.yml`, `Jenkinsfile` → `ci:`
- `src/components/`, `src/pages/`, `src/views/` + new files → `feat:`
- existing component edits + commit msg "fix"/"bug" → `fix:`
- `src/utils/`, refactor patterns → `refactor:`
- multi-area → use scope: `feat(checkout): ...`

### 4. Title
- ≤ 70 char
- Conventional: `<type>(<scope>): <imperative description>`
- Format example: `feat(auth): add OAuth callback handler`

### 5. Summary (1-3 bullets)
- Lead with **why** (motivation/issue), not what code does
- Diff itself shows the what; summary explains the why

### 6. Test plan (checklist)
Auto-populate berdasarkan files touched:
- Path `src/components/X.vue` → `[ ] X komponen render & interaksi`
- Path API/route → `[ ] HTTP integration test`
- DB migration → `[ ] migration up + down`
- Affected tests detected → `[ ] vitest <files> green`
- Default: `[ ] manual smoke test golden path`

## Output Format

```markdown
<type>(<scope>): <title>

## Summary
- Why: <motivation/problem>
- What: <high-level approach>
- Risk: <if any — feature flag, migration, breaking change>

## Test plan
- [ ] <auto-detected test 1>
- [ ] <auto-detected test 2>
- [ ] manual: <golden path>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Boundaries

- **Tidak otomatis run `gh pr create`** — output text saja, user copy/paste atau confirm.
- **Cek branch dulu**: jika belum push, suggest `git push -u origin <branch>`.
- **Ignore noise commits** (merge commits, "wip" commits) di summary inference, tetap di list commits.
- **Bahasa**: Indonesia atau English match dengan commit history mayoritas.

## Why

Nulis PR description manual makan 5-10 mnt + sering miss test plan. Diff sudah punya semua signal (paths, types, commit messages) — tinggal sintesa. Reduce: 5-10 mnt → 30 dtk review + edit.

## How to Apply

Trigger: user di branch siap PR, panggil "draft PR body" atau "gh pr create body". Output text untuk dipakai di `--body "$(cat <<EOF ... EOF)"` atau langsung gh.
