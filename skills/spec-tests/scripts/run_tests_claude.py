#!/usr/bin/env python3
"""
LLM-as-Judge Test Runner

Evaluates spec tests that require semantic understanding, not just assertion matching.
Uses `claude -p` to judge whether a target file/implementation satisfies the intent
and assertions in each test.

Usage:
    python run_tests_claude.py <spec.md> --target <file>      # Single spec file
    python run_tests_claude.py <tests/> --target <file>       # All .md files in directory
    python run_tests_claude.py tests/ --target SKILL.md       # Example: run all tests

Requirements:
    - claude CLI installed and authenticated
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TestCase:
    """A single test case extracted from the spec file."""
    name: str
    section: str
    intent: str
    assertion_block: str
    line_number: int


@dataclass
class TestResult:
    """Result of evaluating a test case."""
    test: TestCase
    passed: bool
    reasoning: str
    error: Optional[str] = None


class SpecParser:
    """Parses markdown spec files into test cases."""

    def __init__(self, content: str):
        self.content = content
        self.lines = content.split('\n')

    def parse(self) -> list[TestCase]:
        """Extract all test cases from the spec file."""
        tests = []
        current_section = ""
        i = 0

        while i < len(self.lines):
            line = self.lines[i]

            # Track H2 sections
            if line.startswith('## '):
                current_section = line[3:].strip()
                i += 1
                continue

            # Found H3 test case
            if line.startswith('### '):
                test_name = line[4:].strip()
                test_line = i + 1
                i += 1

                # Collect intent prose until we hit a code block
                intent_lines = []
                while i < len(self.lines) and not self.lines[i].startswith('```'):
                    if self.lines[i].strip():  # Skip empty lines for intent
                        intent_lines.append(self.lines[i])
                    i += 1

                intent = '\n'.join(intent_lines).strip()

                # Collect the code block (assertion)
                assertion_lines = []
                if i < len(self.lines) and self.lines[i].startswith('```'):
                    i += 1  # Skip opening ```
                    while i < len(self.lines) and not self.lines[i].startswith('```'):
                        assertion_lines.append(self.lines[i])
                        i += 1
                    i += 1  # Skip closing ```

                assertion_block = '\n'.join(assertion_lines).strip()

                if intent and assertion_block:
                    tests.append(TestCase(
                        name=test_name,
                        section=current_section,
                        intent=intent,
                        assertion_block=assertion_block,
                        line_number=test_line
                    ))
                continue

            i += 1

        return tests


class LLMJudge:
    """Uses claude CLI to evaluate test cases against a target."""

    def __init__(self, model: str = "sonnet"):
        self.model = model

    def evaluate(self, test: TestCase, target_content: str, target_name: str) -> TestResult:
        """Evaluate a single test case against the target content."""

        prompt = f"""You are a test evaluator. Determine if a target file satisfies a test specification.

## Target File: {target_name}

```
{target_content}
```

## Test to Evaluate

**Test Name:** {test.name}
**Section:** {test.section}

**Intent (WHY this test matters):**
{test.intent}

**Assertion (WHAT must be true):**
```
{test.assertion_block}
```

## Your Task

Evaluate whether the target file satisfies BOTH:
1. The intent (the underlying reason/requirement)
2. The assertion (the specific condition)

Be strict: if the target doesn't clearly satisfy the requirement, it fails.

Respond with ONLY a JSON object, no other text:
{{"passed": true, "reasoning": "why it passed"}}
or
{{"passed": false, "reasoning": "why it failed"}}"""

        try:
            result = subprocess.run(
                [
                    "claude", "-p",
                    "--output-format", "text",
                    "--model", self.model,
                    prompt
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                return TestResult(
                    test=test,
                    passed=False,
                    reasoning="",
                    error=f"claude CLI failed: {result.stderr}"
                )

            response_text = result.stdout.strip()

            # Extract JSON from response (handle markdown code blocks)
            if '```' in response_text:
                # Find JSON between code blocks
                import re
                match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', response_text, re.DOTALL)
                if match:
                    response_text = match.group(1).strip()

            # Try to find JSON object in response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                response_text = response_text[json_start:json_end]

            parsed = json.loads(response_text)

            return TestResult(
                test=test,
                passed=parsed.get('passed', False),
                reasoning=parsed.get('reasoning', 'No reasoning provided')
            )

        except json.JSONDecodeError as e:
            return TestResult(
                test=test,
                passed=False,
                reasoning="",
                error=f"Failed to parse response as JSON: {e}\nResponse: {response_text[:500]}"
            )
        except subprocess.TimeoutExpired:
            return TestResult(
                test=test,
                passed=False,
                reasoning="",
                error="claude CLI timed out after 120 seconds"
            )
        except Exception as e:
            return TestResult(
                test=test,
                passed=False,
                reasoning="",
                error=f"Evaluation failed: {e}"
            )


class TestRunner:
    """Runs all tests and reports results."""

    # ANSI colors
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def __init__(self, spec_path: Path, target_path: Path, model: str = "sonnet"):
        self.spec_path = spec_path
        self.target_path = target_path
        self.judge = LLMJudge(model=model)

    def run(self) -> tuple[int, int]:
        """Run all tests and return (passed, total) counts."""

        # Load files
        spec_content = self.spec_path.read_text()
        target_content = self.target_path.read_text()

        # Parse tests
        parser = SpecParser(spec_content)
        tests = parser.parse()

        if not tests:
            print(f"{self.YELLOW}No tests found in {self.spec_path}{self.RESET}")
            return 0, 0

        print(f"\n{self.BOLD}Running LLM-as-Judge Tests{self.RESET}")
        print(f"Spec: {self.spec_path}")
        print(f"Target: {self.target_path}")
        print(f"Tests: {len(tests)}")
        print("-" * 60)

        passed = 0
        failed = 0

        for test in tests:
            print(f"\n{self.CYAN}{test.section}{self.RESET} > {test.name} ... ", end="", flush=True)

            result = self.judge.evaluate(test, target_content, self.target_path.name)

            if result.error:
                status = f"{self.RED}ERROR{self.RESET}"
                failed += 1
            elif result.passed:
                status = f"{self.GREEN}PASS{self.RESET}"
                passed += 1
            else:
                status = f"{self.RED}FAIL{self.RESET}"
                failed += 1

            print(status)

            if result.error:
                print(f"  {self.RED}{result.error}{self.RESET}")
            elif not result.passed:
                print(f"  {result.reasoning}")

        # Summary
        print("\n" + "=" * 60)
        if failed == 0:
            print(f"{self.GREEN}{self.BOLD}All {passed} tests passed{self.RESET}")
        else:
            print(f"{self.RED}{self.BOLD}{failed} failed{self.RESET}, {self.GREEN}{passed} passed{self.RESET}")

        return passed, len(tests)


def main():
    parser = argparse.ArgumentParser(
        description="LLM-as-Judge test runner using claude CLI"
    )
    parser.add_argument("spec_path", type=Path, help="Path to spec test file or directory of .md files")
    parser.add_argument("--target", type=Path, required=True, help="Path to the file being tested")
    parser.add_argument("--model", default="sonnet", help="Claude model to use (default: sonnet)")

    args = parser.parse_args()

    if not args.spec_path.exists():
        print(f"Error: Spec path not found: {args.spec_path}")
        sys.exit(1)

    if not args.target.exists():
        print(f"Error: Target file not found: {args.target}")
        sys.exit(1)

    # Check claude CLI is available
    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: claude CLI not found or not working")
        sys.exit(1)

    # Collect spec files
    if args.spec_path.is_dir():
        spec_files = sorted(args.spec_path.glob("*.md"))
        if not spec_files:
            print(f"Error: No .md files found in {args.spec_path}")
            sys.exit(1)
    else:
        spec_files = [args.spec_path]

    # Run all spec files
    total_passed = 0
    total_tests = 0

    for spec_file in spec_files:
        runner = TestRunner(spec_file, args.target, model=args.model)
        passed, total = runner.run()
        total_passed += passed
        total_tests += total

    # Final summary if multiple files
    if len(spec_files) > 1:
        print(f"\n{'=' * 60}")
        print(f"TOTAL: {len(spec_files)} spec files, {total_tests} tests")
        if total_passed == total_tests:
            print(f"\033[92m\033[1mAll {total_passed} tests passed\033[0m")
        else:
            failed = total_tests - total_passed
            print(f"\033[91m\033[1m{failed} failed\033[0m, \033[92m{total_passed} passed\033[0m")

    sys.exit(0 if total_passed == total_tests else 1)


if __name__ == "__main__":
    main()
