#!/usr/bin/env bash
################################################################################
# Tests for bash_utils.sh functions
#
# This script tests the utility functions in scripts/bash_utils.sh
# Run with: bash tests/integration/test_bash_utils.sh
################################################################################

set -euo pipefail

# Get script directory and repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source the utilities we're testing (avoid redeclaration errors)
if [[ -z "${RED:-}" ]]; then
    source "$REPO_ROOT/scripts/bash_utils.sh"
fi

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test helper functions
test_start() {
    local test_name="$1"
    echo -n "Testing $test_name... "
    ((TESTS_RUN++))
}

test_pass() {
    echo "✓ PASS"
    ((TESTS_PASSED++))
}

test_fail() {
    local message="$1"
    echo "✗ FAIL: $message"
    ((TESTS_FAILED++))
}

test_equal() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"

    test_start "$test_name"
    if [[ "$expected" == "$actual" ]]; then
        test_pass
        return 0
    else
        test_fail "Expected '$expected', got '$actual'"
        return 1
    fi
}

test_contains() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"

    test_start "$test_name"
    if [[ "$actual" == *"$expected"* ]]; then
        test_pass
        return 0
    else
        test_fail "Expected '$actual' to contain '$expected'"
        return 1
    fi
}

test_matches() {
    local pattern="$1"
    local actual="$2"
    local test_name="$3"

    test_start "$test_name"
    if [[ "$actual" =~ $pattern ]]; then
        test_pass
        return 0
    else
        test_fail "Expected '$actual' to match pattern '$pattern'"
        return 1
    fi
}

# Test logging functions
test_log_functions() {
    echo "=== Testing Logging Functions ==="

    # Capture output to test log functions
    local output

    # Test log_success
    output=$(log_success "Test message")
    test_contains "✓ Test message" "$output" "log_success format"

    # Test log_error
    output=$(log_error "Error message")
    test_contains "✗ Error message" "$output" "log_error format"

    # Test log_info
    output=$(log_info "Info message")
    test_equal "  Info message" "$output" "log_info format"

    # Test log_warning
    output=$(log_warning "Warning message")
    test_contains "⚠ Warning message" "$output" "log_warning format"
}

# Test utility functions
test_utility_functions() {
    echo "=== Testing Utility Functions ==="

    # Test format_duration
    test_equal "5s" "$(format_duration 5)" "format_duration seconds"
    test_equal "1m 30s" "$(format_duration 90)" "format_duration minutes and seconds"
    test_equal "2m 0s" "$(format_duration 120)" "format_duration exact minutes"

    # Test get_elapsed_time
    local start=100
    local end=150
    test_equal "50" "$(get_elapsed_time $start $end)" "get_elapsed_time calculation"

    # Test format_file_size
    test_equal "512B" "$(format_file_size 512)" "format_file_size bytes"
    test_equal "1KB" "$(format_file_size 1024)" "format_file_size kilobytes"
    test_equal "1MB" "$(format_file_size 1048576)" "format_file_size megabytes"
    test_equal "1GB" "$(format_file_size 1073741824)" "format_file_size gigabytes"
}

# Test choice parsing functions
test_choice_parsing() {
    echo "=== Testing Choice Parsing ==="

    # Test parse_choice_sequence with single digit
    SHORTHAND_CHOICES=()
    parse_choice_sequence "1"
    test_equal "1" "${SHORTHAND_CHOICES[0]:-}" "parse_choice_sequence single digit"

    # Test parse_choice_sequence with multiple digits
    SHORTHAND_CHOICES=()
    parse_choice_sequence "123"
    test_equal "1" "${SHORTHAND_CHOICES[0]:-}" "parse_choice_sequence multiple digits 1"
    test_equal "2" "${SHORTHAND_CHOICES[1]:-}" "parse_choice_sequence multiple digits 2"
    test_equal "3" "${SHORTHAND_CHOICES[2]:-}" "parse_choice_sequence multiple digits 3"

    # Test parse_choice_sequence with comma separated
    SHORTHAND_CHOICES=()
    parse_choice_sequence "1,3,5"
    test_equal "1" "${SHORTHAND_CHOICES[0]:-}" "parse_choice_sequence comma separated 1"
    test_equal "3" "${SHORTHAND_CHOICES[1]:-}" "parse_choice_sequence comma separated 3"
    test_equal "5" "${SHORTHAND_CHOICES[2]:-}" "parse_choice_sequence comma separated 5"

    # Test parse_choice_sequence with spaces
    SHORTHAND_CHOICES=()
    parse_choice_sequence "1 3 5"
    test_equal "1" "${SHORTHAND_CHOICES[0]:-}" "parse_choice_sequence space separated 1"
    test_equal "3" "${SHORTHAND_CHOICES[1]:-}" "parse_choice_sequence space separated 3"
    test_equal "5" "${SHORTHAND_CHOICES[2]:-}" "parse_choice_sequence space separated 5"

    # Test parse_choice_sequence with invalid input
    SHORTHAND_CHOICES=()
    if parse_choice_sequence "abc"; then
        test_fail "parse_choice_sequence should fail on invalid input"
    else
        test_pass "parse_choice_sequence fails on invalid input"
    fi

    # Test parse_choice_sequence with empty input
    SHORTHAND_CHOICES=()
    if parse_choice_sequence ""; then
        test_fail "parse_choice_sequence should fail on empty input"
    else
        test_pass "parse_choice_sequence fails on empty input"
    fi
}

# Test color codes
test_color_codes() {
    echo "=== Testing Color Codes ==="

    # Test that color variables are defined
    test_equal "0;31m" "$RED" "RED color code"
    test_equal "0;32m" "$GREEN" "GREEN color code"
    test_equal "0;34m" "$BLUE" "BLUE color code"
    test_equal "1;33m" "$YELLOW" "YELLOW color code"
    test_equal "0;36m" "$CYAN" "CYAN color code"
    test_equal "1m" "$BOLD" "BOLD color code"
    test_equal "0m" "$NC" "NC (No Color) code"
}

# Test file logging functions (requires temporary files)
test_file_logging() {
    echo "=== Testing File Logging ==="

    local temp_log=$(mktemp)
    export PIPELINE_LOG_FILE="$temp_log"

    # Test log_success_to_file
    log_success_to_file "Test success message"
    test_contains "✓ Test success message" "$(cat "$temp_log")" "log_success_to_file"

    # Test log_error_to_file
    log_error_to_file "Test error message"
    test_contains "✗ Test error message" "$(cat "$temp_log")" "log_error_to_file"

    # Test log_info_to_file
    log_info_to_file "Test info message"
    test_contains "  Test info message" "$(cat "$temp_log")" "log_info_to_file"

    # Test log_warning_to_file
    log_warning_to_file "Test warning message"
    test_contains "⚠ Test warning message" "$(cat "$temp_log")" "log_warning_to_file"

    # Clean up
    rm -f "$temp_log"
    unset PIPELINE_LOG_FILE
}

# Test log header function
test_log_header() {
    echo "=== Testing Log Header ==="

    local output
    output=$(log_header "Test Header")

    # Check that it contains the expected elements
    test_contains "════════════════════════════════════════════════════════════════" "$output" "log_header top border"
    test_contains "Test Header" "$output" "log_header text"
    test_contains "════════════════════════════════════════════════════════════════" "$output" "log_header bottom border"
}

# Test press_enter_to_continue (this will require user interaction, so we'll skip it)
test_press_enter_to_continue() {
    echo "=== Testing press_enter_to_continue ==="
    echo "Skipping interactive test (would require user input)"
}

# Test new structured logging functions
test_log_with_context() {
    echo "=== Testing log_with_context ==="

    local output
    output=$(log_with_context "INFO" "Test message" "test-context")
    test_contains "[INFO]" "$output" "log_with_context level"
    test_contains "[test-context]" "$output" "log_with_context context"
    test_contains "Test message" "$output" "log_with_context message"

    # Test without context
    output=$(log_with_context "WARN" "Warning message")
    test_contains "[WARN]" "$output" "log_with_context no context level"
    test_contains "Warning message" "$output" "log_with_context no context message"
}

test_log_error_with_context() {
    echo "=== Testing log_error_with_context ==="

    local output
    output=$(log_error_with_context "Test error message")
    test_contains "✗ Test error message (in" "$output" "log_error_with_context default"

    # Test with custom context
    output=$(log_error_with_context "Test error message" "custom-context")
    test_contains "✗ Test error message (in custom-context)" "$output" "log_error_with_context custom"
}

test_log_troubleshooting() {
    echo "=== Testing log_troubleshooting ==="

    local output
    output=$(log_troubleshooting "TestError" "Primary error" "Step 1" "Step 2")

    test_contains "✗ Primary error" "$output" "log_troubleshooting primary error"
    test_contains "Troubleshooting steps:" "$output" "log_troubleshooting header"
    test_contains "1. Step 1" "$output" "log_troubleshooting step 1"
    test_contains "2. Step 2" "$output" "log_troubleshooting step 2"
}

test_log_pipeline_error() {
    echo "=== Testing log_pipeline_error ==="

    local output
    output=$(log_pipeline_error "Test Stage" "Test error" 1 "Check this" "Check that")

    test_contains "Pipeline failed at Stage: Test Stage (exit code: 1)" "$output" "log_pipeline_error header"
    test_contains "Error: Test error" "$output" "log_pipeline_error message"
    test_contains "Troubleshooting:" "$output" "log_pipeline_error troubleshooting"
    test_contains "1. Check this" "$output" "log_pipeline_error step 1"
    test_contains "2. Check that" "$output" "log_pipeline_error step 2"
}

test_log_resource_usage() {
    echo "=== Testing log_resource_usage ==="

    local output
    output=$(log_resource_usage "Test Stage" 45)
    test_contains "Stage 'Test Stage' completed in 45s" "$output" "log_resource_usage basic"
    test_contains "[resource-monitor]" "$output" "log_resource_usage context"

    # Test with additional metrics
    output=$(log_resource_usage "Test Stage" 125 "cpu: 80%")
    test_contains "Stage 'Test Stage' completed in 2m 5s (cpu: 80%)" "$output" "log_resource_usage additional"
}

test_log_stage_progress() {
    echo "=== Testing log_stage_progress ==="

    local output
    output=$(log_stage_progress 2 "Test Stage" 5 1000 1005)
    test_contains "[2/5] Test Stage (40% complete)" "$output" "log_stage_progress basic"
    test_contains "Stage elapsed: 5s" "$output" "log_stage_progress elapsed"

    # Test without stage start time
    output=$(log_stage_progress 3 "Test Stage 2" 5 1000)
    test_contains "[3/5] Test Stage 2 (60% complete)" "$output" "log_stage_progress no stage time"
}

# Run all tests
main() {
    echo "Running bash_utils.sh tests..."
    echo

    test_log_functions
    echo

    test_utility_functions
    echo

    test_choice_parsing
    echo

    test_color_codes
    echo

    test_file_logging
    echo

    test_log_header
    echo

    test_press_enter_to_continue
    echo

    test_log_with_context
    echo

    test_log_error_with_context
    echo

    test_log_troubleshooting
    echo

    test_log_pipeline_error
    echo

    test_log_resource_usage
    echo

    test_log_stage_progress
    echo

    # Print summary
    echo "=== Test Results ==="
    echo "Tests run: $TESTS_RUN"
    echo "Tests passed: $TESTS_PASSED"
    echo "Tests failed: $TESTS_FAILED"

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo "✓ All tests passed!"
        exit 0
    else
        echo "✗ $TESTS_FAILED tests failed"
        exit 1
    fi
}

# Run tests
main "$@"