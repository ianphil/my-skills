---
name: spec-tests
description: >
  Intent-based specification tests evaluated by LLM-as-judge. Use when the user
  asks to "create spec tests", "TDD with intent", or wants tests that capture
  WHY, not just WHAT. NOT pytest/jest - natural language specs Claude evaluates.
---

# Spec Tests: Intent-Based Testing for LLM Development

Spec tests are **intent-based specifications** that Claude evaluates as judge. They capture WHY something matters—making them cheat-proof for LLM-driven development.

## The TDD Flow

```
1. Plan       → Define what you're building
2. Spec (red) → Write intent tests (they fail - no implementation yet)
3. Implement  → Build the feature
4. Spec (green) → Tests pass (Claude confirms intent is satisfied)
```

---

## Test File Format

```markdown
# Feature Name

## Test Group

### Test Case Name

Intent prose explaining WHY this test matters. What user need does it serve?
What breaks if this doesn't work?

\`\`\`
Given [precondition]
When [action]
Then [expected outcome]
\`\`\`
```

Structure: **H2** = test group, **H3** = test case, **prose** = required intent, **code block** = expected behavior.

**Critical:** Intent prose must appear **directly above** the code block, between the H3 header and the assertion. Component-level or section-level prose does not substitute for per-test intent—each test needs its own WHY immediately before its code block.

---

## Running Tests

First, copy the runner files to your project (Claude will do this automatically when using the skill):

```bash
# CLAUDE_PLUGIN_ROOT is set automatically when Claude invokes this skill
cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests_claude.py" tests/
cp "${CLAUDE_PLUGIN_ROOT}/scripts/judge_prompt.md" tests/
```

Then run tests:

```bash
python tests/run_tests_claude.py tests/feature.md --target src/feature.py   # Single file
python tests/run_tests_claude.py tests/ --target src/feature.py             # All tests in dir
```

Uses `claude -p` (your subscription, no API key needed).

---

## Why Intent Matters (Cheat-Proofing)

LLMs can "game" tests by changing them instead of fixing code.

**Without intent:**
```markdown
### Completes Quickly
\`\`\`
elapsed < 50ms  # Fails at 73ms
\`\`\`
```
LLM thinks: "50 seems arbitrary, change to 100." User gets laggy editor.

The runner reports `[missing-intent]` and fails immediately—tests without intent prose cannot be evaluated.

**With intent:**
```markdown
### Completes Quickly

Users perceive delays over 50ms as laggy. This runs on every keystroke.
The 50ms target is a UX requirement, not negotiable.

\`\`\`
Given a keystroke event
When process_keystroke() is called
Then it completes in under 50ms
\`\`\`
```

Claude-as-judge evaluates: Does it satisfy the UX requirement? If an LLM "fixes" by relaxing the threshold to 100ms, the runner reports `[intent-violated]`—the assertion might pass literally, but the stated UX requirement is violated.

**Intent properties:**
- **Required** — Missing intent → `[missing-intent]` failure before evaluation
- **Per-test** — Each test needs its own WHY directly above the code block
- **Business-focused** — Why users/product care, not technical details
- **Preserved when porting** — Same intent applies across languages (see example below)
- **Evaluative** — Catches "legal but wrong" solutions via `[intent-violated]`

---

## Example

```markdown
# User Authentication

## Login Flow

### Valid Credentials Succeed

Users expect immediate access with correct credentials. Friction here
directly impacts conversion—users abandon apps that make login difficult.

\`\`\`
Given a user with valid email and password
When they submit the login form
Then they are redirected to the dashboard
And a session token is created
\`\`\`

### Invalid Password Shows Generic Error

Don't reveal whether the email exists—attackers use specific errors to
enumerate accounts.

\`\`\`
Given a user submits an incorrect password
When the login is processed
Then the error is "Invalid email or password" (not "wrong password")
\`\`\`
```

---

## Porting Tests Across Languages

Intent is preserved when porting code between languages—the business reason doesn't change, only the assertion syntax.

**Python spec:**
```markdown
### Completes Quickly

Users perceive delays over 50ms as laggy. This operation runs on every
keystroke, so exceeding this threshold makes the editor feel unresponsive.

\`\`\`python
elapsed < 50  # expect: True
\`\`\`
```

**Same test ported to Rust:**
```markdown
### Completes Quickly

Users perceive delays over 50ms as laggy. This operation runs on every
keystroke, so exceeding this threshold makes the editor feel unresponsive.

\`\`\`rust
elapsed < 50  // expect: true
\`\`\`
```

The intent prose is identical—user perception of lag doesn't change with implementation language. Only the assertion syntax changes.

---

## Evaluation Model

The LLM-as-judge evaluates **both** the assertion AND the intent for every test:

1. **Pre-check:** If intent prose is missing, the test fails immediately with `[missing-intent]`. The assertion is not evaluated—evaluation without intent is undefined.

2. **Dual evaluation:** For tests with intent, Claude checks:
   - Does the assertion pass? (literal check)
   - Does the implementation satisfy the intent? (semantic check)

   The test passes **only if both are true**.

3. **Intent violation:** If the assertion passes but the intent is violated (e.g., gaming thresholds), the test fails with `[intent-violated]`.

This dual evaluation catches "legal but wrong" solutions that traditional assertion-only testing misses.

---

## Checklist

- [ ] Each test has intent prose explaining WHY
- [ ] Intent is business/user focused
- [ ] Expected behavior is clear
- [ ] One behavior per test case

> **Missing intent = immediate failure.** The runner rejects tests without intent prose before evaluating behavior—evaluation without intent is undefined.
