---
target:
  - SKILL.md
  - scripts/run_tests_claude.py
  - scripts/run_tests_opencode.py
  - scripts/run_tests_codex.py
---
# Intent Requirement Specification

This spec defines the required behavior for per-test intent in spec tests.
It ensures the "cheat-proofing" property is preserved across changes to the skill.

**Problem:** LLMs can "game" test assertions by modifying tests instead of fixing
implementations. Without intent, there's no way to distinguish negotiable constraints
from sacred requirements.

**Solution:** Every test block requires intent prose that the LLM-as-judge evaluates
alongside the assertion.

**Error codes:**
- `[missing-intent]` — Test block has no intent prose above it
- `[intent-violated]` — Implementation passes assertion but violates stated intent

---

## Error Code Consistency

### Missing Intent Error Code

Users see error messages from the runner and reference the documentation to
understand them. If docs say `[missing-intent]` but the runner outputs something
different, users can't correlate errors to documentation.

```
Given SKILL.md, scripts/run_tests_claude.py, scripts/run_tests_opencode.py, and scripts/run_tests_codex.py
Then all use [missing-intent] as the error code for tests without intent prose
Because error codes must match between documentation and implementation
```

### Documents Multi-File Given Syntax

When the same requirement applies to multiple files (e.g., docs and implementation
must agree on an error code), users need to write one test that covers all files.
Without this syntax, they'd duplicate the same test for each target.

```
Given the SKILL.md file
Then it documents how to write tests that apply to multiple files using:
  - Multi-file Given clause: "Given file1 and file2"
  - Single assertion that applies to all listed files
  - Guidance on when to use multi-file vs separate tests
Because users need to avoid test duplication when requirements span files
```

---

## Intent is Required

### Documents Intent Requirement

The skill must clearly state that intent prose is mandatory for every test.
Users need to understand this isn't optional—tests without intent cannot be
evaluated and will fail immediately.

```
Given the SKILL.md file
Then it documents that:
  - Intent prose is required for every test
  - Intent must explain WHY the test matters
  - Missing intent causes immediate failure with [missing-intent]
Because users must understand intent is mandatory, not optional
```

### Runner Detects Missing Intent

Spec tests exist for LLM-driven development where the agent implements code to pass
tests. Without intent, the LLM cannot distinguish "this number is arbitrary" from
"this number is a hard requirement." Missing intent means the test cannot be properly
evaluated and must fail.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py parse a spec test with this content:
  ### Completes Quickly
  ```py
  elapsed < 50  # expect: True
  ```

When the SpecParser extracts test cases
Then it should set missing_intent=True for this test
And the runner should report: [missing-intent]
And should NOT invoke the LLM
Because there is no prose explaining WHY 50ms matters
```

### Documents Per-Test Intent Location

The skill must explain that intent belongs directly above each test's code block,
not at the section level. Users might assume section-level prose counts—the docs
must clarify this won't work.

```
Given the SKILL.md file
Then it documents that:
  - Intent prose must appear between H3 header and code block
  - Section-level (H2) intent does not count for individual tests
  - Each test case needs its own WHY
Because users must know where to place intent for it to be recognized
```

### Runner Requires Per-Test Intent

Intent must be immediately discoverable when reading the test. Prose in a different
section or at the component level is not sufficient—each test needs its own "why"
to prevent gaming that specific assertion.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py parse a spec test with this structure:
  ## Performance (component-level intent here)

  ### Completes Quickly
  ```py
  elapsed < 50  # expect: True
  ```

When the SpecParser extracts the "Completes Quickly" test
Then it should set missing_intent=True
And the runner should report: [missing-intent]
Because component-level intent does not substitute for per-test intent
```

---

## Cheat-Proofing

### Relaxing Constraints Violates Intent

The core value of intent is preventing "legal but wrong" solutions. When an LLM
changes a test threshold to make it pass, the assertion succeeds but the user's
actual requirement is violated. The LLM-as-judge must catch this.

```
Given a spec test with this content:
  ### Completes Quickly

  Users perceive delays over 50ms as laggy. This operation runs on every
  keystroke, so exceeding this threshold makes the editor feel unresponsive.

  ```py
  elapsed < 50  # expect: True
  ```

When an implementation takes 73ms
And the LLM "fixes" by changing the test to: elapsed < 100  # expect: True
Then the LLM-as-judge should report: intent-violated
Because the intent states 50ms is a UX requirement, not negotiable
And the fix must be: optimize the code, not relax the threshold
```

### Assertions Without Intent Are Ambiguous

Without intent, the LLM-as-judge cannot determine if a constraint is sacred or
negotiable. This ambiguity is itself a failure—specs must be unambiguous for
autonomous development to work correctly.

```
Given two tests with identical assertions but different intents:

Test A (intent: "50ms is a UX perception threshold"):
  elapsed < 50  # expect: True

Test B (intent: "50ms is a rough estimate, optimize if easy"):
  elapsed < 50  # expect: True

When implementation takes 73ms
Then Test A fix should be: optimize the code
And Test B fix could be: relax to 100ms OR optimize
Because intent determines which fixes are valid
```

---

## Intent Properties

### Intent is Business-Focused

Intent explains why USERS or the PRODUCT care, not technical implementation details.
Technical details belong in the assertion itself. Intent answers: "What breaks for
the user if this test fails?"

```
Given these two intent statements for the same test:

Bad intent: "We use a HashMap with O(1) lookup so this should be fast"
Good intent: "Users perceive delays over 50ms as laggy on every keystroke"

When evaluating intent quality
Then the bad intent should be flagged as: technical-not-business
Because it describes HOW, not WHY users care
And it doesn't help the LLM understand what's negotiable
```

### Intent is Preserved When Porting

When porting code from one language to another, the business reason doesn't change.
The same intent that applies to the Python version applies to the Rust version.
Only the assertion syntax changes.

```
Given a Python spec test:
  ### Completes Quickly

  Users perceive delays over 50ms as laggy. This operation runs on every
  keystroke, so exceeding this threshold makes the editor feel unresponsive.

  ```py
  elapsed < 50  # expect: True
  ```

When porting to Rust
Then the Rust spec test should have:
  - Same intent prose (verbatim or equivalent)
  - Rust assertion syntax: // expect: true

Because the user's perception of lag doesn't change with implementation language
```

---

## Evaluation Model

### LLM-as-Judge Evaluates Both Assertion AND Intent

Traditional test runners only check if assertions pass. Spec tests with intent
require evaluating whether the implementation satisfies the underlying requirement,
not just the literal assertion text.

```
Given a spec test with intent and assertion
When the LLM-as-judge evaluates an implementation
Then it must check:
  1. Does the assertion pass? (literal check)
  2. Does the implementation satisfy the intent? (semantic check)
And the test passes only if BOTH are true
```

### Documents Early Failure for Missing Intent

The skill must explain that missing intent causes immediate failure before
evaluation. Users need to understand this isn't a warning—evaluation without
intent is undefined and the runner won't attempt it.

```
Given the SKILL.md file
Then it documents that:
  - Missing intent causes immediate failure
  - The assertion is not evaluated when intent is missing
  - The error code is [missing-intent]
Because users must understand evaluation requires intent
```

### Runner Fails Early for Missing Intent

If intent is missing, the test cannot be properly evaluated. The failure should
be reported immediately without attempting to run the assertion, because any
result would be meaningless without knowing what's being tested.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py evaluate a test with missing_intent=True
When the LLMJudge.evaluate() method is called
Then it should immediately return a failed TestResult with [missing-intent]
And should NOT invoke the LLM CLI
Because evaluation without intent is undefined
```
