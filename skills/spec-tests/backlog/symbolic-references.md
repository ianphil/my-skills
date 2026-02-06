# Symbolic References in Targets and Assertions

## Problem

Spec tests use literal file paths in frontmatter (`target: src/auth.py`) and
literal values in assertions. If the project restructures, paths break. If
thresholds or constants change, assertions need manual updates even when the
intent hasn't changed.

## Inspiration

Uncle Bob's empire-2025 uses referenceable cells (`=` and `%` characters in
ASCII maps) as symbolic landmarks. Tests say `THEN eventually A will be at %`
instead of `THEN A is at [3, 7]`. Tests survive map resizing because they
reference the symbol, not the coordinate.

## Proposed Solution

Support symbolic references in spec-test frontmatter and assertions:

### Path aliases in frontmatter

```yaml
---
target: src/auth.py
aliases:
  auth: src/auth.py
  session: src/session.py
---
```

### Variable references in assertions

```markdown
### Response Time Under Load

Users perceive delays over 50ms as laggy. This runs on every keystroke.

\`\`\`
Given the $auth module is loaded
When process_keystroke() is called under load
Then it completes within the threshold defined in $auth.MAX_RESPONSE_MS
\`\`\`
```

The judge prompt would resolve `$auth` to the actual file content and
`$auth.MAX_RESPONSE_MS` to the constant's value before evaluation.

## Value

- Tests are resilient to file restructuring
- Constants are defined once (in code) and referenced symbolically
- Reduces brittle hard-coded values in assertions

## Reference

- [Uncle Bob's Acceptance Tests README](https://github.com/unclebob/empire-2025/blob/master/acceptanceTests/README.md) — referenceable cells (`=`, `%`) as symbolic landmarks in map notation
