#!/usr/bin/env python3
"""
LLM-as-Judge Test Runner

Evaluates spec tests that require semantic understanding, not just assertion matching.
Uses `claude -p` to judge whether a target file/implementation satisfies the intent
and assertions in each test.

Usage:
    python run_tests_claude.py specs/tests/auth.md           # Target from frontmatter
    python run_tests_claude.py specs/tests/                  # All .md files in directory
    python run_tests_claude.py spec.md --target file.py      # Override frontmatter target

Spec files must declare target(s) in YAML frontmatter:
    ---
    target: src/auth.py
    ---

    ---
    target:
      - src/auth.py
      - src/session.py
    ---

Requirements:
    - claude CLI installed and authenticated
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Prompt template file location (sibling to this script)
JUDGE_PROMPT_FILE = Path(__file__).parent / "judge_prompt.md"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from markdown content.

    Returns (metadata dict, content without frontmatter).
    Frontmatter must be delimited by --- at start and end.
    """
    if not content.startswith('---'):
        return {}, content

    # Find the closing ---
    end_match = re.search(r'\n---\s*\n', content[3:])
    if not end_match:
        return {}, content

    frontmatter_text = content[3:end_match.start() + 3]
    remaining_content = content[end_match.end() + 3:]

    # Simple YAML parsing for target field (avoid yaml dependency)
    metadata = {}
    lines = frontmatter_text.strip().split('\n')
    current_key = None
    current_list = []

    for line in lines:
        # Array item
        if line.strip().startswith('- '):
            if current_key:
                current_list.append(line.strip()[2:].strip())
        # Key-value pair
        elif ':' in line and not line.startswith(' ') and not line.startswith('\t'):
            # Save previous list if any
            if current_key and current_list:
                metadata[current_key] = current_list
                current_list = []

            key, _, value = line.partition(':')
            current_key = key.strip()
            value = value.strip()
            if value:
                metadata[current_key] = value
                current_key = None

    # Save final list if any
    if current_key and current_list:
        metadata[current_key] = current_list

    return metadata, remaining_content


def get_targets_from_frontmatter(spec_path: Path) -> list[Path]:
    """
    Extract target file paths from spec file frontmatter.

    Supports both single target and array syntax:
        target: src/auth.py
        target:
          - src/auth.py
          - src/session.py

    Returns list of Path objects. Raises SystemExit on error.
    """
    content = spec_path.read_text()
    metadata, _ = parse_frontmatter(content)

    if 'target' not in metadata:
        print(f"Error: [missing-target] No 'target:' field in frontmatter of {spec_path}")
        print("Each spec file must declare its target(s) in frontmatter:")
        print("---")
        print("target: path/to/file.py")
        print("---")
        sys.exit(1)

    target = metadata['target']

    # Normalize to list
    if isinstance(target, str):
        targets = [target]
    else:
        targets = target

    # Convert to Paths and validate
    target_paths = []
    for t in targets:
        path = Path(t)
        if not path.exists():
            print(f"Error: Target file not found: {t}")
            print(f"  (declared in {spec_path})")
            sys.exit(1)
        target_paths.append(path)

    return target_paths


@dataclass
class TestCase:
    """A single test case extracted from the spec file."""
    name: str
    section: str
    intent: str
    assertion_block: str
    line_number: int
    missing_intent: bool = False  # True if test has assertion but no intent


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
        # Strip frontmatter if present
        _, content_without_frontmatter = parse_frontmatter(content)
        self.content = content_without_frontmatter
        self.lines = self.content.split('\n')

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

                # Include test if it has an assertion block (even without intent)
                # Missing intent will be flagged as a failure during evaluation
                if assertion_block:
                    tests.append(TestCase(
                        name=test_name,
                        section=current_section,
                        intent=intent,
                        assertion_block=assertion_block,
                        line_number=test_line,
                        missing_intent=not intent
                    ))
                continue

            i += 1

        return tests


class LLMJudge:
    """Uses claude CLI to evaluate test cases against a target."""

    def __init__(self, model: str = "sonnet"):
        self.model = model
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the judge prompt template from the external markdown file."""
        if not JUDGE_PROMPT_FILE.exists():
            raise FileNotFoundError(
                f"Judge prompt file not found: {JUDGE_PROMPT_FILE}\n"
                f"This file must be present alongside run_tests_claude.py"
            )
        return JUDGE_PROMPT_FILE.read_text()

    def _render_prompt(self, test: TestCase, target_content: str, target_name: str) -> str:
        """Substitute placeholders in the prompt template."""
        return (
            self._prompt_template
            .replace("{{target_name}}", target_name)
            .replace("{{target_content}}", target_content)
            .replace("{{test_name}}", test.name)
            .replace("{{test_section}}", test.section)
            .replace("{{intent}}", test.intent)
            .replace("{{assertion_block}}", test.assertion_block)
        )

    def evaluate(self, test: TestCase, target_content: str, target_name: str) -> TestResult:
        """Evaluate a single test case against the target content."""

        # Fail immediately if intent is missing - don't even call the LLM
        if test.missing_intent:
            return TestResult(
                test=test,
                passed=False,
                reasoning="[missing-intent] Test has no intent prose. Each test requires "
                          "intent explaining WHY it matters. Add prose between the H3 header "
                          "and the code block."
            )

        prompt = self._render_prompt(test, target_content, target_name)

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

    def __init__(self, spec_path: Path, target_paths: list[Path], model: str = "sonnet"):
        self.spec_path = spec_path
        self.target_paths = target_paths
        self.judge = LLMJudge(model=model)

    def _load_targets(self) -> tuple[str, str]:
        """Load and concatenate target file contents. Returns (content, display_name)."""
        if len(self.target_paths) == 1:
            return self.target_paths[0].read_text(), self.target_paths[0].name

        # Multiple targets - concatenate with headers
        parts = []
        names = []
        for path in self.target_paths:
            parts.append(f"# File: {path}\n\n{path.read_text()}")
            names.append(path.name)
        return "\n\n---\n\n".join(parts), ", ".join(names)

    def run(self) -> tuple[int, int]:
        """Run all tests and return (passed, total) counts."""

        # Load files
        spec_content = self.spec_path.read_text()
        target_content, target_name = self._load_targets()

        # Parse tests
        parser = SpecParser(spec_content)
        tests = parser.parse()

        if not tests:
            print(f"{self.YELLOW}No tests found in {self.spec_path}{self.RESET}")
            return 0, 0

        # Format target display
        if len(self.target_paths) == 1:
            target_display = str(self.target_paths[0])
        else:
            target_display = f"{len(self.target_paths)} files: {', '.join(str(p) for p in self.target_paths)}"

        print(f"\n{self.BOLD}Running LLM-as-Judge Tests{self.RESET}")
        print(f"Spec: {self.spec_path}")
        print(f"Target: {target_display}")
        print(f"Tests: {len(tests)}")
        print("-" * 60)

        passed = 0
        failed = 0

        for test in tests:
            print(f"\n{self.CYAN}{test.section}{self.RESET} > {test.name} ... ", end="", flush=True)

            result = self.judge.evaluate(test, target_content, target_name)

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
    parser.add_argument("--target", type=Path, help="Override target file (normally read from frontmatter)")
    parser.add_argument("--model", default="sonnet", help="Claude model to use (default: sonnet)")

    args = parser.parse_args()

    if not args.spec_path.exists():
        print(f"Error: Spec path not found: {args.spec_path}")
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
        # Get targets from frontmatter (or use CLI override)
        if args.target:
            if not args.target.exists():
                print(f"Error: Target file not found: {args.target}")
                sys.exit(1)
            target_paths = [args.target]
        else:
            target_paths = get_targets_from_frontmatter(spec_file)

        runner = TestRunner(spec_file, target_paths, model=args.model)
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
