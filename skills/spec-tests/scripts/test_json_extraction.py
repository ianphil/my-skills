#!/usr/bin/env python3
"""
Test JSON extraction logic for spec test runners.

This file is for development/testing only - not copied to user projects.

Run tests:
    python test_json_extraction.py
"""

import json
import sys
from pathlib import Path

# Import the extraction function from one runner
# (All three should have identical implementation)
sys.path.insert(0, str(Path(__file__).parent))
from run_tests_opencode import extract_judge_response_json, JSONExtractionError


def test_pure_json():
    """Pure JSON without wrapping."""
    response = '{"passed": true, "reasoning": "Looks good"}'
    result = extract_judge_response_json(response)
    assert result == {"passed": True, "reasoning": "Looks good"}
    print("✓ Pure JSON")


def test_nested_objects():
    """THE BUG FIX: Nested objects should work correctly."""
    response = '{"outer": {"inner": 1}, "passed": false, "reasoning": "Nested test"}'
    result = extract_judge_response_json(response)
    assert result["passed"] is False
    assert result["reasoning"] == "Nested test"
    print("✓ Nested objects (BUG FIX)")


def test_deeply_nested_objects():
    """Deeply nested objects should work correctly."""
    response = (
        '{"a": {"b": {"c": {"d": 1}}}, "passed": true, "reasoning": "Deep nesting"}'
    )
    result = extract_judge_response_json(response)
    assert result["passed"] is True
    assert result["reasoning"] == "Deep nesting"
    print("✓ Deeply nested objects")


def test_braces_in_string():
    """Braces in string values should be handled correctly."""
    response = '{"passed": true, "reasoning": "Function {foo()} works"}'
    result = extract_judge_response_json(response)
    assert result["reasoning"] == "Function {foo()} works"
    print("✓ Braces in strings")


def test_escaped_quotes_in_string():
    """Escaped quotes in strings should be handled correctly."""
    response = '{"passed": true, "reasoning": "Error: \\"not found\\""}'
    result = extract_judge_response_json(response)
    assert result["passed"] is True
    assert "not found" in result["reasoning"]
    print("✓ Escaped quotes in strings")


def test_markdown_code_block():
    """JSON wrapped in markdown code block."""
    response = """```json
{"passed": true, "reasoning": "Success"}
```"""
    result = extract_judge_response_json(response)
    assert result == {"passed": True, "reasoning": "Success"}
    print("✓ Markdown code block")


def test_markdown_code_block_no_lang():
    """JSON wrapped in markdown code block without language specifier."""
    response = """```
{"passed": false, "reasoning": "Failed"}
```"""
    result = extract_judge_response_json(response)
    assert result == {"passed": False, "reasoning": "Failed"}
    print("✓ Markdown code block (no lang)")


def test_json_with_text_before():
    """JSON with explanatory text before it."""
    response = 'Here is my evaluation: {"passed": true, "reasoning": "Good"}'
    result = extract_judge_response_json(response)
    assert result == {"passed": True, "reasoning": "Good"}
    print("✓ Text before JSON")


def test_json_with_text_after():
    """JSON with text after it."""
    response = '{"passed": true, "reasoning": "Good"} That is my verdict.'
    result = extract_judge_response_json(response)
    assert result == {"passed": True, "reasoning": "Good"}
    print("✓ Text after JSON")


def test_json_with_newlines():
    """JSON with newlines and formatting."""
    response = """{
    "passed": true,
    "reasoning": "Multi-line\\nreasoning"
}"""
    result = extract_judge_response_json(response)
    assert result["passed"] is True
    print("✓ JSON with newlines")


def test_empty_response_fails():
    """Empty response should raise error."""
    try:
        extract_judge_response_json("")
        assert False, "Should have raised JSONExtractionError"
    except JSONExtractionError as e:
        assert "Empty response" in str(e)
        print("✓ Empty response error")


def test_whitespace_only_fails():
    """Whitespace-only response should raise error."""
    try:
        extract_judge_response_json("   \n\t  ")
        assert False, "Should have raised JSONExtractionError"
    except JSONExtractionError as e:
        assert "Empty response" in str(e)
        print("✓ Whitespace-only response error")


def test_malformed_json_fails():
    """Malformed JSON should raise error with helpful message."""
    try:
        extract_judge_response_json('{"passed": true')
        assert False, "Should have raised JSONExtractionError"
    except JSONExtractionError as e:
        assert "Failed to extract JSON" in str(e)
        print("✓ Malformed JSON error")


def test_missing_passed_field_fails():
    """JSON without 'passed' field should fail validation."""
    try:
        extract_judge_response_json('{"reasoning": "Missing passed"}')
        assert False, "Should have raised JSONExtractionError"
    except JSONExtractionError as e:
        assert "passed" in str(e)
        print("✓ Missing 'passed' field error")


def test_wrong_type_passed_fails():
    """'passed' field with wrong type should fail validation."""
    try:
        extract_judge_response_json('{"passed": "true", "reasoning": "Wrong type"}')
        assert False, "Should have raised JSONExtractionError"
    except JSONExtractionError as e:
        assert "bool" in str(e)
        print("✓ Wrong type for 'passed' error")


def test_passed_as_number_fails():
    """'passed' field as number should fail validation."""
    try:
        extract_judge_response_json('{"passed": 1, "reasoning": "Number"}')
        assert False, "Should have raised JSONExtractionError"
    except JSONExtractionError as e:
        assert "bool" in str(e)
        print("✓ 'passed' as number error")


def test_missing_reasoning_uses_default():
    """Missing 'reasoning' field should use default."""
    result = extract_judge_response_json('{"passed": false}')
    assert result["reasoning"] == "No reasoning provided"
    print("✓ Default reasoning")


def test_wrong_type_reasoning_fails():
    """'reasoning' field with wrong type should fail validation."""
    try:
        extract_judge_response_json('{"passed": true, "reasoning": 123}')
        assert False, "Should have raised JSONExtractionError"
    except JSONExtractionError as e:
        assert "reasoning" in str(e) and "string" in str(e)
        print("✓ Wrong type for 'reasoning' error")


def test_extra_fields_allowed():
    """Extra fields in JSON should be allowed."""
    response = '{"passed": true, "reasoning": "OK", "confidence": 0.95, "details": {}}'
    result = extract_judge_response_json(response)
    assert result["passed"] is True
    assert result["reasoning"] == "OK"
    print("✓ Extra fields allowed")


def test_no_json_in_response_fails():
    """Response with no JSON should fail."""
    try:
        extract_judge_response_json("This is just plain text with no JSON at all.")
        assert False, "Should have raised JSONExtractionError"
    except JSONExtractionError as e:
        assert "Failed to extract JSON" in str(e)
        print("✓ No JSON in response error")


def test_object_inside_array_extracted():
    """JSON object inside array should be extracted (graceful handling)."""
    # The balanced braces strategy finds the object inside the array
    # This is acceptable - LLMs sometimes wrap responses in arrays
    result = extract_judge_response_json('[{"passed": true, "reasoning": "Wrapped"}]')
    assert result["passed"] is True
    assert result["reasoning"] == "Wrapped"
    print("✓ Object inside array extracted")


if __name__ == "__main__":
    print("Testing JSON extraction logic...\n")

    tests = [
        test_pure_json,
        test_nested_objects,
        test_deeply_nested_objects,
        test_braces_in_string,
        test_escaped_quotes_in_string,
        test_markdown_code_block,
        test_markdown_code_block_no_lang,
        test_json_with_text_before,
        test_json_with_text_after,
        test_json_with_newlines,
        test_empty_response_fails,
        test_whitespace_only_fails,
        test_malformed_json_fails,
        test_missing_passed_field_fails,
        test_wrong_type_passed_fails,
        test_passed_as_number_fails,
        test_missing_reasoning_uses_default,
        test_wrong_type_reasoning_fails,
        test_extra_fields_allowed,
        test_no_json_in_response_fails,
        test_object_inside_array_extracted,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print(f"\n{'=' * 40}")
    if failed == 0:
        print(f"✓ All {passed} tests passed!")
    else:
        print(f"✗ {failed} failed, {passed} passed")
        sys.exit(1)
