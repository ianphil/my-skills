---
name: literate-tests
description: >
  Generate literate test suites as MARKDOWN FILES with a custom test runner.
  NOT pytest/jest/etc. The markdown IS the test format. Use when creating 
  specification-as-tests for agent-driven development. Creates two artifacts:
  (1) .md test files with inline assertions, (2) a test runner that parses them.
license: MIT
metadata:
  author: Ian
  version: "2.0"
---

# Literate Test Suite Generator

Create a test suite for **[DOMAIN]** that an agent can run autonomously.

## What This Pattern Produces

> **CRITICAL:** This is NOT pytest/jest/unittest/etc. This creates a CUSTOM test format.

You will generate **two artifacts**:

### 1. Markdown Test Files (`tests/<feature>.md`)

```markdown
# Feature Name

Prose explaining what this tests and why.

## Test Group

### Specific Behavior

\`\`\`py
result = do_thing("input")
result.value  # expect: 42
\`\`\`

### Error Case  

\`\`\`py
do_thing(None)  # error: [null-input]
\`\`\`
```

The markdown file IS the test. Code blocks contain executable code. Comments are assertions.

### 2. Test Runner (`run_tests.py` or equivalent)

A script that:
1. Parses markdown files
2. Extracts code blocks
3. Executes them
4. Validates `# expect:` and `# error:` assertions
5. Reports pass/fail

**Do NOT use pytest, jest, or any standard test framework for the runner itself.**
The runner is custom code that understands this markdown format.

---

## Why This Format

Tests are the oracle for agent-driven development:
1. Agent runs `python run_tests.py`
2. Sees which assertions fail
3. Fixes the code
4. Repeats until green

The test file is both:
- **Documentation** humans can read (it's markdown!)
- **Executable specification** agents verify against

This pattern enabled Simon Willison to port an entire HTML5 parser in 4.5 hours—the agent ran 9,200 tests autonomously.

---

## File Structure

```
project/
├── src/
│   └── <module>.py           # Code under test
├── tests/
│   └── <feature>.md          # Markdown test files (NOT .py!)
└── run_tests.py              # Custom test runner
```

---

## Markdown Test File Format

### Frontmatter (Required)

Must be the FIRST thing in the file:

```toml
# Test Configuration
module = "mypackage.validator"
import = ["validate", "normalize", "ValidationError"]
isolation = "per-block"
```

### Error Code Index (Required)

List ALL error codes at the top, before any tests:

```markdown
**Error codes:**
- `[empty-input]` — User provided empty string
- `[null-input]` — User provided null/None
- `[invalid-format]` — String doesn't match expected pattern
```

### Test Sections

Headers create test groups. Prose explains intent. Code blocks are tests:

```markdown
## Input Validation

Users paste data from spreadsheets which may contain invisible whitespace.
The validator normalizes input before checking length.

### Accepts Valid Input

\`\`\`py
validate("hello")  # expect: True
\`\`\`

### Rejects Empty String

Empty means "user submitted nothing" — distinct from whitespace-only:

\`\`\`py
validate("")  # error: [empty-input]
\`\`\`
```

---

## Assertion Syntax

### Value Assertions

```py
expression  # expect: <value>
```

The line before `# expect:` must be an **evaluable expression**, not a statement.

```py
# Setup lines run first
result = calculate(10)
# This line is evaluated and compared
result.value  # expect: 42
```

### Error Assertions

```py
statement  # error: [code]
statement  # error: "message substring"  
statement  # error: [code] "message substring"
```

### Matchers

For non-exact comparisons:

```py
pi_value()  # expect: approx(3.14159, tol=0.0001)
output      # expect: contains("success")
text        # expect: matches(/^Error: \d+/)
```

### CLI/Shell Tests

```sh
mycommand --bad-flag
# exit: 1
# stderr: contains("[invalid-flag]")
```

---

## Test Runner Requirements

The runner you generate must:

1. **Parse TOML frontmatter** — Extract module, imports, isolation mode
2. **Extract code blocks** — Find ```py (or language) blocks
3. **Parse assertions** — Recognize `# expect:` and `# error:` comments
4. **Execute code** — Run each block with proper isolation
5. **Validate assertions** — Compare results, catch exceptions, check error codes
6. **Report results** — Show pass/fail with helpful messages

### Runner Skeleton (Python)

```python
#!/usr/bin/env python3
"""Literate Test Runner - parses markdown, executes code blocks, validates assertions."""

def parse_frontmatter(content: str) -> dict:
    """Extract TOML config from start of file."""
    ...

def extract_tests(content: str) -> list[TestCase]:
    """Find code blocks and their assertions."""
    ...

def run_test(test: TestCase, context: dict) -> TestResult:
    """Execute code block, validate assertions."""
    ...

def main():
    for md_file in Path("tests").glob("*.md"):
        # Parse, run, report
        ...
```

---

## Error Identity (Critical)

Every error must have a **stable code** the runner can match:

| Language | How to Expose Code |
|----------|-------------------|
| Python | Exception with `.code` property |
| Rust | Error enum variant |
| CLI | `[code]` in stderr + exit code |
| C# | Exception type name |

Example Python exception:

```python
class ValidationError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)

# Usage
raise ValidationError("empty-input", "Input cannot be empty")
```

The runner matches `# error: [empty-input]` against `exception.code`.

---

## Example: Complete Test File

```toml
# Test Configuration  
module = "temperature"
import = ["celsius_to_fahrenheit", "TemperatureError"]
isolation = "per-block"
```

# Temperature Conversion

Converts between Celsius and Fahrenheit with validation.

**Problem:** Users need temperature conversion, but invalid inputs (below 
absolute zero) must fail clearly—not return nonsense values.

**Error codes:**
- `[below-absolute-zero]` — Temperature violates laws of physics

---

## Celsius to Fahrenheit

Standard formula: `F = (C × 9/5) + 32`

### Converts Freezing Point

```py
celsius_to_fahrenheit(0)  # expect: 32.0
```

### Converts Boiling Point

```py  
celsius_to_fahrenheit(100)  # expect: 212.0
```

### Rejects Below Absolute Zero

-273.15°C is the physical limit. Below that is impossible:

```py
celsius_to_fahrenheit(-300)  # error: [below-absolute-zero]
```

---

## Checklist Before Generating

When asked to create literate tests, verify:

- [ ] Create `.md` files in `tests/`, NOT `.py` test files
- [ ] Create a custom `run_tests.py` runner, NOT pytest
- [ ] Include TOML frontmatter at top of each test file
- [ ] Include error code index before tests
- [ ] Use `# expect:` and `# error:` assertion syntax
- [ ] Prose explains WHY, not just WHAT
- [ ] One behavior per code block
- [ ] Test names are behavior descriptions

---

## Domain Spec Template

Fill in when generating:

- **What it does:** [DESCRIPTION]
- **What problem it solves:** [USER PAIN]
- **Language:** [LANGUAGE]
- **Code block tag:** [py/rs/sh/etc]
- **Comment prefix:** [#/////--]
- **Error codes:** [EXHAUSTIVE LIST]
- **Public API:** [FUNCTIONS TO TEST]
- **Happy paths:** [LIST]
- **Error cases:** [LIST + WHY]
- **Edge cases:** [LIST + WHY]