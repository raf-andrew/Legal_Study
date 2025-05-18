#!/bin/bash

# Exit on any error
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Create necessary directories
log "Creating necessary directories..."
mkdir -p .codespaces/{logs,complete,verification,checklist,docs,issues,services}

# Run health check
log "Running health check..."
python .codespaces/scripts/health_check.py

# Run test cycles
log "Starting test cycles..."
python .codespaces/scripts/run_test_cycles.py

# Generate final report
log "Generating final report..."
php artisan test:report --output=.codespaces/reports/final_report_$(date +%Y%m%d_%H%M%S).html

log "Testing process completed!"
