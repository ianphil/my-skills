---
target:
  - scripts/run_tests_claude.py
  - scripts/run_tests_opencode.py
  - scripts/run_tests_codex.py
---
# Graceful Degradation — SKIP Status for Structural Issues

Structural issues (`[missing-intent]`, `[missing-assertion]`) are authoring problems,
not test failures. They should produce SKIP status so they don't block feedback on
the rest of the suite or pollute `--rerun-failed`.

---

## SKIP Status

### Structural issues produce SKIP not FAIL

Half-written tests shouldn't count as real failures. When a test is missing its
intent statement or assertion code block, the runner can't evaluate it — but that's
an authoring problem, not an implementation problem. Treating these as FAIL would
penalize developers for incomplete specs rather than incomplete code.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
When LLMJudge.evaluate() encounters a test with missing_intent=True or missing_assertion=True
Then the returned TestResult must have skipped=True
And the TestRunner result loop must print SKIP (not FAIL) for that test
Because structural issues are authoring problems, not implementation failures
```

### Skipped tests don't affect exit code when passes exist

A suite with passing tests and some skipped tests should exit 0, not 1.
Skipped tests represent incomplete specs, and their presence shouldn't block
CI or signal failure when real tests are passing.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
When a test run produces at least one PASS and one or more SKIPs but zero FAILs
Then the runner must exit with code 0
Because skipped tests are not failures and should not block a green build
```

### Skipped tests are excluded from rerun-failed failure file

The `--rerun-failed` workflow saves failed test names to `.spec-tests-failures.json`.
Skipped tests must not appear in this file, because re-running them would just
skip them again — wasting time without providing value.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
When a test is skipped due to missing_intent or missing_assertion
Then its name must NOT be appended to the failed_names list
And it must NOT appear in .spec-tests-failures.json
Because re-running a skipped test would just skip it again
```

### All-skipped suite exits with code 2

When every test in a suite is skipped, there are no real results at all. This is
a distinct state from "all passed" — the user needs to know that nothing was
actually evaluated. Exit code 2 signals this without conflating it with failure.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
When a test run produces zero PASS results, zero FAIL results, and one or more SKIPs
Then the runner must exit with code 2
Because an all-skipped suite means nothing was actually evaluated
```
