# spec-tests

Intent-based specification tests evaluated by LLM-as-judge. Natural language specs that capture **WHY**, not just **WHAT**.

## Why use this?

If you're using LLMs to write code, you've probably seen this: the test says `elapsed < 50ms`, it fails at 73ms, and the LLM "fixes" it by changing the threshold to 100ms. Test passes. User gets a laggy app.

Traditional tests only check **what**. Spec tests also check **why**—so when the LLM sees "users perceive delays over 50ms as laggy," it knows the threshold isn't negotiable.

This matters when:
- LLMs are writing or modifying your code
- You want tests that survive refactoring without losing their purpose
- Requirements come from product/UX and need to stay anchored to user needs
- You're tired of tests that pass technically but miss the point

## What is this?

Natural language specs with intent statements, evaluated by an LLM judge. Each test has:
- **Intent** — WHY this matters (business reason, user need)
- **Assertion** — WHAT should happen (Given/When/Then)

The judge checks both. If the assertion passes but violates the intent, you get `[intent-violated]` instead of a false green.

```
[missing-target]    → Spec file has no target: in frontmatter
[missing-intent]    → Test has no intent statement
[missing-assertion] → Test has no assertion code block
[intent-violated]   → Assertion passes but violates stated business requirement
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

```
Given a user with valid email and password
When they submit the login form
Then they are redirected to the dashboard
```
```

2. Copy the runner to your project:

```bash
cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests_claude.py" specs/tests/
cp "${CLAUDE_PLUGIN_ROOT}/scripts/judge_prompt.md" specs/tests/
```

3. Run tests:

```bash
python specs/tests/run_tests_claude.py specs/tests/authentication.md
python specs/tests/run_tests_claude.py specs/tests/authentication.md --test "Valid Credentials Succeed"  # Single test
```

Uses `claude -p` (your subscription, no API key needed).

**Options:** `--target FILE` (override target), `--model MODEL`, `--test "Name"` (run single test)

**Alternative runners:** `run_tests_opencode.py` (uses opencode CLI), `run_tests_codex.py` (uses OpenAI Codex CLI). Same interface, different LLM backend.

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
│   ├── run_tests_claude.py   # Test runner (claude)
│   ├── run_tests_opencode.py # Test runner (opencode)
│   ├── run_tests_codex.py    # Test runner (codex)
│   └── judge_prompt.md       # LLM judge prompt template
└── specs/tests/          # Spec tests for this skill (dogfooding)
    └── *.md              # intent-requirement, skill-structure, etc.
```

## See Also

- [SKILL.md](SKILL.md) — Full specification with examples, cheat-proofing details, and evaluation model
