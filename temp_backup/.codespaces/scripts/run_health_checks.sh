#!/bin/bash

set -e

# Error handling
trap 'echo "Error occurred at line $LINENO. Command: $BASH_COMMAND"' ERR

# Create necessary directories
mkdir -p .codespaces/logs
mkdir -p .codespaces/complete
mkdir -p .codespaces/verification
mkdir -p .codespaces/docs
mkdir -p .codespaces/issues

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Run health checks
run_health_checks() {
    log "Running health checks..."
    python3 .codespaces/scripts/run_health_checks.py

    if [ $? -eq 0 ]; then
        log "Health checks completed successfully"
        return 0
    else
        log "Health checks failed"
        return 1
    fi
}

# Main function
main() {
    log "Starting health check process..."

    # Run health checks
    run_health_checks

    # Exit with appropriate status
    if [ $? -eq 0 ]; then
        log "All health checks passed"
        exit 0
    else
        log "Health checks failed"
        exit 1
    fi
}

# Run main function
main
