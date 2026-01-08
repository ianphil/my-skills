---
name: literate-tests
description: >
  This skill should be used when the user asks to "create literate tests",
  "generate markdown tests", "specification-as-tests", "TDD with markdown",
  "agent-driven testing", "port code to another language", or mentions test
  suites where markdown IS the test format. NOT for pytest/jest/unittest.
  Creates .md test files with inline assertions and uses a bundled custom
  test runner. Includes cookbook for porting code between languages.
---

# Literate Test Suite Generator

Create a test suite for **[DOMAIN]** that an agent can run autonomously.

> **Porting Code?** If your goal is to port code from one language to another (e.g., PowerShell → bash),
> see the **[Porting Code Cookbook](references/creating-tests-for-porting-code.md)** for a comprehensive
> guide on creating layered test suites that define the contract both implementations must satisfy.

## What This Pattern Produces

> **CRITICAL:** This is NOT pytest/jest/unittest/etc. This creates a CUSTOM test format.

Generate **two artifacts**:

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

### 2. Test Runner (language-specific)

Copy the appropriate bundled runner for your language:

| Language | Runner | Copy Command |
|----------|--------|--------------|
| Python | `run_tests.py` | `cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.py" tests/` |
| JavaScript | `run_tests.js` | `cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.js" tests/` |
| TypeScript | `run_tests.ts` | `cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.ts" tests/` |
| Bash/Shell | `run_tests.sh` | `cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.sh" tests/` |
| PowerShell | `run_tests.ps1` | `cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.ps1" tests/` |
| Rust | `run_tests.rs` | `cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests.rs" tests/` |
| C# | `RunTests.cs` | `cp "${CLAUDE_PLUGIN_ROOT}/scripts/RunTests.cs" tests/` |

All runners:
1. Parse markdown files for TOML frontmatter
2. Extract language-specific code blocks
3. Validate `# expect:` / `// expect:` and `# error:` / `// error:` assertions
4. Support matchers: `approx()`, `contains()`
5. Report pass/fail with colored output

**Do NOT use pytest, jest, xunit, or any standard test framework.**

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

## Red/Green TDD Requirement

> **CRITICAL:** Tests MUST actually test the real script/module, not self-contained snippets.

Tests should **fail (red)** when:
- The implementation doesn't exist
- The implementation has bugs
- The implementation behavior doesn't match the assertion

Tests should **pass (green)** only when:
- The implementation exists AND
- The implementation behaves correctly

### Wrong: Self-Contained Snippets (Don't Do This)

```markdown
### Normalizes to lowercase
\`\`\`bash
# This tests bash itself, NOT your script!
input="HELLO"
echo "$input" | tr '[:upper:]' '[:lower:]'
# expect: hello
\`\`\`
```

This passes regardless of whether your script exists or works.

### Correct: Test the Actual Implementation

```markdown
### Normalizes to lowercase
\`\`\`bash
# Source the actual script being tested
source "../../tools/scripts/my-script.sh" --source-only

# Call the real function
result=$(normalize_input "HELLO")
echo "$result"
# expect: hello
\`\`\`
```

This **fails** until `my-script.sh` exists with a working `normalize_input` function.

### Script Sourcing Patterns

**Bash** - Use `--source-only` flag pattern:
```bash
# In test file
source "$(dirname "${BASH_SOURCE[0]}")/../../path/to/script.sh" --source-only

# In script being tested (at bottom)
if [[ "${1:-}" != "--source-only" ]]; then
    main "$@"
fi
```

**PowerShell** - Dot-source the script:
```powershell
. "$PSScriptRoot/../../path/to/script.ps1"
```

**Python** - Import the module:
```python
from mypackage.module import function_under_test
```

### For Porting: Both Test Suites Must Test Real Implementations

When porting from Language A to Language B:
1. **PowerShell tests** source and test the original `.ps1` script
2. **Bash tests** source and test the ported `.sh` script
3. Both should **fail** if their respective implementation is missing/broken
4. Both should **pass** when their implementation is correct

---

## Living Documentation Through Intent

Tests = executable docs that stay accurate (lies fail CI). Each test answers: **"What can the user now do?"**

**Intent structure per component:**
- **Purpose:** One sentence — what does this do?
- **Why it matters:** Business/technical value
- **After X completes, a user can...** — Concrete outcomes
- **Error codes:** What can go wrong

**Example:**
```markdown
## Buildout Intent
**Purpose:** Provision shared infrastructure
**Why it matters:** Without this, no Service Bus/KeyVault/storage
**After Buildout, developer can:** Connect to Service Bus, store secrets, upload artifacts

### Service Bus Is Accessible
\`\`\`py
namespace.is_accessible  # expect: True
\`\`\`
```

**Bad:** `config["buildout"].priority # expect: 1` (implementation detail)
**Good:** "After Buildout, developer can connect to Service Bus" (user outcome)

---

## File Structure

```
project/
├── src/
│   └── <module>.<ext>        # Code under test
└── tests/
    ├── <feature>.md          # Markdown test files
    └── run_tests.<ext>       # Language-specific runner (copied from skill)
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

Assertions are inline comments that define expected behavior:

```py
validate("hello")  # expect: True
validate("")       # error: [empty-input]
pi_value()         # expect: approx(3.14159, tol=0.0001)
```

**For complete syntax details** including matchers, CLI tests, and language-specific formats, see **[Assertion Syntax Reference](references/assertion-syntax.md)**.

---

## Using the Bundled Runners

Copy runner: `cp "${CLAUDE_PLUGIN_ROOT}/scripts/<runner>" tests/`

| Language | Run Command | Code Blocks | Assertions | Requirements |
|----------|-------------|-------------|------------|--------------|
| Python | `python tests/run_tests.py` | `py`, `python` | `# expect:`, `# error:` | - |
| JavaScript | `node tests/run_tests.js` | `js`, `javascript` | `// expect:`, `// error:`, `// throws:` | - |
| TypeScript | `npx tsx tests/run_tests.ts` | `ts`, `typescript` | `// expect:`, `// error:`, `// throws:` | `npm install -D tsx` |
| Bash | `bash tests/run_tests.sh` | `sh`, `bash` | `# exit:`, `# stdout:`, `# stderr:` | - |
| PowerShell | `pwsh tests/run_tests.ps1` | `ps1`, `powershell`, `bash`, `sh` | `# exit:`, `# stdout:`, `# stderr:`, `# throws:`, `# expect:` | Supports both PS & bash |
| Rust | `rust-script tests/run_tests.rs` | `rs`, `rust` | `// expect:`, `// error:`, `// compiles`, `// compile_fails:` | `cargo install rust-script` |
| C# | `dotnet script tests/RunTests.cs` | `cs`, `csharp` | `// expect:`, `// error:` | `dotnet tool install -g dotnet-script` |

**PowerShell runner note:** The `# expect:` assertion compares stdout: `echo "hello" # expect: hello`

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

When asked to create literate tests:

- [ ] Identify target language and copy appropriate runner from `${CLAUDE_PLUGIN_ROOT}/scripts/`
- [ ] Create `.md` files in `tests/`, NOT language-specific test files
- [ ] Include TOML frontmatter at top of each test file
- [ ] Include error code index before tests
- [ ] Use correct assertion syntax for language (`#` for Python/Bash, `//` for Rust/C#)
- [ ] **Document intent**: Purpose, Why it matters, Outcomes (not just mechanics)
- [ ] Prose explains WHY, not just WHAT
- [ ] One behavior per code block
- [ ] Test names are behavior descriptions (outcomes, not implementations)

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

### Intent Template (per component/feature)

For each major component, document:

```markdown
## [Component] Intent

**Purpose:** [One sentence: what does this component do?]

**Why it matters:** [2-3 sentences: business/technical value, what breaks without it]

**After [Component] completes, a user can:**
- [Concrete outcome 1]
- [Concrete outcome 2]
- [Concrete outcome 3]

**Error codes:**
- `[error-code-1]` — [When this happens and what it means]
- `[error-code-2]` — [When this happens and what it means]
```

This ensures your tests serve as both **executable specifications** and **onboarding documentation**.