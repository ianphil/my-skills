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
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Prompt template file location (sibling to this script)
JUDGE_PROMPT_FILE = Path(__file__).parent / "judge_prompt.md"
FAILURE_FILE = Path(".spec-tests-failures.json")


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
    skipped: bool = False


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


def load_failures(failure_path: Path) -> list[dict]:
    if not failure_path.exists():
        return []
    try:
        data = json.loads(failure_path.read_text())
        return data.get("failures", [])
    except (json.JSONDecodeError, KeyError):
        return []


def save_failures(failure_path: Path, failures: list[dict]) -> None:
    if not failures:
        failure_path.unlink(missing_ok=True)
        return
    data = {"version": 1, "failures": failures}
    failure_path.write_text(json.dumps(data, indent=2) + "\n")


def build_ir_dict(spec_path: Path, target_paths: list[Path], tests: list[TestCase]) -> dict:
    """Build the inspectable intermediate representation as a plain dict."""
    return {
        "source": str(spec_path),
        "target": [str(p) for p in target_paths],
        "tests": [
            {
                "group": t.section,
                "name": t.name,
                "intent": t.intent,
                "assertion": t.assertion_block,
                "line_number": t.line_number,
                "missing_intent": t.missing_intent,
                "missing_assertion": t.missing_assertion,
            }
            for t in tests
        ],
    }


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

    def _render_prompt(self, test: TestCase, target_paths: list[Path]) -> str:
        """Substitute placeholders in the prompt template."""
        target_files = "\n".join(f"- {p.absolute()}" for p in target_paths)
        return (
            self._prompt_template.replace("{{target_files}}", target_files)
            .replace("{{test_name}}", test.name)
            .replace("{{test_section}}", test.section)
            .replace("{{intent}}", test.intent)
            .replace("{{assertion_block}}", test.assertion_block)
        )

    def evaluate(self, test: TestCase, target_paths: list[Path]) -> TestResult:
        """Evaluate a single test case against the target content."""

        # Skip immediately if assertion is missing - don't even call the LLM
        if test.missing_assertion:
            return TestResult(
                test=test,
                passed=False,
                reasoning="[missing-assertion] Test has no assertion code block. Add a "
                "fenced code block after the intent.",
                skipped=True,
            )

        # Skip immediately if intent is missing - don't even call the LLM
        if test.missing_intent:
            return TestResult(
                test=test,
                passed=False,
                reasoning="[missing-intent] Test has no intent statement. Each test requires "
                "intent explaining WHY it matters. Add statement between the H3 header "
                "and the code block.",
                skipped=True,
            )

        prompt = self._render_prompt(test, target_paths)

        max_retries = 3
        retry_delay = 2  # seconds

        try:
            result = None
            for attempt in range(max_retries):
                result = subprocess.run(
                    [
                        "claude",
                        "-p",
                        "--output-format",
                        "text",
                        "--model",
                        self.model,
                        prompt,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                # Retry on "[ACTION REQUIRED]" terms acceptance error
                if result.returncode != 0 and "[ACTION REQUIRED]" in result.stderr:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                break

            if result.returncode != 0:
                return TestResult(
                    test=test,
                    passed=False,
                    reasoning="",
                    error=f"claude CLI failed: {result.stderr}",
                )

            response_text = result.stdout.strip()

            # Extract and validate JSON from response
            try:
                parsed = extract_judge_response_json(response_text)
                return TestResult(
                    test=test,
                    passed=parsed["passed"],
                    reasoning=parsed["reasoning"],
                )
            except JSONExtractionError as e:
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
                        f"JSON extraction failed: {e}\n\n"
                        f"Response received:\n{response_preview}"
                    ),
                )

        except subprocess.TimeoutExpired:
            return TestResult(
                test=test,
                passed=False,
                reasoning="",
                error="claude CLI timed out after 120 seconds",
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
        model: str = "sonnet",
        test_filter: str = None,
        test_names_filter: list[str] = None,
    ):
        self.spec_path = spec_path
        self.target_paths = target_paths
        self.test_filter = test_filter
        self.test_names_filter = test_names_filter
        self.judge = LLMJudge(model=model)

    def _get_absolute_paths(self) -> list[Path]:
        """Return absolute paths to target files."""
        return [p.absolute() for p in self.target_paths]

    def run(self) -> tuple[int, int, int, list[str]]:
        """Run all tests and return (passed, failed, skipped, failed_names)."""

        # Load files
        spec_content = self.spec_path.read_text()
        target_paths = self._get_absolute_paths()

        # Parse tests
        parser = SpecParser(spec_content)
        tests = parser.parse()

        if not tests:
            print(f"{self.YELLOW}No tests found in {self.spec_path}{self.RESET}")
            return 0, 0, 0, []

        # Filter by test name if specified
        if self.test_filter:
            tests = [t for t in tests if t.name == self.test_filter]
            if not tests:
                print(
                    f"{self.YELLOW}No test named '{self.test_filter}' found{self.RESET}"
                )
                return 0, 0, 0, []

        # Filter by test names list (for --rerun-failed)
        if self.test_names_filter:
            tests = [t for t in tests if t.name in self.test_names_filter]
            if not tests:
                print(
                    f"{self.YELLOW}No matching failed tests in {self.spec_path}{self.RESET}"
                )
                return 0, 0, 0, []

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
        skipped = 0
        failed_names = []

        for test in tests:
            print(
                f"\n{self.spec_path}:{test.line_number} {self.CYAN}{test.section}{self.RESET} > {test.name} ... ",
                end="",
                flush=True,
            )

            result = self.judge.evaluate(test, target_paths)

            if result.skipped:
                status = f"{self.YELLOW}SKIP{self.RESET}"
                skipped += 1
            elif result.error:
                status = f"{self.RED}ERROR{self.RESET}"
                failed += 1
                failed_names.append(test.name)
            elif result.passed:
                status = f"{self.GREEN}PASS{self.RESET}"
                passed += 1
            else:
                status = f"{self.RED}FAIL{self.RESET}"
                failed += 1
                failed_names.append(test.name)

            print(status)

            if result.skipped:
                print(f"  {self.YELLOW}{result.reasoning}{self.RESET}")
            elif result.error:
                print(f"  {self.RED}{result.error}{self.RESET}")
            elif not result.passed:
                print(f"  {result.reasoning}")

        # Summary
        print("\n" + "=" * 60)
        summary_parts = []
        if passed:
            summary_parts.append(f"{self.GREEN}{passed} passed{self.RESET}")
        if failed:
            summary_parts.append(f"{self.RED}{failed} failed{self.RESET}")
        if skipped:
            summary_parts.append(f"{self.YELLOW}{skipped} skipped{self.RESET}")

        if failed == 0 and skipped == 0:
            print(f"{self.GREEN}{self.BOLD}All {passed} tests passed{self.RESET}")
        else:
            print(f"{self.BOLD}{', '.join(summary_parts)}{self.RESET}")

        return passed, failed, skipped, failed_names


def main():
    parser = argparse.ArgumentParser(
        description="LLM-as-Judge test runner using claude CLI"
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
        "--model", default="sonnet", help="Claude model to use (default: sonnet)"
    )
    parser.add_argument("--test", help="Run only the test with this name (exact match)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse spec and output IR as JSON without running LLM judge",
    )
    parser.add_argument(
        "--rerun-failed",
        action="store_true",
        help="Re-run only tests that failed in the previous run",
    )

    args = parser.parse_args()

    if args.rerun_failed and args.test:
        print("Error: --rerun-failed and --test are mutually exclusive")
        sys.exit(1)

    if not args.spec_path.exists():
        print(f"Error: Spec path not found: {args.spec_path}")
        sys.exit(1)

    if not args.dry_run:
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

    # Handle --rerun-failed
    rerun_filter = {}
    if args.rerun_failed:
        prev_failures = load_failures(FAILURE_FILE)
        if not prev_failures:
            print("No previous failures found. Nothing to re-run.")
            sys.exit(0)
        for entry in prev_failures:
            spec_key = entry.get("spec_file", "")
            test_name = entry.get("test_name", "")
            rerun_filter.setdefault(spec_key, set()).add(test_name)
        spec_files = [
            sf for sf in spec_files if str(sf.resolve()) in rerun_filter
        ]
        if not spec_files:
            print("No previous failures match current spec files. Nothing to re-run.")
            sys.exit(0)

    # Run all spec files
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    dry_run_results = []
    all_failures = []

    for spec_file in spec_files:
        # Get targets from frontmatter (or use CLI override)
        if args.target:
            if not args.target.exists():
                print(f"Error: Target file not found: {args.target}")
                sys.exit(1)
            target_paths = [args.target]
        else:
            target_paths = get_targets_from_frontmatter(spec_file)

        if args.dry_run:
            spec_content = spec_file.read_text()
            parser = SpecParser(spec_content)
            tests = parser.parse()
            if args.test:
                tests = [t for t in tests if t.name == args.test]
            dry_run_results.append(build_ir_dict(spec_file, target_paths, tests))
        else:
            names_filter = None
            if rerun_filter:
                resolved = str(spec_file.resolve())
                names_filter = list(rerun_filter.get(resolved, []))

            runner = TestRunner(
                spec_file,
                target_paths,
                model=args.model,
                test_filter=args.test,
                test_names_filter=names_filter,
            )
            passed, failed, skipped, failed_names = runner.run()
            total_passed += passed
            total_failed += failed
            total_skipped += skipped
            for name in failed_names:
                all_failures.append(
                    {"spec_file": str(spec_file.resolve()), "test_name": name}
                )

    if args.dry_run:
        if len(dry_run_results) == 1:
            print(json.dumps(dry_run_results[0], indent=2))
        else:
            print(json.dumps(dry_run_results, indent=2))
        sys.exit(0)

    # Save failure file
    save_failures(FAILURE_FILE, all_failures)
    if all_failures:
        print(f"\nFailures saved to {FAILURE_FILE} — re-run with --rerun-failed")

    # Final summary if multiple files
    total_tests = total_passed + total_failed + total_skipped
    if len(spec_files) > 1:
        print(f"\n{'=' * 60}")
        print(f"TOTAL: {len(spec_files)} spec files, {total_tests} tests")
        if total_failed == 0 and total_skipped == 0:
            print(f"\033[92m\033[1mAll {total_passed} tests passed\033[0m")
        else:
            parts = []
            if total_passed:
                parts.append(f"\033[92m{total_passed} passed\033[0m")
            if total_failed:
                parts.append(f"\033[91m{total_failed} failed\033[0m")
            if total_skipped:
                parts.append(f"\033[93m{total_skipped} skipped\033[0m")
            print(", ".join(parts))

    # Exit codes: 0 = pass (skips OK), 1 = any real failure, 2 = all tests skipped
    if total_failed > 0:
        sys.exit(1)
    elif total_passed == 0 and total_skipped > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
