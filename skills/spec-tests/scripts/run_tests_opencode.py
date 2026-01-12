#!/usr/bin/env python3
"""
LLM-as-Judge Test Runner (opencode)

Evaluates spec tests that require semantic understanding, not just assertion matching.
Uses `opencode run` to judge whether a target file/implementation satisfies the intent
and assertions in each test.

Usage:
    python run_tests_opencode.py specs/tests/auth.md           # Target from frontmatter
    python run_tests_opencode.py specs/tests/                  # All .md files in directory
    python run_tests_opencode.py spec.md --target file.py      # Override frontmatter target

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
    - opencode CLI installed and authenticated
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
OPENCODE_FORMAT = "json"
RUN_TIMEOUT = 180


# ============================================================================
# JSON Extraction Helpers
# NOTE: This code is intentionally duplicated across all three runners
# (run_tests_opencode.py, run_tests_claude.py, run_tests_codex.py) to maintain
# portability. Each runner must be self-contained as a single file.
# ============================================================================


class JSONExtractionError(Exception):
    """Raised when JSON cannot be extracted from LLM response."""

    pass


def _extract_json_pure(text: str) -> dict:
    """Strategy 1: Assume response is pure JSON."""
    return json.loads(text.strip())


def _extract_json_from_code_block(text: str) -> dict:
    """Strategy 2: Extract from markdown code block."""
    if "```" not in text:
        raise ValueError("No code block markers found")

    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if not match:
        raise ValueError("Code block markers present but pattern didn't match")

    return json.loads(match.group(1).strip())


def _extract_json_balanced_braces(text: str) -> dict:
    """
    Strategy 3: Extract balanced JSON object using brace counting.

    This fixes the nested object bug by properly tracking brace depth
    and respecting string boundaries.
    """
    start = text.find("{")
    if start < 0:
        raise ValueError("No opening brace found")

    depth = 0
    in_string = False
    escape_next = False

    for i in range(start, len(text)):
        char = text[i]

        # Handle escape sequences
        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue

        # Track string boundaries (braces inside strings don't count)
        if char == '"':
            in_string = not in_string
            continue

        # Count braces only outside strings
        if not in_string:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    # Found matching closing brace
                    json_text = text[start : i + 1]
                    return json.loads(json_text)

    raise ValueError(f"No matching closing brace found (depth={depth})")


def _extract_json_lenient(text: str) -> dict:
    """Strategy 4: Try with aggressive whitespace/prefix removal."""
    cleaned = text.strip()

    # Remove common LLM response prefixes
    prefixes = [
        "Here's the JSON:",
        "Here is the JSON:",
        "Response:",
        "Output:",
    ]
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()

    return _extract_json_balanced_braces(cleaned)


def extract_judge_response_json(response_text: str) -> dict:
    """
    Extract and parse JSON from LLM response using multiple strategies.

    Tries strategies in order:
    1. Pure JSON (no wrapping)
    2. Markdown code block
    3. Balanced brace extraction (handles nested objects)
    4. Lenient (with prefix removal)

    Args:
        response_text: Raw text from LLM

    Returns:
        Parsed JSON dictionary with 'passed' and 'reasoning' keys

    Raises:
        JSONExtractionError: If JSON cannot be extracted/parsed or schema is invalid
    """
    if not response_text or not response_text.strip():
        raise JSONExtractionError("Empty response from LLM")

    strategies = [
        ("pure JSON", _extract_json_pure),
        ("code block", _extract_json_from_code_block),
        ("balanced braces", _extract_json_balanced_braces),
        ("lenient", _extract_json_lenient),
    ]

    errors = []
    for strategy_name, strategy_func in strategies:
        try:
            data = strategy_func(response_text)

            # Validate schema
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict, got {type(data).__name__}")
            if "passed" not in data:
                raise ValueError("Missing required field: 'passed'")
            if not isinstance(data["passed"], bool):
                raise ValueError(
                    f"Field 'passed' must be bool, got {type(data['passed']).__name__}"
                )

            # 'reasoning' is optional, use default if missing
            if "reasoning" not in data:
                data["reasoning"] = "No reasoning provided"
            elif not isinstance(data["reasoning"], str):
                raise ValueError(
                    f"Field 'reasoning' must be string, got {type(data['reasoning']).__name__}"
                )

            return data

        except (json.JSONDecodeError, ValueError) as e:
            errors.append(f"{strategy_name}: {e}")
            continue

    # All strategies failed
    preview = response_text[:200].replace("\n", "\\n")
    error_details = "\n  ".join(errors)
    raise JSONExtractionError(
        f"Failed to extract JSON using all strategies:\n  {error_details}\n"
        f"Response preview: {preview}..."
    )


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """
    Parse YAML frontmatter from markdown content.

    Returns (metadata dict, content without frontmatter).
    Frontmatter must be delimited by --- at start and end.
    """
    if not content.startswith("---"):
        return {}, content

    # Find the closing ---
    end_match = re.search(r"\n---\s*(?:\n|$)", content[3:])
    if not end_match:
        return {}, content

    frontmatter_text = content[3 : end_match.start() + 3]
    remaining_content = content[end_match.end() + 3 :]

    # Simple YAML parsing for target field (avoid yaml dependency)
    metadata = {}
    lines = frontmatter_text.strip().split("\n")
    current_key = None
    current_list = []

    for line in lines:
        # Array item
        if line.strip().startswith("- "):
            if current_key:
                current_list.append(line.strip()[2:].strip())
        # Key-value pair
        elif ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            # Save previous list if any
            if current_key and current_list:
                metadata[current_key] = current_list
                current_list = []

            key, _, value = line.partition(":")
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

    if "target" not in metadata:
        print(
            f"Error: [missing-target] No 'target:' field in frontmatter of {spec_path}"
        )
        print("Each spec file must declare its target(s) in frontmatter:")
        print("---")
        print("target: path/to/file.py")
        print("---")
        sys.exit(1)

    target = metadata["target"]

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
    missing_assertion: bool = False  # True if test has no code block


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
        self.lines = self.content.split("\n")

    def parse(self) -> list[TestCase]:
        """Extract all test cases from the spec file."""
        tests = []
        current_section = ""
        i = 0

        while i < len(self.lines):
            line = self.lines[i]

            # Track H2 sections
            if line.startswith("## "):
                current_section = line[3:].strip()
                i += 1
                continue

            # Found H3 test case
            if line.startswith("### "):
                test_name = line[4:].strip()
                test_line = i + 1
                i += 1

                # Collect intent statement until we hit a code block
                intent_lines = []
                missing_assertion = False
                while i < len(self.lines):
                    if self.lines[i].startswith("```"):
                        break
                    if self.lines[i].startswith("## ") or self.lines[i].startswith(
                        "### "
                    ):
                        missing_assertion = True
                        break
                    if self.lines[i].strip():  # Skip empty lines for intent
                        intent_lines.append(self.lines[i])
                    i += 1

                intent = "\n".join(intent_lines).strip()

                # Collect the code block (assertion)
                assertion_lines = []
                if i < len(self.lines) and self.lines[i].startswith("```"):
                    i += 1  # Skip opening ```
                    while i < len(self.lines) and not self.lines[i].startswith("```"):
                        assertion_lines.append(self.lines[i])
                        i += 1
                    i += 1  # Skip closing ```
                else:
                    missing_assertion = True

                assertion_block = "\n".join(assertion_lines).strip()

                # Include test if it has an assertion block (even without intent)
                # Missing intent will be flagged as a failure during evaluation
                if assertion_block or missing_assertion:
                    tests.append(
                        TestCase(
                            name=test_name,
                            section=current_section,
                            intent=intent,
                            assertion_block=assertion_block,
                            line_number=test_line,
                            missing_intent=not intent,
                            missing_assertion=missing_assertion,
                        )
                    )
                continue

            i += 1

        return tests


class LLMJudge:
    """Uses opencode CLI to evaluate test cases against a target."""

    def __init__(self, model: str = "github-copilot/claude-sonnet-4.5"):
        self.model = model
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the judge prompt template from the external markdown file."""
        if not JUDGE_PROMPT_FILE.exists():
            raise FileNotFoundError(
                f"Judge prompt file not found: {JUDGE_PROMPT_FILE}\n"
                f"This file must be present alongside run_tests_opencode.py"
            )
        return JUDGE_PROMPT_FILE.read_text()

    def _render_prompt(
        self, test: TestCase, target_content: str, target_name: str
    ) -> str:
        """Substitute placeholders in the prompt template."""
        return (
            self._prompt_template.replace("{{target_name}}", target_name)
            .replace("{{target_content}}", target_content)
            .replace("{{test_name}}", test.name)
            .replace("{{test_section}}", test.section)
            .replace("{{intent}}", test.intent)
            .replace("{{assertion_block}}", test.assertion_block)
        )

    def _extract_text_from_events(self, output: str) -> tuple[str, list[str]]:
        """Extract text from opencode JSON event stream."""
        text_parts = []
        event_errors = []
        for line in output.splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_type = event.get("type")
            if event_type == "text":
                part = event.get("part", {})
                text = part.get("text")
                if text:
                    text_parts.append(text)
            elif event_type == "error":
                event_errors.append(event.get("error") or str(event))
        return "".join(text_parts).strip(), event_errors

    def evaluate(
        self, test: TestCase, target_content: str, target_name: str
    ) -> TestResult:
        """Evaluate a single test case against the target content."""

        # Fail immediately if intent is missing - don't even call the LLM
        if test.missing_assertion:
            return TestResult(
                test=test,
                passed=False,
                reasoning="[missing-assertion] Test has no assertion code block. Add a "
                "fenced code block after the intent.",
            )

        # Fail immediately if intent is missing - don't even call the LLM
        if test.missing_intent:
            return TestResult(
                test=test,
                passed=False,
                reasoning="[missing-intent] Test has no intent statement. Each test requires "
                "intent explaining WHY it matters. Add statement between the H3 header "
                "and the code block.",
            )

        prompt = self._render_prompt(test, target_content, target_name)
        retry_prompt_suffix = (
            "\n\nREMINDER: Output ONLY a JSON object. No markdown, no code fences."
        )
        max_retries = 2

        try:
            response_text = ""
            last_error = ""
            for attempt in range(max_retries):
                run_prompt = prompt if attempt == 0 else prompt + retry_prompt_suffix
                result = subprocess.run(
                    [
                        "opencode",
                        "run",
                        "-m",
                        self.model,
                        "--format",
                        OPENCODE_FORMAT,
                    ],
                    input=run_prompt,
                    capture_output=True,
                    text=True,
                    timeout=RUN_TIMEOUT,
                )

                if result.returncode != 0:
                    return TestResult(
                        test=test,
                        passed=False,
                        reasoning="",
                        error=f"opencode CLI failed: {result.stderr}",
                    )

                response_text = result.stdout.strip()
                event_errors = []
                if OPENCODE_FORMAT == "json":
                    response_text, event_errors = self._extract_text_from_events(
                        response_text
                    )
                    if event_errors and not response_text:
                        last_error = f"opencode event error: {event_errors[0]}"
                        continue

                if not response_text:
                    last_error = "opencode returned empty response"
                    continue

                # Extract and validate JSON from response
                try:
                    parsed = extract_judge_response_json(response_text)
                    return TestResult(
                        test=test,
                        passed=parsed["passed"],
                        reasoning=parsed["reasoning"],
                    )
                except JSONExtractionError as e:
                    last_error = f"JSON extraction failed: {e}"
                    continue

            # Final failure after all retries
            preview_len = 300
            response_preview = (
                response_text[:preview_len] if response_text else "(empty)"
            )
            if response_text and len(response_text) > preview_len:
                response_preview += f"... ({len(response_text)} chars total)"

            return TestResult(
                test=test,
                passed=False,
                reasoning="",
                error=(
                    f"Failed to extract valid JSON after {max_retries} attempts.\n"
                    f"Last error: {last_error}\n\n"
                    f"Response received:\n{response_preview}"
                ),
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                test=test,
                passed=False,
                reasoning="",
                error=f"opencode CLI timed out after {RUN_TIMEOUT} seconds",
            )
        except Exception as e:
            return TestResult(
                test=test, passed=False, reasoning="", error=f"Evaluation failed: {e}"
            )


class TestRunner:
    """Runs all tests and reports results."""

    # ANSI colors
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(
        self,
        spec_path: Path,
        target_paths: list[Path],
        model: str = "github-copilot/claude-sonnet-4.5",
        test_filter: str = None,
    ):
        self.spec_path = spec_path
        self.target_paths = target_paths
        self.test_filter = test_filter
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

        # Filter by test name if specified
        if self.test_filter:
            tests = [t for t in tests if t.name == self.test_filter]
            if not tests:
                print(
                    f"{self.YELLOW}No test named '{self.test_filter}' found{self.RESET}"
                )
                return 0, 0

        # Format target display
        if len(self.target_paths) == 1:
            target_display = str(self.target_paths[0])
        else:
            target_display = f"{len(self.target_paths)} files: {', '.join(str(p) for p in self.target_paths)}"

        print(f"\n{self.BOLD}Running LLM-as-Judge Tests (opencode){self.RESET}")
        print(f"Spec: {self.spec_path}")
        print(f"Target: {target_display}")
        print(f"Tests: {len(tests)}")
        print("-" * 60)

        passed = 0
        failed = 0

        for test in tests:
            print(
                f"\n{self.CYAN}{test.section}{self.RESET} > {test.name} ... ",
                end="",
                flush=True,
            )

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
            print(
                f"{self.RED}{self.BOLD}{failed} failed{self.RESET}, {self.GREEN}{passed} passed{self.RESET}"
            )

        return passed, len(tests)


def main():
    parser = argparse.ArgumentParser(
        description="LLM-as-Judge test runner using opencode CLI"
    )
    parser.add_argument(
        "spec_path", type=Path, help="Path to spec test file or directory of .md files"
    )
    parser.add_argument(
        "--target",
        type=Path,
        help="Override target file (normally read from frontmatter)",
    )
    parser.add_argument(
        "--model",
        default="github-copilot/claude-sonnet-4.5",
        help="Model to use in provider/model format (default: github-copilot/claude-sonnet-4.5)",
    )
    parser.add_argument("--test", help="Run only the test with this name (exact match)")

    args = parser.parse_args()

    if not args.spec_path.exists():
        print(f"Error: Spec path not found: {args.spec_path}")
        sys.exit(1)

    # Check opencode CLI is available
    try:
        subprocess.run(["opencode", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: opencode CLI not found or not working")
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

        runner = TestRunner(
            spec_file, target_paths, model=args.model, test_filter=args.test
        )
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
            print(
                f"\033[91m\033[1m{failed} failed\033[0m, \033[92m{total_passed} passed\033[0m"
            )

    sys.exit(0 if total_passed == total_tests else 1)


if __name__ == "__main__":
    main()
