#!/bin/bash

# Test Automation Script

# Set up environment
echo "Setting up test environment..."
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p .logs .errors .complete

# Run tests
echo "Running tests..."

# Smoke tests
echo "Running smoke tests..."
pytest -m smoke --cov=app --cov-report=term --cov-report=html --html=test_report_smoke.html --self-contained-html
SMOKE_RESULT=$?

# ACID tests
echo "Running ACID tests..."
pytest -m acid --cov=app --cov-report=term --cov-report=html --html=test_report_acid.html --self-contained-html
ACID_RESULT=$?

# Chaos tests
echo "Running chaos tests..."
pytest -m chaos --cov=app --cov-report=term --cov-report=html --html=test_report_chaos.html --self-contained-html
CHAOS_RESULT=$?

# Security tests
echo "Running security tests..."
pytest -m security --cov=app --cov-report=term --cov-report=html --html=test_report_security.html --self-contained-html
SECURITY_RESULT=$?

# Generate final report
echo "Generating final report..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE=".complete/test_report_${TIMESTAMP}.md"

cat > $REPORT_FILE << EOF
# Test Execution Report
Date: $(date)

## Test Results
- Smoke Tests: $(if [ $SMOKE_RESULT -eq 0 ]; then echo "PASSED"; else echo "FAILED"; fi)
- ACID Tests: $(if [ $ACID_RESULT -eq 0 ]; then echo "PASSED"; else echo "FAILED"; fi)
- Chaos Tests: $(if [ $CHAOS_RESULT -eq 0 ]; then echo "PASSED"; else echo "FAILED"; fi)
- Security Tests: $(if [ $SECURITY_RESULT -eq 0 ]; then echo "PASSED"; else echo "FAILED"; fi)

## Coverage Report
$(coverage report)

## Error Logs
$(find .errors -type f -exec cat {} \;)

## Next Steps
$(if [ $SMOKE_RESULT -eq 0 ] && [ $ACID_RESULT -eq 0 ] && [ $CHAOS_RESULT -eq 0 ] && [ $SECURITY_RESULT -eq 0 ]; then
    echo "All tests passed successfully. Proceed with deployment."
else
    echo "Some tests failed. Please review the error logs and fix the issues."
fi)
EOF

# Clean up
echo "Cleaning up..."
deactivate
rm -rf venv
rm -rf .pytest_cache
rm -rf __pycache__
rm -rf .coverage

# Exit with appropriate status
if [ $SMOKE_RESULT -eq 0 ] && [ $ACID_RESULT -eq 0 ] && [ $CHAOS_RESULT -eq 0 ] && [ $SECURITY_RESULT -eq 0 ]; then
    echo "All tests passed successfully!"
    exit 0
else
    echo "Some tests failed. Please check the reports and logs."
    exit 1
fi 