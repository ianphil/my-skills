---
name: ainotes
description: This skill should be used when the user asks to "consolidate notes", "summarize ainotes", "clean up notes", "ainotes", or wants to consolidate accumulated agent observations into a compact summary.
---

# AI Notes — Consolidate

Consolidate raw session observations from `.ainotes/log.md` into a curated `.ainotes/memory.md`.

## Workflow

1. Check if `.ainotes/` directory exists in the repo root. If not, create it with empty `memory.md`, `rules.md`, and `log.md`.
2. Read `.ainotes/log.md` — these are raw observations appended by the commit skill.
3. Read `.ainotes/memory.md` — this is the current curated memory.
4. Read `.ainotes/rules.md` — check for any rules that should be updated or deduplicated.
5. Consolidate log entries into memory:
   - Merge new observations into the appropriate section
   - Deduplicate — if a fact is already in memory, skip it
   - Merge related observations into single concise entries
   - Prune stale info that contradicts newer observations
   - Keep memory under **~200 lines** (hard limit)
5. If any log entries describe mistakes or operational lessons, ensure they're captured in `rules.md` as one-liners.
6. Write updated `memory.md`
7. Truncate `log.md` — keep only the last 10 entries as a buffer, remove everything else.

## memory.md Format

Use structured sections. Only include sections that have content:

```markdown
# AI Notes — <project name>

## Architecture
- <observation>

## Gotchas
- <observation>

## Workflows
- <observation>

## Testing
- <observation>

## Dependencies
- <observation>

## Conventions
- <observation>
```

## Rules

- Every bullet must be a **terse one-liner** — no paragraphs
- Prefer specifics over generalities (file paths, command names, exact behavior)
- If memory exceeds ~200 lines, aggressively prune least-useful entries
- Never duplicate information already in README.md or AGENTS.md
- When merging contradictory observations, keep the newer one
- Mistakes and operational lessons go in `rules.md`, not `memory.md`
