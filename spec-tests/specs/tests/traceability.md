---
target:
  - scripts/run_tests_claude.py
  - scripts/run_tests_opencode.py
  - scripts/run_tests_codex.py
---
# Source Traceability

Tests for `file:line` source location in test output, enabling click-to-navigate
from terminal failures back to the spec file.

---

## Output Format

### Test Output Includes spec_path and line_number

When a suite has many tests, finding the failing spec by name alone requires
manual searching. Including `spec_path:line_number` in the output line enables
click-to-navigate in terminals and editors, matching the convention used by
compilers and linters.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then the print statement for each test in TestRunner.run() includes
  self.spec_path and test.line_number in the format "spec_path:line_number"
  before the section and test name
Because terminal click-to-navigate requires the file:line pattern in output
```
