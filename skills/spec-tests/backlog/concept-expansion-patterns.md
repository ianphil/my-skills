# High-Level Concept Expansion Patterns

## Problem

Test authors often need to set up common preconditions (authenticated user,
database seeded, server running) that expand into multiple implementation
steps. Without guidance, authors either write too much implementation detail
in their specs or too little context for the judge to evaluate properly.

## Inspiration

Uncle Bob's empire-2025 defines high-level concepts that silently expand into
multiple setup steps. `GIVEN A is waiting for input` expands to 5+ lines:
set mode awake, build player map, set player items, process items batch. The
test author writes intent, the compiler handles mechanics.

## Proposed Solution

Document a catalog of reusable "concept patterns" that spec-test authors can
use, knowing the LLM judge understands their expansion:

### Common Patterns

```markdown
### Pattern: Authenticated User
Given an authenticated user with role "admin"
→ Judge understands: valid session, proper role assignment, middleware passes

### Pattern: Seeded Database
Given a database with standard test fixtures
→ Judge understands: schema applied, seed data loaded, connections available

### Pattern: Clean State
Given a fresh application state
→ Judge understands: no prior state, default configuration, no side effects
```

### Implementation

- Add a `patterns:` section to frontmatter or a separate `patterns.md` file
  per project
- The runner includes pattern definitions in the judge prompt context
- Authors reference patterns by name; the judge evaluates against the expansion

```yaml
---
target: src/auth.py
patterns: specs/patterns.md
---
```

## Value

- Consistent setup language across a test suite
- Less boilerplate in individual test files
- Judge has explicit expansion context for accurate evaluation

## Reference

- [Uncle Bob's Acceptance Tests README](https://github.com/unclebob/empire-2025/blob/master/acceptanceTests/README.md) — `GIVEN A is waiting for input` silently expands to multi-step setup
