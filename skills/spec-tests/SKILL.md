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

---

## Running Tests

```bash
cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests_claude.py" tests/
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

Claude-as-judge evaluates: Does it satisfy the UX requirement? Relaxing to 100ms = FAIL.

**Intent properties:**
- **Required** — Missing intent = test failure
- **Per-test** — Each test needs its own WHY
- **Business-focused** — Why users/product care, not technical details
- **Preserved when porting** — Same intent applies across languages (Python → Rust)
- **Evaluative** — Catches "legal but wrong" solutions

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

## Checklist

- [ ] Each test has intent prose explaining WHY
- [ ] Intent is business/user focused
- [ ] Expected behavior is clear
- [ ] One behavior per test case

> **Missing intent = immediate failure.** The runner rejects tests without intent prose before evaluating behavior—evaluation without intent is undefined.
