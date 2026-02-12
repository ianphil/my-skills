---
name: commit
description: This skill should be used when the user asks to "commit changes", "push my code", "commit and push", "save my work", or wants to stage all changes and push to remote.
---

# Commit

Stage all changes, create a commit with a descriptive message, and push to the remote branch.

## Workflow

1. Run `git status` to review changes
2. Run `git diff` to understand what changed
3. Reflect on session — if something genuinely noteworthy was learned about the codebase, append observations to `.ainotes/log.md` (create `.ainotes/` if it doesn't exist). If `.ainotes/summary.md` doesn't exist yet, create it with a minimal `# AI Notes — <project name>` header so prime can find it immediately. **Skip if nothing new was learned.**
4. Run `git log -3 --oneline` to match commit message style
5. Stage relevant files, including `.ainotes/` if modified (prefer specific files over `git add -A`)
6. Create commit with descriptive message following repository conventions
7. Push to remote branch

## AI Notes Format

When appending to `.ainotes/log.md`, use this format:

```
## YYYY-MM-DD
- <area>: <one-line observation>
- <area>: <one-line observation>
```

Rules:
- **Terse bullets only** — one-liners, no paragraphs
- Only write if something genuinely noteworthy was learned
- Don't duplicate what's already in README.md or AGENTS.md
- Prefer specifics (file paths, commands, exact behavior) over generalities

## Commit Message Format

```
<type>: <short description>

<optional body explaining why>
```

Common types: feat, fix, chore, docs, refactor, test

## Rules

- Do NOT add Co-Authored-By, Signed-off-by, or any trailer attributions to commits