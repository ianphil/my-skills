---
target:
  - scripts/run_tests_claude.py
  - scripts/run_tests_opencode.py
  - scripts/run_tests_codex.py
---
# Rerun Failed Tests

Tests for the `--rerun-failed` flag that re-runs only previously failed tests
by reading a `.spec-tests-failures.json` file written after every run.

---

## Flag Acceptance

### All Runners Accept --rerun-failed Flag

After fixing a couple of failures, re-running the entire suite wastes tokens on
tests that already passed. The `--rerun-failed` flag must be accepted by all
runners so users can iterate cheaply on just the broken tests.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then all accept a "--rerun-failed" argparse flag with action="store_true"
And all define a FAILURE_FILE constant set to Path(".spec-tests-failures.json")
Because users need to re-run only failed tests without wasting tokens
```

---

## Failure File Persistence

### Runners Write Failure File After Each Run

Without a persistent record of which tests failed, the runner has no way to
know what to re-run. The failure file must be written after every run (with
failures) and deleted when all tests pass.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then all define load_failures() and save_failures() helper functions
And save_failures writes a JSON file with {"version": 1, "failures": [...]}
  where each failure has "spec_file" (resolved absolute path) and "test_name"
And save_failures deletes the file when the failures list is empty
And the main() function calls save_failures after the runner loop
Because the runner needs a persistent record of failures to support --rerun-failed
```

---

## Filtering Behavior

### --rerun-failed Filters to Only Previously Failed Tests

The core value of `--rerun-failed` is skipping tests that already passed.
It must load the failure file, build a filter of spec-file-to-test-names,
narrow the spec files to only those with failures, and pass the test names
filter to the TestRunner.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then when --rerun-failed is set:
  - The runner loads previous failures from FAILURE_FILE via load_failures()
  - If no failure file exists, it prints a message and exits 0
  - It builds a rerun_filter mapping resolved spec paths to test name sets
  - It narrows spec_files to only those with recorded failures
  - It passes test_names_filter to TestRunner for per-spec-file filtering
And TestRunner.__init__ accepts a test_names_filter parameter
And TestRunner.run() filters tests by test_names_filter when provided
Because only previously-failed tests should be re-evaluated
```

---

## Mutual Exclusion

### --rerun-failed and --test Are Mutually Exclusive

Using both flags is ambiguous — does the user want a specific test or the
previous failures? Rather than guessing, the runner must reject the
combination with a clear error message.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then when both --rerun-failed and --test are provided:
  - The runner prints "Error: --rerun-failed and --test are mutually exclusive"
  - The runner exits with sys.exit(1)
And this check happens before any spec file processing
Because ambiguous flag combinations should fail fast with a clear message
```
