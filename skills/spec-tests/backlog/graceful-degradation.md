# Graceful Degradation for Structural Issues

## Problem

When a spec test has structural problems (missing intent, malformed frontmatter,
unparseable code block), the runner can halt or produce confusing errors. Other
valid tests in the same file may not run.

## Inspiration

Uncle Bob's empire-2025 parser emits `(pending "Unrecognized: ...")` for any
directive pattern it cannot match. The test shows up as "pending" (skipped) in
the Speclj report rather than crashing the entire suite. All other tests
continue to run normally.

## Proposed Solution

Introduce a `pending` or `skipped` status alongside `pass`, `fail`, and `error`:

```
PASS  auth.md:10  "Valid Credentials"
SKIP  auth.md:23  "Expired Token" — [missing-intent] no intent statement found
FAIL  auth.md:35  "Invalid Password"

Results: 1 passed, 1 failed, 1 skipped
```

Implementation:

- Structural validation errors (`[missing-intent]`, `[missing-assertion]`,
  `[missing-target]`) produce `SKIP` instead of `FAIL`
- The test is recorded with its error code and a human-readable reason
- The suite continues running remaining tests
- Exit code reflects: 0 = all pass (skips OK), 1 = any fail, 2 = all skip

## Value

- One broken test doesn't block feedback on the rest of the suite
- Authors can iteratively fix structural issues while still getting results
- Clear distinction between "test evaluated and failed" vs "test couldn't be evaluated"

## Reference

- [Uncle Bob's Acceptance Tests README](https://github.com/unclebob/empire-2025/blob/master/acceptanceTests/README.md) — unrecognized patterns emit `(pending ...)` instead of crashing the suite
