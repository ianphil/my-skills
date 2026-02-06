# Evaluation Model

The LLM-as-judge evaluates **both** the assertion AND the intent for every test:

1. **Pre-check:** If intent statement is missing, the test fails immediately with `[missing-intent]`. The assertion is not evaluated—evaluation without intent is undefined.

2. **Dual evaluation:** For tests with intent, Claude checks:
   - Does the assertion pass? (literal check)
   - Does the implementation satisfy the intent? (semantic check)

   The test passes **only if both are true**.

3. **Intent violation:** If the assertion passes but the intent is violated (e.g., gaming thresholds), the test fails with `[intent-violated]`.

This dual evaluation catches "legal but wrong" solutions that traditional assertion-only testing misses.

---

## Error Codes

**Runner errors** (caught before LLM evaluation):
| Code | Meaning | Status |
|------|---------|--------|
| `[missing-intent]` | Test has no intent statement above code block | SKIP |
| `[missing-assertion]` | Test has no code block | SKIP |
| `[missing-target]` | Spec file has no target in frontmatter | Fatal (exit 1) |

Structural issues (`[missing-intent]`, `[missing-assertion]`) produce SKIP status — they don't count as failures, don't pollute `--rerun-failed`, and don't cause exit code 1.

**Judge error codes** (returned by LLM evaluation):
| Code | Meaning |
|------|---------|
| `[intent-violated]` | Assertion passes but intent requirement is not satisfied |
| `[assertion-failed]` | The literal assertion check failed |
| `[ambiguous]` | Judge cannot determine pass/fail with confidence |
| `[not-implemented]` | Feature is stubbed, TODO, or incomplete |

---

## Response Format

The judge outputs JSON that runners parse:
```json
{"passed": true, "reasoning": "..."}
{"passed": false, "reasoning": "[assertion-failed] Expected X but found Y"}
```

The `reasoning` field should be brief (~100 characters) and include the error code when failing.

---

## Strictness Rules

The judge follows these principles:
- **No benefit of doubt** — Ambiguous cases fail with `[ambiguous]`
- **Complete implementations only** — Stubs and TODOs fail with `[not-implemented]`
- **Intent over letter** — Passing assertion while violating intent still fails

---

## Alternative Runners

The skill includes runners for multiple LLM CLIs. All share the same test format and judge prompt.

| Runner | CLI | Non-interactive flag | Default model |
|--------|-----|---------------------|---------------|
| `run_tests_claude.py` | claude | `-p` | sonnet |
| `run_tests_opencode.py` | opencode | `run` | sonnet-class |
| `run_tests_codex.py` | codex | `exec` | gpt-5.2-codex |

Copy the runner for your preferred CLI:
```bash
cp "${CLAUDE_PLUGIN_ROOT}/scripts/run_tests_<cli>.py" specs/tests/
cp "${CLAUDE_PLUGIN_ROOT}/scripts/judge_prompt.md" specs/tests/
```

---

## Template Variables

If customizing `judge_prompt.md`, these placeholders are available:

| Variable | Content |
|----------|---------|
| `{{target_name}}` | Filename being tested |
| `{{target_content}}` | Full content of target file |
| `{{test_name}}` | H3 header (test case name) |
| `{{test_section}}` | H2 header (test group name) |
| `{{intent}}` | Intent statement text |
| `{{assertion_block}}` | Code block content |
