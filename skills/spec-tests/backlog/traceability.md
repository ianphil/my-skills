# Source Traceability in Test Results

## Problem

When a spec test fails, the runner reports the test name and pass/fail status,
but doesn't consistently link back to the exact source file and line number.
In large spec suites, locating the failing test requires manual searching.

## Inspiration

Uncle Bob's empire-2025 generator embeds `army.txt:7` in every generated test
name. Any Speclj failure immediately links back to the exact acceptance test
source line. No guessing, no searching.

## Proposed Solution

Include source file path and line number in all test output:

```
FAIL  specs/tests/auth.md:23  "Valid Credentials"
      Intent: Users must be able to sign in...
      Reasoning: The implementation returns 403 instead of a session token...
```

Implementation steps:

- Track line numbers during markdown parsing in `SpecParser`
- Include `source_file` and `line_number` in the `TestCase` dataclass
- Format output as `file:line` for editor clickability (most terminals and
  editors support click-to-navigate on `path:line` patterns)

## Value

- Click-to-navigate from terminal output to the failing spec
- Faster debugging in large test suites
- Consistent with how compilers and linters report errors

## Reference

- [Uncle Bob's Acceptance Tests README](https://github.com/unclebob/empire-2025/blob/master/acceptanceTests/README.md) — generated test names include `filename:line` for traceability
