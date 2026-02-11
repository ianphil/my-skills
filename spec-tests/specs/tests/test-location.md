---
target:
  - SKILL.md
  - scripts/run_tests_claude.py
  - scripts/run_tests_opencode.py
  - scripts/run_tests_codex.py
---
# Test Location Convention

This spec verifies the test location and frontmatter target system works correctly.
Tests should live in `specs/tests/` and declare their targets via frontmatter.

---

## Error Code Consistency

### Missing Target Error Code

Users see error messages from the runner and reference the documentation to
understand them. If docs say `[missing-target]` but the runner outputs something
different, users can't correlate errors to documentation.

```
Given SKILL.md, scripts/run_tests_claude.py, scripts/run_tests_opencode.py, and scripts/run_tests_codex.py
Then all use [missing-target] as the error code for specs without target frontmatter
Because error codes must match between documentation and implementation
```

---

## Frontmatter Target

### Single Target Syntax is Documented

Users need to know how to declare a single target file. Without clear syntax,
they'll guess and get it wrong, leading to confusing errors.

```
Given the SKILL.md file
Then it shows the single target frontmatter syntax:
  ---
  target: path/to/file
  ---
Because users need a clear example to follow
```

### Array Target Syntax is Documented

Some specs test behavior that spans multiple files. Users need to know how to
declare multiple targets so the judge has full context.

```
Given the SKILL.md file
Then it shows the array target frontmatter syntax:
  ---
  target:
    - file1
    - file2
  ---
Because multi-file features need multi-file context for accurate evaluation
```

### Missing Target Causes Clear Error

If a user forgets the frontmatter, they should get a helpful error message
that tells them exactly what's wrong and how to fix it.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
When a spec file has no target: field in frontmatter
Then they exit with error containing: [missing-target]
And the error message explains how to add frontmatter
Because cryptic errors waste user time debugging the wrong thing
```

---

## Directory Convention

### Specs Live in specs/tests/

A consistent location makes specs discoverable. Users shouldn't have to hunt
for where tests live or wonder where to put new ones.

```
Given the SKILL.md file
Then it documents that spec tests live in specs/tests/
Because consistent conventions reduce cognitive load
```

### Files Named by Feature Not Target

Spec files should be named for what they test conceptually, not which file
they target. This makes the test suite readable as a feature list.

```
Given the SKILL.md file
Then it documents that spec files are named by feature/spec
And NOT named by mirroring the target file path
Because "authentication.md" is clearer than "src/auth.py.md"
```

---

## Runner Implementation

### Runner Parses Frontmatter

The runner must actually read and parse the frontmatter to extract targets.
Without this, the documented convention is just documentation with no teeth.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then all have a function that parses YAML frontmatter
And extracts the target field (string or list)
Because the runner must enforce what the docs promise
```

### Frontmatter Closing at EOF Is Accepted

Spec files sometimes end immediately after the closing `---`. If the parser
requires a trailing newline, it will ignore valid frontmatter and emit a
misleading [missing-target] error.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then their frontmatter parser accepts a closing --- delimiter at EOF
And does not treat valid frontmatter as missing-target
Because spec files may not end with a newline
```

### Runner Supports Target Override

Sometimes users need to test against a different file than the frontmatter
specifies (e.g., testing a local copy). The --target flag should override.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then the --target CLI argument is optional (not required)
And if provided, it overrides the frontmatter target
Because flexibility prevents users from editing spec files just to test locally
```
