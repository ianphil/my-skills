**Findings**
- High: `skills/spec-tests/scripts/run_tests_opencode.py:286` uses `opencode run --format default`, which appears to post-process output; the observed response `python\nend_match = ...` looks like a stripped code block, so any JSON the model emitted may be dropped before parsing, causing `JSONDecodeError`.
- Medium: `skills/spec-tests/scripts/judge_prompt.md:46-78` and `skills/spec-tests/scripts/judge_prompt.md:82-107` include multiple fenced code examples, which can prime models to answer in code blocks despite the “JSON only” directive; if opencode “default” formatting prefers code blocks, the JSON can be lost.
- Low: `skills/spec-tests/scripts/run_tests_opencode.py:330-336` treats any non-JSON output as a hard error with no retry or fallback; one non-compliant response turns into an ERROR rather than a FAIL, making the suite flaky even if the model mostly complies.

**Open Questions**
- Should the opencode runner be allowed to use a raw/JSON output format instead of `--format default`, or do we need to harden the prompt to explicitly forbid code blocks and language tags?

**Change Summary**
- No changes made.
