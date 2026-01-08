#!/usr/bin/env bash
# Literate Test Runner for Bash/Shell
# Parses markdown test files and validates assertions.
#
# Copy this file to your project's tests/ directory:
#     cp run_tests.sh /path/to/project/tests/
#
# Run from project root:
#     bash tests/run_tests.sh

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Counters
TOTAL_PASSED=0
TOTAL_FAILED=0

# Determine tests directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(basename "$SCRIPT_DIR")" == "tests" ]]; then
    TESTS_DIR="$SCRIPT_DIR"
else
    TESTS_DIR="$SCRIPT_DIR/tests"
fi

if [[ ! -d "$TESTS_DIR" ]]; then
    echo "No tests/ directory found"
    exit 1
fi

# Parse TOML-like frontmatter
parse_frontmatter() {
    local content="$1"
    local key="$2"

    # Extract value for key from frontmatter
    echo "$content" | sed -n '/^```toml/,/^```/p' | grep "^${key}" | sed "s/${key}[[:space:]]*=[[:space:]]*//" | tr -d '"' | tr -d "'"
}

# Run a single test block
run_test() {
    local code="$1"
    local test_name="$2"
    local assertions="$3"

    # Create temp script
    local tmp_script
    tmp_script=$(mktemp)
    echo "$code" > "$tmp_script"
    chmod +x "$tmp_script"

    # Execute and capture output
    local stdout stderr exit_code
    stdout=$(mktemp)
    stderr=$(mktemp)

    set +e
    bash "$tmp_script" > "$stdout" 2> "$stderr"
    exit_code=$?
    set -e

    local passed=true
    local fail_message=""

    # Check assertions
    while IFS= read -r assertion; do
        [[ -z "$assertion" ]] && continue

        local type value
        type=$(echo "$assertion" | cut -d: -f1)
        value=$(echo "$assertion" | cut -d: -f2-)

        case "$type" in
            exit)
                local expected_exit
                expected_exit=$(echo "$value" | tr -d ' ')
                if [[ "$exit_code" != "$expected_exit" ]]; then
                    passed=false
                    fail_message="Expected exit code $expected_exit, got $exit_code"
                fi
                ;;
            stdout)
                # Handle contains("...") matcher
                if [[ "$value" =~ contains\(\"([^\"]+)\"\) ]]; then
                    local substring="${BASH_REMATCH[1]}"
                    if ! grep -q "$substring" "$stdout"; then
                        passed=false
                        fail_message="stdout should contain '$substring'"
                    fi
                elif [[ "$value" =~ matches\(/([^/]+)/\) ]]; then
                    local pattern="${BASH_REMATCH[1]}"
                    if ! grep -qE "$pattern" "$stdout"; then
                        passed=false
                        fail_message="stdout should match /$pattern/"
                    fi
                else
                    # Exact match
                    local expected
                    expected=$(echo "$value" | sed 's/^[[:space:]]*//' | tr -d '"')
                    if [[ "$(cat "$stdout")" != "$expected" ]]; then
                        passed=false
                        fail_message="Expected stdout '$expected', got '$(cat "$stdout")'"
                    fi
                fi
                ;;
            stderr)
                # Handle contains("...") matcher
                if [[ "$value" =~ contains\(\"([^\"]+)\"\) ]]; then
                    local substring="${BASH_REMATCH[1]}"
                    if ! grep -q "$substring" "$stderr"; then
                        passed=false
                        fail_message="stderr should contain '$substring'"
                    fi
                elif [[ "$value" =~ \[([^\]]+)\] ]]; then
                    # Error code format [code]
                    local error_code="${BASH_REMATCH[1]}"
                    if ! grep -q "\[$error_code\]" "$stderr"; then
                        passed=false
                        fail_message="stderr should contain [$error_code]"
                    fi
                fi
                ;;
        esac
    done <<< "$assertions"

    # Cleanup
    rm -f "$tmp_script" "$stdout" "$stderr"

    if $passed; then
        echo -e "  ${GREEN}✓${NC} $test_name"
        TOTAL_PASSED=$((TOTAL_PASSED + 1))
    else
        echo -e "  ${RED}✗${NC} $test_name"
        echo "      $fail_message"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
}

# Process a single markdown file
process_file() {
    local file="$1"
    local content
    content=$(cat "$file")

    echo ""
    echo "============================================================"
    echo "  $(basename "$file")"
    echo "============================================================"

    local current_section=""
    local current_test=""
    local in_code_block=false
    local code_lang=""
    local code_content=""
    local assertions=""
    local line_num=0

    while IFS= read -r line || [[ -n "$line" ]]; do
        line_num=$((line_num + 1))

        # Track section headers
        if [[ "$line" =~ ^##[[:space:]](.+)$ ]]; then
            current_section="${BASH_REMATCH[1]}"
            echo ""
            echo "  $current_section"
            echo "  $(printf '%*s' ${#current_section} '' | tr ' ' '-')"
        elif [[ "$line" =~ ^###[[:space:]](.+)$ ]]; then
            current_test="${BASH_REMATCH[1]}"
        fi

        # Start of code block
        if [[ "$line" =~ ^\`\`\`(sh|bash)$ ]] && ! $in_code_block; then
            in_code_block=true
            code_lang="${BASH_REMATCH[1]}"
            code_content=""
            assertions=""
            continue
        fi

        # End of code block
        if [[ "$line" == '```' ]] && $in_code_block; then
            in_code_block=false
            if [[ -n "$assertions" ]]; then
                run_test "$code_content" "${current_test:-Test at line $line_num}" "$assertions"
            fi
            continue
        fi

        # Inside code block
        if $in_code_block; then
            # Check for assertion comments
            if [[ "$line" =~ ^#[[:space:]]*(exit|stdout|stderr):[[:space:]]*(.+)$ ]]; then
                assertions+="${BASH_REMATCH[1]}:${BASH_REMATCH[2]}"$'\n'
            else
                code_content+="$line"$'\n'
            fi
        fi
    done < "$file"
}

# Main
main() {
    local test_files=("$TESTS_DIR"/*.md)

    if [[ ! -e "${test_files[0]}" ]]; then
        echo "No .md test files found in tests/"
        exit 1
    fi

    for file in "${test_files[@]}"; do
        process_file "$file"
    done

    echo ""
    echo "============================================================"
    echo "  Summary: $TOTAL_PASSED passed, $TOTAL_FAILED failed"
    echo "============================================================"
    echo ""

    if [[ $TOTAL_FAILED -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
