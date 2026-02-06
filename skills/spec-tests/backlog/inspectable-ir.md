# Inspectable Intermediate Representation

## Problem

When a spec test fails unexpectedly, there's no way to inspect what the runner
parsed from the markdown before sending it to the LLM judge. Debugging requires
guessing whether the issue is in parsing (wrong test extracted) or evaluation
(LLM misjudged).

## Inspiration

Uncle Bob's empire-2025 acceptance test framework uses a three-stage pipeline:
`.txt` → `.edn` (intermediate representation) → `.clj` (executable specs). The
EDN stage is inspectable — you can see exactly what the parser produced before
code generation runs.

## Proposed Solution

Emit a structured parse result (JSON or YAML) before sending to the LLM judge.
This could be:

- A `--dry-run` flag that outputs the parsed test cases as JSON without evaluating
- A `--emit-ir` flag that writes `.json` files alongside test results
- Always writing an IR file to a `.spec-tests-cache/` directory

## Expected IR Structure

```json
{
  "source": "specs/tests/authentication.md",
  "target": ["src/auth.py"],
  "tests": [
    {
      "group": "Login Flow",
      "name": "Valid Credentials",
      "intent": "Users must be able to sign in with correct email and password...",
      "assertion": "Given a registered user...\nWhen they submit valid credentials...\nThen they receive a session token",
      "line_number": 15
    }
  ]
}
```

## Value

- Debug parsing issues without re-running the LLM judge
- Validate that frontmatter, intent, and assertions were correctly extracted
- Enable tooling that consumes the IR (editors, CI dashboards)
