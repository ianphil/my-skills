# Review: run_tests_opencode.py

**Reviewer:** Claude Sonnet  
**Date:** 2026-01-11  
**Overall Grade:** A-

## Summary

Production-ready test runner with thoughtful error handling and good UX. Clean separation of concerns, robust frontmatter parsing, and comprehensive validation. Minor improvements needed for JSON extraction robustness, progress feedback, and parallel execution.

---

## Architecture & Design ✓

**Strengths:**
- Clean separation: `SpecParser`, `LLMJudge`, `TestRunner` have distinct responsibilities
- Uses `opencode run` with JSON event streaming for LLM evaluation
- Handles both single and multiple target files elegantly
- Comprehensive error handling with specific failure modes (`[missing-intent]`, `[missing-assertion]`, `[missing-target]`)
- Early validation: fails fast for missing intent/assertions without calling LLM

---

## Issues & Improvements

### 1. Regex-based JSON extraction (lines 351-361)

**Issue:** The fallback `find('{')` / `rfind('}')` can extract incomplete JSON if there are nested objects.

```python
# Current approach
json_start = response_text.find('{')
json_end = response_text.rfind('}') + 1
if json_start >= 0 and json_end > json_start:
    response_text = response_text[json_start:json_end]
```

**Risk:** Extracts `{"passed": true}` from `{"outer": {"passed": true}, "reasoning": "..."}`.

**Recommendation:** Use a proper JSON decoder or be stricter about format requirements. Consider rejecting responses that require extraction after retry exhaustion.

---

### 2. Hardcoded model default (line 239, 409, 503)

**Issue:** `claude-sonnet-4.5` may not exist—is this future-proofing?

```python
def __init__(self, model: str = "github-copilot/claude-sonnet-4.5"):
```

**Recommendation:**
- Document which models are tested/supported
- Validate model format on startup:
  ```python
  if "/" not in args.model:
      print(f"Error: Model must be in provider/model format")
      sys.exit(1)
  ```

---

### 3. Missing progress indicator for long tests

**Issue:** 180s timeout is reasonable, but no progress shown during LLM evaluation.

**Current:**
```python
print(f"\n{self.CYAN}{test.section}{self.RESET} > {test.name} ... ", end="", flush=True)
result = self.judge.evaluate(test, target_content, target_name)
```

**Enhancement:**
```python
print(f"\n{self.CYAN}{test.section}{self.RESET} > {test.name} ... ⏳ ", end="", flush=True)
result = self.judge.evaluate(test, target_content, target_name)
# Clear the spinner after evaluation
print("\033[2K\r", end="")  # Clear line
print(f"\n{self.CYAN}{test.section}{self.RESET} > {test.name} ... {status}")
```

---

### 4. Missing line numbers in error messages

**Issue:** Errors don't reference where in the spec file to fix the issue.

**Current (lines 298-305):**
```python
reasoning="[missing-intent] Test has no intent prose. Each test requires "
          "intent explaining WHY it matters. Add prose between the H3 header "
          "and the code block."
```

**Enhancement:**
```python
reasoning=(f"[missing-intent] Test at line {test.line_number} has no intent prose. "
           f"Each test requires intent explaining WHY it matters. Add prose between "
           f"the H3 header and the code block.")
```

Makes it easier to navigate to the failing test in the editor.

---

### 5. Timeout handling lacks context

**Current (lines 382-388):**
```python
except subprocess.TimeoutExpired:
    return TestResult(
        test=test,
        passed=False,
        reasoning="",
        error=f"opencode CLI timed out after {RUN_TIMEOUT} seconds"
    )
```

**Enhancement:**
```python
error=(f"opencode CLI timed out after {RUN_TIMEOUT} seconds\n"
       f"  Test: {test.name}\n"
       f"  Consider: Is the target file very large? Is the model responding?")
```

---

## Missing Features

### 1. Parallel test execution

**Current:** Tests run sequentially, blocking on each LLM evaluation.

**Enhancement:** Use `concurrent.futures` for parallel execution:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

# In TestRunner.run():
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(self.judge.evaluate, test, target_content, target_name): test 
               for test in tests}
    for future in as_completed(futures):
        result = future.result()
        # Process result
```

**Benefit:** 3x speedup for test suites with 10+ tests.

---

### 2. Verbose mode for debugging

**Enhancement:**
```python
parser.add_argument("-v", "--verbose", action="store_true", 
                    help="Show full LLM prompts and responses")

# In LLMJudge.evaluate():
if verbose:
    print(f"\n{'='*60}")
    print(f"PROMPT:\n{prompt}")
    print(f"\n{'='*60}")
    print(f"RESPONSE:\n{response_text}")
    print(f"{'='*60}\n")
```

---

### 3. Test discovery without execution

**Enhancement:**
```python
parser.add_argument("--list", action="store_true", 
                    help="List all tests without running them")

# In main():
if args.list:
    for spec_file in spec_files:
        tests = SpecParser(spec_file.read_text()).parse()
        print(f"\n{spec_file}:")
        for test in tests:
            status = "❌" if test.missing_intent else "✓"
            print(f"  {status} {test.section} > {test.name}")
    sys.exit(0)
```

---

### 4. Partial results on interrupt

**Issue:** Ctrl+C loses all progress.

**Enhancement:**
```python
import signal

def signal_handler(sig, frame):
    print(f"\n\n{self.YELLOW}Interrupted. Partial results:{self.RESET}")
    print(f"{self.GREEN}{passed} passed{self.RESET}, {self.RED}{failed} failed{self.RESET}")
    sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)
```

---

### 5. Target content caching

**Issue:** When multiple tests share targets, content is re-read for each test.

**Enhancement:**
```python
# In TestRunner.__init__():
self._target_cache = {}

def _load_targets(self) -> tuple[str, str]:
    cache_key = tuple(sorted(str(p) for p in self.target_paths))
    if cache_key in self._target_cache:
        return self._target_cache[cache_key]
    
    content, name = self._do_load_targets()
    self._target_cache[cache_key] = (content, name)
    return content, name
```

---

## Documentation Gaps

### 1. judge_prompt.md contents not reviewed

**Question:** What should the judge prompt template contain? Should review that file for completeness.

---

### 2. Model compatibility

**Missing documentation:**
- Which models are tested/supported?
- Is `claude-sonnet-4.5` actually available via opencode GitHub Copilot provider?
- What's the fallback if a model isn't available?

**Recommendation:** Add to SKILL.md:
```markdown
## Supported Models

Tested with:
- `github-copilot/claude-sonnet-4` (recommended)
- `github-copilot/gpt-4`

Check available models:
```bash
opencode run --help  # Should list providers/models
```

---

### 3. Rate limiting

**Missing:** No mention of handling API rate limits from opencode/GitHub Copilot.

**Enhancement:** Add retry logic with exponential backoff:
```python
if "rate limit" in result.stderr.lower():
    time.sleep(2 ** attempt)  # Exponential backoff
    continue
```

---

## Code Quality Highlights

### Excellent Practices

1. **Frontmatter parsing** (lines 44-91): Simple YAML parser avoids external dependencies while supporting both single and array target syntax

2. **Early validation** (lines 288-305): Fails fast for missing intent/assertions without calling the LLM—saves time and API costs

3. **Retry logic** (lines 312-373): Handles JSON extraction failures with prompt refinement—appends reminder on retry

4. **Event stream parsing** (lines 264-283): Robust extraction from `opencode` JSON events with error accumulation

5. **Clear user feedback**: Color-coded output with ANSI codes (lines 401-407)

6. **Multi-target concatenation** (lines 415-426): Elegant handling of multiple target files with separators

---

## Testing Recommendations

### Unit tests needed for:

1. **Frontmatter parser edge cases:**
   - Empty frontmatter
   - Nested YAML (should fail gracefully)
   - Missing closing `---`
   - Array vs string target values

2. **SpecParser edge cases:**
   - Test with no intent but has assertion
   - Test with intent but no assertion
   - Multiple consecutive H3 headers
   - Code blocks with nested backticks

3. **JSON extraction:**
   - Response with markdown code fences
   - Response with nested JSON objects
   - Response with text before/after JSON
   - Completely invalid JSON

---

## Priority Ranking

**High priority:**
1. Add line numbers to error messages (easy win)
2. Validate model format on startup (prevents confusing errors)
3. Document supported models (user-facing)

**Medium priority:**
4. Add verbose mode for debugging (developer UX)
5. Improve JSON extraction robustness (correctness)
6. Add progress indicators (user feedback)

**Low priority (nice to have):**
7. Parallel test execution (performance)
8. Test discovery mode (convenience)
9. Target content caching (minor optimization)
10. Graceful interrupt handling (edge case)

---

## Comparison Questions

**For reviewer:** Should compare with `run_tests_claude.py` to ensure feature parity:

1. Does the Claude runner have features this one lacks?
2. Are error messages consistent between runners?
3. Should both runners share a common base class?
4. Is the judge prompt the same for both?

---

## Final Verdict

**Production ready:** Yes, with minor improvements recommended.

**Blockers:** None. Current issues are quality-of-life improvements, not correctness problems.

**Next steps:**
1. Review `judge_prompt.md` for prompt quality
2. Verify model name (`claude-sonnet-4.5` vs `claude-sonnet-4`)
3. Add high-priority improvements (line numbers, model validation)
4. Consider refactoring shared code if both runners exist
