---
name: commit
description: This skill should be used when the user asks to "commit changes", "push my code", "commit and push", "save my work", or wants to stage all changes and push to remote.
---

# Commit

Stage changes, record observations, commit, and push.

## Phase 1: Review Changes

```powershell
git status
git diff --stat
git diff
```

Understand what changed and why. This context feeds Phase 2.

## Phase 2: Write AI Notes

**This phase is mandatory.** Every commit must evaluate whether observations belong in `.ainotes/log.md`.

### Setup (first time only)

If `.ainotes/` does not exist in the repo root:

```powershell
mkdir .ainotes
```

Create `.ainotes/summary.md`:

```markdown
# AI Notes — <project name>
```

Create `.ainotes/log.md`:

```markdown
# AI Notes — Log
```

### Append Observations

Reflect on the **entire session** — not just the diff. Consider:

- Architecture patterns or gotchas discovered
- Build/test commands that aren't documented
- Surprising behavior, race conditions, edge cases
- File relationships or conventions not obvious from code
- Dependency quirks or version constraints

**Append** to `.ainotes/log.md` using this exact format:

```markdown
## YYYY-MM-DD
- <area>: <one-line observation>
- <area>: <one-line observation>
```

If today's date header already exists, append bullets under it. Otherwise create a new header.

### What NOT to write

- Anything already in `README.md` or `AGENTS.md`
- Generic statements ("the code is well-structured")
- Descriptions of what you just changed — that's what the commit message is for

### When to skip

Only skip if **genuinely nothing new was learned** in this session. This should be rare. If you touched code, you almost certainly learned something. When in doubt, write a note.

## Phase 3: Commit

```powershell
git log -3 --oneline
```

Match the existing commit style. Stage files explicitly:

```powershell
git add <changed files>
git add .ainotes/log.md          # always include if modified
git add .ainotes/summary.md      # include if created
```

Prefer `git add <file>` over `git add -A`.

Commit message format:

```
<type>: <short description>

<optional body explaining why>
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`

## Phase 4: Push

```powershell
git push
```

If push is rejected (behind remote):

```powershell
git pull --rebase
git push
```

## Rules

- Do NOT add Co-Authored-By, Signed-off-by, or any trailer attributions
- Do NOT use `git add -A` unless every changed file should be staged
- Do NOT skip Phase 2 without explicitly stating why nothing was learned
- If on `main` or `master`, warn the user before pushing