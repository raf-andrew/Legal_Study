#!/bin/bash

# Legal Study System Test Script
# This script runs tests for the system components

# Configuration
LOG_DIR="../.logs"
TEST_LOG="$LOG_DIR/test_$(date +%Y%m%d_%H%M%S).log"
TEST_RESULTS_DIR="../.build/test_results"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$TEST_LOG"
}

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$TEST_RESULTS_DIR"

# Activate Python virtual environment
log_message "Activating Python virtual environment..."
source "../.build/venv/bin/activate"

# Run Python unit tests
log_message "Running Python unit tests..."
python3 -m pytest ../.cursor/tests ../.prompts/tests ../.jobs/tests ../.qa/tests ../.research/tests \
    --junitxml="$TEST_RESULTS_DIR/python_tests.xml" \
    --html="$TEST_RESULTS_DIR/python_tests.html" \
    --self-contained-html

# Run frontend tests
log_message "Running frontend tests..."
cd "../"
npm test -- --outputFile="$TEST_RESULTS_DIR/frontend_tests.json"
cd ".build/build_scripts"

# Run integration tests
log_message "Running integration tests..."
python3 -m pytest ../tests/integration \
    --junitxml="$TEST_RESULTS_DIR/integration_tests.xml" \
    --html="$TEST_RESULTS_DIR/integration_tests.html" \
    --self-contained-html

# Generate test coverage report
log_message "Generating test coverage report..."
coverage run -m pytest ../.cursor ../.prompts ../.jobs ../.qa ../.research
coverage html -d "$TEST_RESULTS_DIR/coverage_report"

# Verify test results
log_message "Verifying test results..."
if [ -f "$TEST_RESULTS_DIR/python_tests.xml" ] && \
   [ -f "$TEST_RESULTS_DIR/frontend_tests.json" ] && \
   [ -f "$TEST_RESULTS_DIR/integration_tests.xml" ]; then
    log_message "Tests completed successfully"
    exit 0
else
    log_message "ERROR: Test verification failed"
    exit 1
fi 