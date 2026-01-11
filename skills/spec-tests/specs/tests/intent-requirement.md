---
target:
  - SKILL.md
  - scripts/run_tests_claude.py
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

## Intent is Required

### Test Blocks Must Have Intent Prose

Spec tests exist for LLM-driven development where the agent implements code to pass
tests. Without intent, the LLM cannot distinguish "this number is arbitrary" from
"this number is a hard requirement." Missing intent means the test cannot be properly
evaluated and must fail.

```
Given the run_tests_claude.py runner parses a spec test with this content:
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

### Intent Must Appear Directly Above Code Block

Intent must be immediately discoverable when reading the test. Prose in a different
section or at the component level is not sufficient—each test needs its own "why"
to prevent gaming that specific assertion.

```
Given the run_tests_claude.py runner parses a spec test with this structure:
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

### Missing Intent Fails Before Assertion Check

If intent is missing, the test cannot be properly evaluated. The failure should
be reported immediately without attempting to run the assertion, because any
result would be meaningless without knowing what's being tested.

```
Given the run_tests_claude.py runner evaluates a test with missing_intent=True
When the LLMJudge.evaluate() method is called
Then it should immediately return a failed TestResult with [missing-intent]
And should NOT invoke the claude CLI
Because evaluation without intent is undefined
```
