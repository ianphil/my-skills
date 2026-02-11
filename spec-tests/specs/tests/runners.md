---
target:
  - scripts/run_tests_claude.py
  - scripts/run_tests_opencode.py
  - scripts/run_tests_codex.py
---
# CLI Runners

Tests for LLM CLI runners. Each runner wraps a specific CLI tool but must share
common behavior for consistent test execution across different backends.

---

## Non-Interactive Execution

### Claude Runner Uses Non-Interactive Mode

Test runners execute in CI pipelines, scripts, and automated workflows where no
human is present to interact with prompts. A runner that launches an interactive
session would hang indefinitely, breaking automation.

```
Given the run_tests_claude.py file
Then it invokes claude with the "-p" flag for non-interactive prompt mode
Because automated test execution cannot handle interactive prompts
```

### Opencode Runner Uses Non-Interactive Mode

Test runners execute in CI pipelines, scripts, and automated workflows where no
human is present to interact with prompts. A runner that launches an interactive
session would hang indefinitely, breaking automation.

```
Given the run_tests_opencode.py file
Then it invokes opencode with the "run" subcommand for non-interactive execution
Because automated test execution cannot handle interactive prompts
```

### Codex Runner Uses Non-Interactive Mode

Test runners execute in CI pipelines, scripts, and automated workflows where no
human is present to interact with prompts. A runner that launches an interactive
session would hang indefinitely, breaking automation.

```
Given the run_tests_codex.py file
Then it invokes codex with the "exec" subcommand for non-interactive execution
Because automated test execution cannot handle interactive prompts
```

---

## Model Configuration

### Claude Runner Allows Model Selection

Different models have different capabilities, costs, and speed tradeoffs. Teams
need to choose faster/cheaper models for rapid iteration and more capable models
for final validation. Hardcoding a model would force unnecessary costs or miss
quality issues.

```
Given the run_tests_claude.py file
Then it accepts a model parameter and passes it via "--model" flag to claude
Because teams need flexibility to balance cost, speed, and accuracy
```

### Opencode Runner Allows Model Selection

Different models have different capabilities, costs, and speed tradeoffs. Teams
need to choose faster/cheaper models for rapid iteration and more capable models
for final validation. Hardcoding a model would force unnecessary costs or miss
quality issues.

```
Given the run_tests_opencode.py file
Then it accepts a model parameter and passes it via "-m" flag in provider/model format
Because teams need flexibility to balance cost, speed, and accuracy
```

### Codex Runner Allows Model Selection

Different models have different capabilities, costs, and speed tradeoffs. Teams
need to choose faster/cheaper models for rapid iteration and more capable models
for final validation. Hardcoding a model would force unnecessary costs or miss
quality issues.

```
Given the run_tests_codex.py file
Then it accepts a model parameter and passes it via "--model" flag to codex
Because teams need flexibility to balance cost, speed, and accuracy
```

### Codex Runner Default Model

Without a sensible default, users must always specify a model even for quick
runs. The default should be capable enough for accurate judging but not the
most expensive option.

```
Given the run_tests_codex.py file
Then it defaults to "gpt-5.2-codex" when no model is specified
Because users expect reasonable out-of-box behavior without configuration
```

### Both Runners Default to Sonnet-Class Model

Without a sensible default, users must always specify a model even for quick
runs. The default should be capable enough for accurate judging but not the
most expensive option.

```
Given run_tests_claude.py and run_tests_opencode.py
Then both default to a sonnet-class model when no model is specified
Because users expect reasonable out-of-box behavior without configuration
```

---

## Output Handling

### Claude Runner Requests Text Output

The runner must extract structured verdicts (pass/fail + reasoning) from LLM
responses. If the CLI outputs decorated/formatted text, parsing becomes fragile
and error-prone.

```
Given the run_tests_claude.py file
Then it passes "--output-format text" to claude CLI
Because structured verdict extraction requires predictable output format
```

### Opencode Runner Requests JSON Output

The runner must extract structured verdicts (pass/fail + reasoning) from LLM
responses. If the CLI outputs decorated/formatted text, parsing becomes fragile
and error-prone.

```
Given the run_tests_opencode.py file
Then it passes "--format json" to opencode CLI
Because structured verdict extraction requires raw JSON events
```

### Codex Runner Requests JSON Output

The runner must extract structured verdicts (pass/fail + reasoning) from LLM
responses. If the CLI outputs decorated/formatted text, parsing becomes fragile
and error-prone.

```
Given the run_tests_codex.py file
Then it passes "--json" to codex exec
And writes the last assistant message with "--output-last-message"
Because structured verdict extraction requires machine-readable output
```

### Claude Runner Parses JSON from Responses

LLM responses may include markdown formatting, explanation text, or code blocks
around the actual JSON verdict. The runner must reliably extract the JSON
regardless of surrounding content.

```
Given the run_tests_claude.py file
Then it has logic to extract JSON from responses that may include:
  - Markdown code blocks (```json ... ```)
  - Surrounding explanation text
And parses the JSON object expecting "passed" and "reasoning" fields
Because LLMs don't always output bare JSON even when instructed to
```

### Opencode Runner Parses JSON from Responses

LLM responses may include markdown formatting, explanation text, or code blocks
around the actual JSON verdict. The runner must reliably extract the JSON
regardless of surrounding content.

```
Given the run_tests_opencode.py file
Then it has logic to extract JSON from responses that may include:
  - Markdown code blocks (```json ... ```)
  - Surrounding explanation text
And parses the JSON object expecting "passed" and "reasoning" fields
Because LLMs don't always output bare JSON even when instructed to
```

### Codex Runner Parses JSON from Responses

LLM responses may include markdown formatting, explanation text, or code blocks
around the actual JSON verdict. The runner must reliably extract the JSON
regardless of surrounding content.

```
Given the run_tests_codex.py file
Then it has logic to extract JSON from responses that may include:
  - Markdown code blocks (```json ... ```)
  - Surrounding explanation text
And parses the JSON object expecting "passed" and "reasoning" fields
Because LLMs don't always output bare JSON even when instructed to
```

---

## Reliability

### All Runners Enforce Execution Timeout

LLM calls can hang due to network issues, overloaded servers, or pathological
prompts. Without timeouts, a single stuck test blocks the entire suite
indefinitely, making CI unusable.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then all enforce a timeout on CLI execution (at least 60 seconds, at most 300)
Because hung tests must not block CI pipelines indefinitely
```

### All Runners Report Errors Without Crashing

When the CLI fails (auth issues, network errors, invalid responses), the runner
should report the failure for that specific test and continue with remaining
tests. Crashing on first error wastes the work already done.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then all return a TestResult with error information when CLI fails
And continue processing remaining tests
Because partial results are more valuable than complete failure
```

---

## Prompt Handling

### All Runners Load External Prompt Template

The judge prompt is complex and benefits from being editable without modifying
Python code. Inlining it would make maintenance harder and bloat the runner.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then all load the judge prompt from judge_prompt.md in the scripts directory
Because separating prompt from code enables easier iteration and review
```

### All Runners Substitute Test Variables

Each test has unique content (name, section, intent, assertions) that must be
injected into the prompt template. The runner must reliably substitute all
placeholders.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then all substitute these placeholders when rendering the prompt:
  - {{target_name}}
  - {{target_content}}
  - {{test_name}}
  - {{test_section}}
  - {{intent}}
  - {{assertion_block}}
Because the judge needs complete context to evaluate each test accurately
```
