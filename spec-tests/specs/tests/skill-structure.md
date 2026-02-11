---
target:
  - SKILL.md
  - scripts/run_tests_claude.py
  - scripts/run_tests_opencode.py
  - scripts/run_tests_codex.py
  - references/examples.md
---
# Skill Structure Requirements

This spec tests the structural elements of the spec-tests skill that aren't
about intent specifically, but are essential for users to understand and use
the skill correctly.

---

## TDD Flow

### Documents the Red-Green Cycle

The skill must teach the TDD workflow: write failing tests first, then implement.
Without this, users might write tests after implementation, defeating the purpose
of specification-driven development.

```
Given the SKILL.md file
Then it documents a flow that includes:
  - Planning/defining what to build
  - Writing spec tests that fail (red) before implementation exists
  - Implementing the feature
  - Tests passing (green) after implementation
Because TDD ensures tests are written as specifications, not afterthoughts
```

---

## Test Format

### Documents H2/H3 Structure

Users need to know how to structure their test files. Without clear format
guidance, tests become inconsistent and the runner can't parse them reliably.

```
Given the SKILL.md file
Then it documents that:
  - H2 (##) headers define test groups/sections
  - H3 (###) headers define individual test cases
  - Intent statement appears between H3 and code block
  - Code blocks contain expected behavior
Because consistent structure enables reliable parsing and clear organization
```

### Runner Parses H2/H3 Structure

The runner must implement what the documentation promises. If the parser doesn't
correctly extract H2 sections and H3 test cases, users get confusing failures
even when their spec files follow the documented format.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py
Then all have a SpecParser class that:
  - Tracks H2 (##) headers as section names
  - Extracts H3 (###) headers as test case names
  - Collects text between H3 and code block as intent
  - Extracts code block content as assertion
Because the implementation must match the documented structure
```

### Runner Flags Missing Assertion Block

A test without a code block is malformed. The runner should fail fast with a
clear error rather than skipping the test or mis-attaching later blocks.

```
Given run_tests_claude.py, run_tests_opencode.py, and run_tests_codex.py parse a spec test with this content:
  ### Missing Assertion
  Intent explaining why this matters.

When the SpecParser extracts test cases
Then it should set missing_assertion=True for this test
And the runner should report: [missing-assertion]
Because tests without assertion blocks cannot be evaluated
```

---

## Runner

### Documents How to Run Tests

Users need to know the exact command to run tests. Without this, the skill
is just documentation with no way to verify implementations.

```
Given the SKILL.md file
Then it includes:
  - How to copy the runner to a project
  - The command to run tests (python run_tests_claude.py)
  - How targets are specified (frontmatter or --target flag)
Because users can't verify implementations without knowing how to run the runner
```

### Uses Claude CLI Not API

Users shouldn't need an API key to run tests. The skill uses their existing
Claude subscription via `claude -p`. If this isn't documented, users might
think they need to set up API access.

```
Given the SKILL.md file
Then it mentions that the runner uses:
  - claude -p (or "claude CLI" or similar)
  - User's subscription (not API key)
Because users should know they don't need separate API billing to use this
```

---

## Differentiation

### Not Traditional Testing Frameworks

Users might confuse spec tests with pytest, jest, or unittest. The skill must
clearly state this is a different paradigm—LLM-evaluated natural language specs,
not assertion-based code tests. Without this, users will try to write code
assertions instead of intent-based specifications.

```
Given the SKILL.md file
Then it explicitly states this is NOT:
  - pytest
  - jest
  - unittest
  - or similar traditional test frameworks
Because users need to understand this is a different testing paradigm
```

---

## Test Granularity

### One Behavior Per Test

Each test should cover a single behavior. When tests combine multiple behaviors,
failures become ambiguous—you don't know which behavior broke. This also makes
tests harder to understand and maintain.

```
Given the SKILL.md and references/examples.md files
Then they document that each test should cover one behavior
  (may be phrased as "one behavior per test" or "single behavior" or similar)
And explain why: multi-behavior tests create ambiguous failures
Because users need to understand both the rule and the reasoning
```
