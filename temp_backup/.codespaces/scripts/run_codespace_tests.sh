#!/bin/bash

# Exit on any error
set -e

# Configuration
TEST_REPORTS_DIR="reports/unit"
CHECKLIST_DIR=".checklist"
COMPLETE_DIR=".complete"
VERIFICATION_DIR=".verification"
DOCS_DIR="docs/testing"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create necessary directories
mkdir -p "$TEST_REPORTS_DIR"
mkdir -p "$VERIFICATION_DIR"
mkdir -p "$COMPLETE_DIR"
mkdir -p "$DOCS_DIR"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to run tests and generate reports
run_tests() {
    local test_suite=$1
    local report_file="$TEST_REPORTS_DIR/${test_suite}_${TIMESTAMP}.html"
    local log_file="$TEST_REPORTS_DIR/${test_suite}_${TIMESTAMP}.log"

    log_message "Starting $test_suite tests..."

    # Run tests with coverage and generate HTML report
    python .codespaces/scripts/run_unit_tests.py \
        --test-suite "$test_suite" \
        --report-file "$report_file" \
        --coverage-report "$TEST_REPORTS_DIR/coverage_${test_suite}_${TIMESTAMP}" \
        --junit-report "$TEST_REPORTS_DIR/junit_${test_suite}_${TIMESTAMP}.xml" \
        --log-file "$log_file" \
        --verbose

    # Check test execution status
    if [ $? -eq 0 ]; then
        log_message "$test_suite tests completed successfully"
    else
        log_message "ERROR: $test_suite tests failed"
        return 1
    fi

    # Generate verification report
    python .codespaces/scripts/generate_verification_report.py \
        --test-report "$report_file" \
        --coverage-report "$TEST_REPORTS_DIR/coverage_${test_suite}_${TIMESTAMP}.xml" \
        --output "$VERIFICATION_DIR/${test_suite}_verification_${TIMESTAMP}.json" \
        --log-file "$log_file"

    # Generate documentation
    python .codespaces/scripts/generate_test_docs.py \
        --test-suite "$test_suite" \
        --report-file "$report_file" \
        --coverage-report "$TEST_REPORTS_DIR/coverage_${test_suite}_${TIMESTAMP}.xml" \
        --verification-file "$VERIFICATION_DIR/${test_suite}_verification_${TIMESTAMP}.json" \
        --output "$DOCS_DIR/${test_suite}_${TIMESTAMP}.md"
}

# Function to verify checklist items
verify_checklist() {
    local test_suite=$1
    local verification_file="$VERIFICATION_DIR/${test_suite}_verification_${TIMESTAMP}.json"

    log_message "Verifying checklist items for $test_suite..."

    # Process checklist items
    python .codespaces/scripts/verify_checklist.py \
        --verification-file "$verification_file" \
        --checklist-dir "$CHECKLIST_DIR" \
        --complete-dir "$COMPLETE_DIR" \
        --test-suite "$test_suite" \
        --verbose

    # Check verification status
    if [ $? -eq 0 ]; then
        log_message "$test_suite verification completed successfully"
    else
        log_message "ERROR: $test_suite verification failed"
        return 1
    fi
}

# Function to resolve issues
resolve_issues() {
    local test_suite=$1
    local log_file="$TEST_REPORTS_DIR/${test_suite}_${TIMESTAMP}.log"

    log_message "Resolving issues for $test_suite..."

    # Run issue resolution script
    python .codespaces/scripts/resolve_issues.py \
        --test-suite "$test_suite" \
        --log-file "$log_file" \
        --verification-dir "$VERIFICATION_DIR" \
        --verbose

    # Check resolution status
    if [ $? -eq 0 ]; then
        log_message "$test_suite issues resolved successfully"
    else
        log_message "ERROR: Failed to resolve $test_suite issues"
        return 1
    fi
}

# Main test execution
log_message "Starting comprehensive unit testing in Codespaces..."

# Create test execution log
execution_log="$TEST_REPORTS_DIR/test_execution_${TIMESTAMP}.log"
touch "$execution_log"

# Run API tests
run_tests "api" 2>&1 | tee -a "$execution_log"
verify_checklist "api" 2>&1 | tee -a "$execution_log"
resolve_issues "api" 2>&1 | tee -a "$execution_log"

# Run service tests
run_tests "services" 2>&1 | tee -a "$execution_log"
verify_checklist "services" 2>&1 | tee -a "$execution_log"
resolve_issues "services" 2>&1 | tee -a "$execution_log"

# Run utility tests
run_tests "utils" 2>&1 | tee -a "$execution_log"
verify_checklist "utils" 2>&1 | tee -a "$execution_log"
resolve_issues "utils" 2>&1 | tee -a "$execution_log"

# Generate final verification summary
python .codespaces/scripts/generate_summary.py \
    --verification-dir "$VERIFICATION_DIR" \
    --output "$TEST_REPORTS_DIR/verification_summary_${TIMESTAMP}.html" \
    --log-file "$execution_log"

# Generate final documentation
python .codespaces/scripts/generate_final_docs.py \
    --test-reports-dir "$TEST_REPORTS_DIR" \
    --verification-dir "$VERIFICATION_DIR" \
    --docs-dir "$DOCS_DIR" \
    --timestamp "$TIMESTAMP" \
    --log-file "$execution_log"

log_message "Testing completed. Reports available in $TEST_REPORTS_DIR"
log_message "Verification results available in $VERIFICATION_DIR"
log_message "Documentation available in $DOCS_DIR"

# Check if all tests passed
if [ -f "$COMPLETE_DIR/all_tests_complete" ]; then
    log_message "All tests completed successfully!"
    exit 0
else
    log_message "ERROR: Some tests failed. Please check the reports for details."
    exit 1
fi
