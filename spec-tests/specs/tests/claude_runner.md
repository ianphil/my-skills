---
target: scripts/run_tests_claude.py
---
# Claude CLI Runner

Tests specific to the `claude` CLI integration. These tests would need to be
updated or replaced when adding support for alternative LLM CLIs.

---

## CLI Invocation

### Invokes Claude CLI

The runner uses `claude -p` so users don't need API keys—just their existing
Claude subscription. This is the implementation detail that makes the runner
claude-specific.

```
Given the run_tests_claude.py runner
Then the LLMJudge class invokes claude via subprocess with:
  - "claude" as the command
  - "-p" flag for prompt mode
Because users shouldn't need separate API billing to run spec tests
```
