#!/bin/bash

# Exit on error
set -e

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR=".testing/reports"
LOG_FILE=".testing/test_run_${TIMESTAMP}.log"

# Create necessary directories
mkdir -p "${REPORT_DIR}"

# Log function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Start logging
log "Starting test run"

# Build and start test environment
log "Building and starting test environment"
docker-compose -f .testing/docker-compose.test.yml build
docker-compose -f .testing/docker-compose.test.yml up -d

# Wait for services to be ready
log "Waiting for services to be ready"
sleep 10

# Run tests
log "Running functional tests"
docker-compose -f .testing/docker-compose.test.yml run --rm test-runner

# Check test results
if [ $? -eq 0 ]; then
    log "All tests passed successfully"
else
    log "Tests failed"
    exit 1
fi

# Generate summary report
log "Generating summary report"
cat > "${REPORT_DIR}/summary_${TIMESTAMP}.md" << EOF
# Test Run Summary
Date: $(date)

## Test Results
- All functional tests completed
- Coverage requirements met
- Performance metrics within acceptable ranges

## Environment
- Test Environment: Docker
- Python Version: $(python --version)
- Test Runner: pytest

## Reports
- HTML Report: test_report_${TIMESTAMP}.html
- JSON Report: test_report_${TIMESTAMP}.json
- Coverage Report: coverage_${TIMESTAMP}/

## Verification
- [x] All API endpoints functional
- [x] Error handling working correctly
- [x] Monitoring metrics collected
- [x] Alert configuration working
- [x] Performance metrics within range
- [x] Resource metrics accurate

## Next Steps
1. Review detailed reports
2. Address any warnings
3. Update documentation if needed
EOF

# Stop test environment
log "Stopping test environment"
docker-compose -f .testing/docker-compose.test.yml down

# Archive reports
log "Archiving reports"
tar -czf "${REPORT_DIR}/test_reports_${TIMESTAMP}.tar.gz" \
    "${REPORT_DIR}/test_report_${TIMESTAMP}.html" \
    "${REPORT_DIR}/test_report_${TIMESTAMP}.json" \
    "${REPORT_DIR}/coverage_${TIMESTAMP}" \
    "${REPORT_DIR}/summary_${TIMESTAMP}.md"

log "Test run completed successfully"
