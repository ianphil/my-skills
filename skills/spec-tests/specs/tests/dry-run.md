---
target:
  - scripts/run_tests_claude.py
  - scripts/run_tests_opencode.py
  - scripts/run_tests_codex.py
---
# Dry Run (Inspectable IR)

Tests for the `--dry-run` flag that outputs the parsed intermediate representation
as JSON without invoking any LLM.

---

## Flag Acceptance

### All Runners Accept --dry-run Flag

When a spec test fails, users need to distinguish parser bugs from judge bugs.
Without a way to inspect what the parser extracted, debugging requires reading
runner internals. The `--dry-run` flag must be accepted by all runners.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then all accept a "--dry-run" argparse flag with action="store_true"
Because users need to inspect parsed IR without invoking the LLM
```

---

## Output Schema

### Dry Run Outputs Valid JSON with Correct Schema

The dry-run output must be machine-parseable JSON so it can be piped to
`jq`, `python -m json.tool`, or other tooling. The schema must include
source, target, and a tests array with group, name, intent, assertion,
line_number, missing_intent, and missing_assertion fields.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then all contain a build_ir_dict function that returns a dict with keys:
  - "source" (string path to spec file)
  - "target" (list of string paths)
  - "tests" (list of dicts with keys: group, name, intent, assertion, line_number, missing_intent, missing_assertion)
And the dry-run path prints this dict as JSON via json.dumps
Because the IR must be machine-parseable for tooling and debugging
```

---

## Test Filtering

### Dry Run Respects --test Filter

When debugging a single test, users combine `--dry-run` with `--test` to see
only that test's parsed IR. Without filter support, they'd have to visually
search through all tests in the JSON output.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then when --dry-run is combined with --test, the output only includes
  tests whose name matches the filter
Because users need to inspect a single test's IR without noise from others
```

---

## LLM Skipping

### Dry Run Skips LLM Invocation

The whole point of `--dry-run` is instant, free feedback. If it still calls
the LLM, it defeats the purpose — costing money and adding latency. The
CLI availability check must also be skipped since the CLI may not be installed
in environments where only parsing is needed.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then when --dry-run is set:
  - The CLI availability check (subprocess.run with --version) is skipped
  - No TestRunner or LLMJudge is instantiated
  - The code exits with sys.exit(0) after printing JSON
Because dry-run must be instant, free, and work without the CLI installed
```
