#!/bin/bash

# Exit on any error
set -e

# Configuration
TEST_REPORTS_DIR=".codespaces/reports"
CHECKLIST_DIR=".checklist"
COMPLETE_DIR=".complete"
VERIFICATION_DIR=".verification"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create necessary directories
mkdir -p "$TEST_REPORTS_DIR"
mkdir -p "$CHECKLIST_DIR"
mkdir -p "$COMPLETE_DIR"
mkdir -p "$VERIFICATION_DIR"

# Function to run tests for a specific suite
run_tests() {
    local suite_name=$1
    echo "Running tests for $suite_name..."

    # Run pytest with coverage
    python -m pytest "tests/codespaces/$suite_name" \
        --cov=src \
        --cov-report=html \
        --cov-report=xml \
        -v \
        --junitxml="$TEST_REPORTS_DIR/${suite_name}_${TIMESTAMP}.xml" \
        --html="$TEST_REPORTS_DIR/${suite_name}_${TIMESTAMP}.html" \
        --self-contained-html

    # Copy coverage reports
    if [ -d "htmlcov" ]; then
        cp -r htmlcov "$TEST_REPORTS_DIR/coverage_${suite_name}_${TIMESTAMP}"
    fi
    if [ -f "coverage.xml" ]; then
        cp coverage.xml "$TEST_REPORTS_DIR/coverage_${suite_name}_${TIMESTAMP}.xml"
    fi
}

# Function to verify checklist items
verify_checklist() {
    local suite_name=$1
    local checklist_file="$CHECKLIST_DIR/${suite_name}_checklist.txt"

    if [ -f "$checklist_file" ]; then
        echo "Verifying checklist for $suite_name..."
        while IFS= read -r item; do
            if [ -f "$COMPLETE_DIR/$item" ]; then
                echo "✓ $item"
            else
                echo "✗ $item"
                return 1
            fi
        done < "$checklist_file"
    fi
}

# Main execution
echo "Starting Codespaces test suite..."

# Run tests for each component
run_tests "environment"
run_tests "configuration"
run_tests "deployment"
run_tests "integration"
run_tests "cleanup"

# Generate verification summary
echo "Generating verification summary..."
{
    echo "Test Run Summary - $(date)"
    echo "========================"
    echo
    echo "Test Reports: $TEST_REPORTS_DIR"
    echo "Verification Results: $VERIFICATION_DIR"
    echo
    echo "Completed Tests:"
    ls -1 "$COMPLETE_DIR"
} > "$VERIFICATION_DIR/summary_${TIMESTAMP}.txt"

# Clean up test codespaces
echo "Cleaning up test codespaces..."
docker ps -a --filter "name=test_" -q | xargs -r docker stop
docker ps -a --filter "name=test_" -q | xargs -r docker rm
docker volume ls -q --filter "name=test_" | xargs -r docker volume rm
docker network ls -q --filter "name=test_" | xargs -r docker network rm

echo "Test suite completed. Reports available in $TEST_REPORTS_DIR"
echo "Verification results available in $VERIFICATION_DIR"
