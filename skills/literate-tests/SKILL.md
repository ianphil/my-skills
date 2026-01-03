---
name: literate-tests
description: >
  Generate literate test suites that serve as both documentation and executable
  assertions. Use when creating test suites for agent-driven development, writing
  specification-as-tests, or building autonomous testing workflows. Triggers on:
  test generation requests, specification writing, agent-executable test design.
license: MIT
metadata:
  author: Ian
  version: "1.0"
---

# Literate Test Suite Generator

Create a test suite for **[DOMAIN]** that an agent can run autonomously.

## Why This Format

Tests are the oracle. An agent runs them, sees failures, fixes code, repeats. The test file is both:
- **Documentation** humans can read
- **Executable assertions** agents can verify against

---

## Runner Contract

The test runner must behave predictably. Specify these for your environment:

| Setting | Options | Your Choice |
|---------|---------|-------------|
| **Isolation** | `per-block` (fresh state each block) / `per-file` (shared within file) | [CHOICE] |
| **Execution order** | Top-to-bottom within each file | (fixed) |
| **Bootstrapping** | How code-under-test is loaded | [MODULE/IMPORT/ENTRYPOINT] |
| **Stream capture** | stdout/stderr captured per block | (fixed) |
| **Determinism** | Fixed random seed, no wall-clock dependencies | (required) |

**Determinism requirements:**
- No network calls unless explicitly mocked
- Time must be injected/frozen if tests depend on it
- Locale and timezone fixed (e.g., UTC, en-US)

**Bootstrapping example:**
```toml
# Frontmatter MUST be the first thing in the file (no blank lines before)
module = "mypackage.validator"
import = ["validate", "normalize", "ValidationError"]
```

### Block Semantics

- A code block may contain **multiple statements**
- Each block must contain **at least one assertion** (`expect:` or `error:`)
- For `error:` assertions, the failing statement must be the **last statement** in the block
- In `per-block` isolation: variables defined in a block do not carry to the next block
- In `per-file` isolation: state is shared within the file, blocks execute top-to-bottom

### Setup Blocks (Optional)

A `## Setup` section at the start of a file or group runs before each test in that scope:

```markdown
## Setup

\`\`\`py
from mymodule import Client
client = Client(test_mode=True)
\`\`\`

## Tests That Use Client

\`\`\`py
client.ping()  # expect: "pong"
\`\`\`
```

Setup blocks contain no assertions. Keep them minimal—prefer stateless tests.

---

## Assertion Syntax (Canonical)

Assertions are encoded in comments using the target language's comment prefix.

### Value Assertions

```
<expr>  <comment> expect: <value>
```

The asserted line must be an **evaluable expression** (not a statement like `x = 1`). All lines before the assertion in the same block run as setup.

**Regular comments** (not starting with `expect:` or `error:`) are allowed and ignored by the runner:

```py
# This is just a comment explaining the test
result = calculate()  # This too
result.value  # expect: 42
```

Where `<value>` is one of:
- **Primitives:** `42`, `3.14`, `true`, `false`, `null`/`None`/`nil`
- **Strings:** `"hello"` (double-quoted)
- **Language expressions:** `ErrorKind::InvalidInput`, `StatusCode.OK`

**Comparison is structural equality** (deep equals), not reference identity.

### Equality Rules

- **Primitives:** exact equality
- **Floats:** use `approx()` for tolerance; `NaN` requires explicit handling
- **Objects/structs:** compare by JSON-serializable shape or explicit projection
- **Collections:** order matters for lists/arrays; order ignored for sets; keys compared for maps/dicts

### Error Assertions

```
<statement>  <comment> error: [code]
<statement>  <comment> error: "text"
<statement>  <comment> error: [code] "text"
```

The runner executes the statement, expects it to fail, and matches:
- `[code]` — error's stable identifier (see Error Identity below)
- `"text"` — substring match against error message

### Stream/Exit Assertions (CLI/Shell)

```sh
some_command --flag
# exit: 1
# stdout: "expected output"
# stderr: "error message"
```

Stream assertions support:
- **Exact match:** `# stdout: "exact text"`
- **Contains:** `# stdout: contains("substring")`
- **Regex:** `# stderr: matches(/pattern/)`

### Matchers

| Matcher | Meaning |
|---------|---------|
| `approx(3.14159, tol=0.0001)` | Floating-point within tolerance |
| `contains("substring")` | String/output contains text |
| `matches(/regex/)` | String matches regular expression |

**Examples:**
```
pi_value()      // expect: approx(3.14159, tol=0.0001)
error.message   // expect: contains("invalid")
output          // expect: matches(/^Error: .*line \d+/)
```

---

## Error Identity (Critical)

Every error the system produces must have a **stable identifier** the runner can match against. This is non-negotiable—without it, agents will "fix" tests by changing error messages.

**Error codes are compared exactly as written** (case-sensitive).

| Language Type | How to Expose Error Code |
|---------------|-------------------------|
| **Exceptions** (Python, C#, JS) | `.code` property or exception type name |
| **Result types** (Rust, Go) | Error variant/type is the code |
| **CLI tools** | stderr includes `[code]`, plus exit code |
| **Return values** (C) | Document sentinel values as codes |

**Requirement:** The domain spec must list ALL error codes exhaustively.

---

## Language Profile

Specify for your target language:

| Aspect | Value |
|--------|-------|
| **Language** | [LANGUAGE] |
| **Code block tag** | [e.g., `py`, `cs`, `rs`, `ps1`, `sh`] |
| **Comment prefix** | [e.g., `#`, `//`, `--`] |
| **Error identity mechanism** | [.code property / exception type / result variant / exit+stderr] |

---

## Structure

```
tests/
  <feature>.md    # One file per feature area
```

Each markdown file:
- Headers (`##`) create test groups
- Prose explains *why* the behavior exists
- Code blocks demonstrate and verify

---

## Documenting Intent (Critical for Agents)

The prose isn't decoration—it's how the agent understands *what correct means*.

### Before each test group, explain:

**What problem it solves:**
```markdown
## Input Validation

Users paste data from spreadsheets, which often includes invisible
whitespace characters. The validator must normalize these before
length checks, or users get confusing "too long" errors on strings
that look fine.
```

**Why an edge case matters:**
```markdown
### Empty vs Whitespace-Only

These are different failures. Empty means "user submitted nothing"
(user error). Whitespace-only means "user pasted invisible characters"
(data cleaning needed). The error messages must distinguish them so
callers can handle appropriately.
```

### The test name IS documentation:

- Bad: `## Test 3`
- Bad: `## Error Case`
- Good: `## Rejects Strings Over 100 Characters`
- Good: `## Treats Empty and Whitespace-Only Differently`

### Inline comments for non-obvious assertions:

```py
# -40 is where Celsius and Fahrenheit scales intersect
celsius_to_fahrenheit(-40)  # expect: -40.0

# IEEE 754: negative zero equals positive zero
compare(-0.0, 0.0)  # expect: true
```

---

## Writing Good Tests

**One behavior per code block:**
```
validate("")  // error: [empty-input]
```

```
validate(null)  // error: [null-input]
```

**Error codes must be stable identifiers:**
- Good: `[invalid-assignment]`, `[null-input]`, `[parse-error]`
- Bad: `[error]`, `[failed]`, `[oops]`

---

## Examples by Language

### Python
```py
validate(None)  # error: [null-input]
```

### Rust
```rs
let r = parse("garbage");
r.unwrap_err().code()  // expect: "invalid-input"
```

### Bash
```sh
mytool
# exit: 1
# stderr: contains("[missing-argument]")
```

### PowerShell
```ps1
Get-Thing -Path "C:\nonexistent"  # error: [PathNotFound]
```

### C#
```cs
service.Process(null);  // error: [ArgumentNullException]
```

---

## Domain Spec Template

Fill in when generating tests:

- **What it does:** [DESCRIPTION]
- **What problem it solves:** [WHY THIS EXISTS]
- **Language:** [LANGUAGE]
- **Code block tag:** [TAG]
- **Comment prefix:** [PREFIX]
- **Error identity mechanism:** [how errors expose stable codes]
- **Bootstrapping:** [how code-under-test is loaded]
- **Isolation model:** [`per-block` or `per-file`]
- **Error codes:** [EXHAUSTIVE LIST with descriptions]
- **Public API surface:** [LIST of functions/commands to test]
- **Happy paths:** [LIST]
- **Error cases:** [LIST with *why* each error exists]
- **Edge cases:** [LIST with *why* each matters]

---

## Requirements Checklist

- Error code index at top of file
- Every error code has at least one test
- Every public function has at least one happy-path test
- Edge cases (empty, null, boundary) covered
- Prose explains intent—agent should understand correct behavior
- Test names are behavior descriptions
- Coverage is auditable by scanning headers
