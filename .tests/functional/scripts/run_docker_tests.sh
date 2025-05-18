#!/bin/bash

# Exit on any error
set -e

# Configuration
TEST_REPORTS_DIR="reports/functional"
CHECKLIST_DIR=".checklist"
COMPLETE_DIR=".complete"
VERIFICATION_DIR=".verification"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create necessary directories
mkdir -p "$TEST_REPORTS_DIR"
mkdir -p "$VERIFICATION_DIR"
mkdir -p "$COMPLETE_DIR"

# Function to run tests and generate reports
run_tests() {
    local test_suite=$1
    local report_file="$TEST_REPORTS_DIR/${test_suite}_${TIMESTAMP}.html"

    echo "Running $test_suite tests..."

    # Run tests with coverage and generate HTML report
    pytest "tests/functional/$test_suite" \
        --html="$report_file" \
        --self-contained-html \
        --cov="app" \
        --cov-report=html:"$TEST_REPORTS_DIR/coverage_${test_suite}_${TIMESTAMP}" \
        --cov-report=xml:"$TEST_REPORTS_DIR/coverage_${test_suite}_${TIMESTAMP}.xml" \
        --junitxml="$TEST_REPORTS_DIR/junit_${test_suite}_${TIMESTAMP}.xml"

    # Generate verification report
    python scripts/generate_verification_report.py \
        --test-report "$report_file" \
        --coverage-report "$TEST_REPORTS_DIR/coverage_${test_suite}_${TIMESTAMP}.xml" \
        --output "$VERIFICATION_DIR/${test_suite}_verification_${TIMESTAMP}.json"
}

# Function to verify checklist items
verify_checklist() {
    local test_suite=$1
    local verification_file="$VERIFICATION_DIR/${test_suite}_verification_${TIMESTAMP}.json"

    echo "Verifying checklist items for $test_suite..."

    # Process checklist items
    python scripts/verify_checklist.py \
        --verification-file "$verification_file" \
        --checklist-dir "$CHECKLIST_DIR" \
        --complete-dir "$COMPLETE_DIR" \
        --test-suite "$test_suite"
}

# Main test execution
echo "Starting comprehensive functional testing..."

# Run API tests
run_tests "api"
verify_checklist "api"

# Run service tests
run_tests "services"
verify_checklist "services"

# Run integration tests
run_tests "integration"
verify_checklist "integration"

# Generate final verification summary
python scripts/generate_summary.py \
    --verification-dir "$VERIFICATION_DIR" \
    --output "$TEST_REPORTS_DIR/verification_summary_${TIMESTAMP}.html"

echo "Testing completed. Reports available in $TEST_REPORTS_DIR"
echo "Verification results available in $VERIFICATION_DIR"
