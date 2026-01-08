#!/usr/bin/env python3
"""Literate Test Runner - parses markdown test files and validates assertions.

Copy this file to your project's tests/ directory:
    cp run_tests.py /path/to/project/tests/

Run from project root:
    python tests/run_tests.py
"""

import importlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestCase:
    name: str
    section: str
    code: str
    language: str
    assertions: list[dict]
    line_number: int


@dataclass
class TestResult:
    test: TestCase
    passed: bool
    message: str
    actual: str | None = None


def parse_frontmatter(content: str) -> dict:
    """Extract TOML-like config from the start of the file."""
    config = {}
    match = re.match(r'^```toml\n(.*?)```', content, re.DOTALL)
    if match:
        for line in match.group(1).strip().split('\n'):
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if value.startswith('[') and value.endswith(']'):
                    # Parse list
                    value = [v.strip().strip('"').strip("'")
                             for v in value[1:-1].split(',') if v.strip()]
                config[key] = value
    return config


def extract_tests(content: str) -> list[TestCase]:
    """Find code blocks and their assertions from markdown."""
    tests = []
    current_section = ""
    current_test_name = ""

    lines = content.split('\n')
    i = 0
    line_number = 0

    while i < len(lines):
        line = lines[i]
        line_number = i + 1

        # Track section headers
        if line.startswith('## '):
            current_section = line[3:].strip()
        elif line.startswith('### '):
            current_test_name = line[4:].strip()

        # Find code blocks
        code_match = re.match(r'^```(py|sh|python|bash)\s*$', line)
        if code_match:
            language = code_match.group(1)
            if language == 'python':
                language = 'py'
            if language == 'bash':
                language = 'sh'

            code_lines = []
            assertions = []
            i += 1

            while i < len(lines) and not lines[i].startswith('```'):
                code_line = lines[i]

                # Check for assertions in comments
                if language == 'py':
                    expect_match = re.search(r'#\s*expect:\s*(.+)$', code_line)
                    error_match = re.search(r'#\s*error:\s*(.+)$', code_line)

                    if expect_match:
                        # Get the expression before the comment
                        expr = code_line.split('#')[0].strip()
                        assertions.append({
                            'type': 'expect',
                            'expression': expr,
                            'expected': expect_match.group(1).strip(),
                            'line': code_line
                        })
                    elif error_match:
                        expr = code_line.split('#')[0].strip()
                        assertions.append({
                            'type': 'error',
                            'expression': expr,
                            'expected': error_match.group(1).strip(),
                            'line': code_line
                        })
                    else:
                        code_lines.append(code_line)
                elif language == 'sh':
                    # Shell assertions come after the command
                    exit_match = re.match(r'^#\s*exit:\s*(\d+)$', code_line)
                    stdout_match = re.match(r'^#\s*stdout:\s*(.+)$', code_line)
                    stderr_match = re.match(r'^#\s*stderr:\s*(.+)$', code_line)

                    if exit_match:
                        assertions.append({
                            'type': 'exit',
                            'expected': int(exit_match.group(1))
                        })
                    elif stdout_match:
                        assertions.append({
                            'type': 'stdout',
                            'expected': stdout_match.group(1).strip()
                        })
                    elif stderr_match:
                        assertions.append({
                            'type': 'stderr',
                            'expected': stderr_match.group(1).strip()
                        })
                    else:
                        code_lines.append(code_line)

                i += 1

            if assertions:
                tests.append(TestCase(
                    name=current_test_name or f"Test at line {line_number}",
                    section=current_section,
                    code='\n'.join(code_lines),
                    language=language,
                    assertions=assertions,
                    line_number=line_number
                ))

        i += 1

    return tests


def parse_expected_value(expected: str, actual):
    """Parse expected value string and compare with actual."""
    expected = expected.strip()

    # Handle approx() matcher
    approx_match = re.match(r'approx\(([^,]+),\s*tol=([^)]+)\)', expected)
    if approx_match:
        target = float(approx_match.group(1))
        tolerance = float(approx_match.group(2))
        if isinstance(actual, (int, float)):
            return abs(actual - target) <= tolerance
        return False

    # Handle contains() matcher
    contains_match = re.match(r'contains\("([^"]+)"\)', expected)
    if contains_match:
        substring = contains_match.group(1)
        return substring in str(actual)

    # Handle list
    if expected.startswith('[') and expected.endswith(']'):
        return str(actual) == expected or actual == eval(expected)

    # Handle string
    if expected.startswith('"') and expected.endswith('"'):
        return str(actual) == expected[1:-1]

    # Handle numeric
    try:
        if '.' in expected:
            return float(actual) == float(expected)
        return int(actual) == int(expected)
    except (ValueError, TypeError):
        pass

    # Handle boolean/None
    if expected == 'True':
        return actual is True
    if expected == 'False':
        return actual is False
    if expected == 'None':
        return actual is None

    # String comparison
    return str(actual) == expected


def run_python_test(test: TestCase, module_imports: dict) -> TestResult:
    """Execute a Python code block and validate assertions."""
    # Build execution context
    context = dict(module_imports)

    # First, run all setup code (non-assertion lines)
    setup_code = test.code
    if setup_code.strip():
        try:
            exec(setup_code, context)
        except Exception as e:
            return TestResult(
                test=test,
                passed=False,
                message=f"Setup failed: {type(e).__name__}: {e}",
                actual=str(e)
            )

    # Now check assertions
    for assertion in test.assertions:
        if assertion['type'] == 'expect':
            expr = assertion['expression']
            expected = assertion['expected']

            try:
                actual = eval(expr, context)
                if parse_expected_value(expected, actual):
                    continue
                else:
                    return TestResult(
                        test=test,
                        passed=False,
                        message=f"Expected {expected}, got {actual!r}",
                        actual=str(actual)
                    )
            except Exception as e:
                return TestResult(
                    test=test,
                    passed=False,
                    message=f"Expression failed: {type(e).__name__}: {e}",
                    actual=str(e)
                )

        elif assertion['type'] == 'error':
            expr = assertion['expression']
            expected_code = assertion['expected']

            # Extract error code from [code] format
            code_match = re.match(r'\[([^\]]+)\]', expected_code)
            expected_error_code = code_match.group(1) if code_match else expected_code

            try:
                exec(expr, context)
                return TestResult(
                    test=test,
                    passed=False,
                    message=f"Expected error [{expected_error_code}] but no exception raised",
                    actual="No exception"
                )
            except Exception as e:
                # Check if exception has a .code attribute
                error_code = getattr(e, 'code', None) or type(e).__name__
                if error_code == expected_error_code:
                    continue
                else:
                    return TestResult(
                        test=test,
                        passed=False,
                        message=f"Expected error [{expected_error_code}], got [{error_code}]: {e}",
                        actual=str(e)
                    )

    return TestResult(test=test, passed=True, message="OK")


def run_shell_test(test: TestCase) -> TestResult:
    """Execute a shell command and validate assertions."""
    command = test.code.strip()

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
    except subprocess.TimeoutExpired:
        return TestResult(
            test=test,
            passed=False,
            message="Command timed out after 30 seconds"
        )
    except Exception as e:
        return TestResult(
            test=test,
            passed=False,
            message=f"Command failed: {e}"
        )

    for assertion in test.assertions:
        if assertion['type'] == 'exit':
            expected_code = assertion['expected']
            if result.returncode != expected_code:
                return TestResult(
                    test=test,
                    passed=False,
                    message=f"Expected exit code {expected_code}, got {result.returncode}",
                    actual=f"stdout: {result.stdout}\nstderr: {result.stderr}"
                )

        elif assertion['type'] == 'stdout':
            expected = assertion['expected']
            contains_match = re.match(r'contains\("([^"]+)"\)', expected)
            if contains_match:
                substring = contains_match.group(1)
                if substring not in result.stdout:
                    return TestResult(
                        test=test,
                        passed=False,
                        message=f"stdout should contain '{substring}'",
                        actual=result.stdout
                    )

        elif assertion['type'] == 'stderr':
            expected = assertion['expected']
            contains_match = re.match(r'contains\("([^"]+)"\)', expected)
            if contains_match:
                substring = contains_match.group(1)
                if substring not in result.stderr:
                    return TestResult(
                        test=test,
                        passed=False,
                        message=f"stderr should contain '{substring}'",
                        actual=result.stderr
                    )

    return TestResult(test=test, passed=True, message="OK")


def load_module_imports(config: dict) -> dict:
    """Load the module and imports specified in config."""
    imports = {}

    module_name = config.get('module')
    import_names = config.get('import', [])

    if not module_name:
        return imports

    try:
        module = importlib.import_module(module_name)
        for name in import_names:
            if hasattr(module, name):
                imports[name] = getattr(module, name)
            else:
                print(f"  Warning: {name} not found in {module_name}")
    except ImportError as e:
        print(f"  Warning: Could not import {module_name}: {e}")

    return imports


def run_test_file(path: Path) -> tuple[int, int]:
    """Run all tests in a markdown file. Returns (passed, failed) counts."""
    content = path.read_text()
    config = parse_frontmatter(content)
    tests = extract_tests(content)

    print(f"\n{'='*60}")
    print(f"  {path.name}")
    print(f"{'='*60}")

    if not tests:
        print("  No tests found")
        return 0, 0

    module_imports = load_module_imports(config)

    passed = 0
    failed = 0
    current_section = ""

    for test in tests:
        if test.section != current_section:
            current_section = test.section
            print(f"\n  {current_section}")
            print(f"  {'-' * len(current_section)}")

        if test.language == 'py':
            result = run_python_test(test, module_imports)
        elif test.language == 'sh':
            result = run_shell_test(test)
        else:
            result = TestResult(test=test, passed=False, message=f"Unknown language: {test.language}")

        if result.passed:
            print(f"  \033[32m✓\033[0m {test.name}")
            passed += 1
        else:
            print(f"  \033[31m✗\033[0m {test.name}")
            print(f"      {result.message}")
            if result.actual:
                actual_preview = result.actual[:100] + "..." if len(result.actual) > 100 else result.actual
                print(f"      Actual: {actual_preview}")
            failed += 1

    return passed, failed


def main():
    """Run all markdown test files in tests/ directory."""
    # When run from tests/, look in current directory
    # When run from project root, look in tests/
    script_dir = Path(__file__).parent
    if script_dir.name == "tests":
        tests_dir = script_dir
    else:
        tests_dir = script_dir / "tests"

    if not tests_dir.exists():
        print("No tests/ directory found")
        sys.exit(1)

    test_files = list(tests_dir.glob("*.md"))

    if not test_files:
        print("No .md test files found in tests/")
        sys.exit(1)

    total_passed = 0
    total_failed = 0

    for test_file in sorted(test_files):
        passed, failed = run_test_file(test_file)
        total_passed += passed
        total_failed += failed

    print(f"\n{'='*60}")
    print(f"  Summary: {total_passed} passed, {total_failed} failed")
    print(f"{'='*60}\n")

    sys.exit(0 if total_failed == 0 else 1)


if __name__ == "__main__":
    main()
