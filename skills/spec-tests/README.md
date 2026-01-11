# spec-tests

Intent-based specification tests evaluated by LLM-as-judge. Natural language specs that capture **WHY**, not just **WHAT**.

## What is this?

Traditional tests check assertions. Spec tests check **intent**—the business reason behind the assertion. This makes them cheat-proof for LLM-driven development: Claude can't "game" the test by relaxing thresholds when it understands *why* those thresholds exist.

```
[missing-intent]  → Test has no intent prose, fails immediately
[intent-violated] → Assertion passes but violates stated business requirement
```

## Quick Start

1. Create a spec file in `specs/tests/`:

```markdown
---
target: src/auth.py
---
# Authentication

## Login

### Valid Credentials Succeed

Users expect immediate access with correct credentials. Friction here
directly impacts conversion—users abandon apps that make login difficult.

​```
Given a user with valid email and password
When they submit the login form
Then they are redirected to the dashboard
​```
```

2. Copy the runner to your project:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests_claude.py" specs/tests/
cp "${CLAUDE_PLUGIN_ROOT}/scripts/judge_prompt.md" specs/tests/
```

3. Run tests:

```bash
python specs/tests/run_tests_claude.py specs/tests/authentication.md
```

Uses `claude -p` (your subscription, no API key needed).

## Test Format

| Element | Markdown | Purpose |
|---------|----------|---------|
| Group | `## Section` | Organize related tests |
| Test | `### Name` | Individual test case |
| Intent | Prose before code block | **Required.** WHY this matters |
| Assertion | Code block | Expected behavior (Given/When/Then) |

## Files

```
skills/spec-tests/
├── SKILL.md              # Full documentation (Claude reads this)
├── README.md             # This file
├── scripts/
│   ├── run_tests_claude.py   # Test runner
│   └── judge_prompt.md       # LLM judge prompt template
└── specs/tests/          # Spec tests for this skill (dogfooding)
    ├── intent-requirement.md
    ├── skill-structure.md
    └── test-location.md
```

## See Also

- [SKILL.md](SKILL.md) — Full specification with examples, cheat-proofing details, and evaluation model
