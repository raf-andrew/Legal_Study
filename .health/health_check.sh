#!/bin/bash

# Legal Study System Health Check Script
# This script performs comprehensive health checks on the system infrastructure

# Configuration
LOG_DIR=".logs"
HEALTH_LOG="$LOG_DIR/health_check_$(date +%Y%m%d_%H%M%S).log"
ERROR_LOG="$LOG_DIR/error_check_$(date +%Y%m%d_%H%M%S).log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$HEALTH_LOG"
}

# Function to log errors
log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" | tee -a "$ERROR_LOG"
}

# Function to check directory structure
check_directory_structure() {
    log_message "Checking directory structure..."
    
    required_dirs=(
        ".cursor"
        ".prompts"
        ".jobs"
        ".qa"
        ".research"
        ".build"
        ".deployment"
        ".health"
        ".logs"
        ".backup"
        ".tests"
        ".completed"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            log_error "Missing required directory: $dir"
            return 1
        fi
    done
    
    log_message "Directory structure check passed"
    return 0
}

# Function to check file permissions
check_file_permissions() {
    log_message "Checking file permissions..."
    
    # Check if we have write permissions in key directories
    for dir in ".cursor" ".prompts" ".jobs" ".qa"; do
        if [ ! -w "$dir" ]; then
            log_error "No write permissions in directory: $dir"
            return 1
        fi
    done
    
    log_message "File permissions check passed"
    return 0
}

# Function to check build system
check_build_system() {
    log_message "Checking build system..."
    
    if [ ! -d ".build" ]; then
        log_error "Build directory not found"
        return 1
    fi
    
    # Check for required build files
    required_build_files=(
        ".build/build_scripts/setup.sh"
        ".build/build_scripts/compile.sh"
        ".build/build_scripts/test.sh"
    )
    
    for file in "${required_build_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Missing build file: $file"
            return 1
        fi
    done
    
    log_message "Build system check passed"
    return 0
}

# Function to check QA system
check_qa_system() {
    log_message "Checking QA system..."
    
    if [ ! -d ".qa" ]; then
        log_error "QA directory not found"
        return 1
    fi
    
    # Check for required QA files
    required_qa_files=(
        ".qa/checklists/job_management_qa.md"
        ".qa/checklists/prompt_qa.md"
        ".qa/checklists/research_qa.md"
    )
    
    for file in "${required_qa_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Missing QA file: $file"
            return 1
        fi
    done
    
    log_message "QA system check passed"
    return 0
}

# Function to check test system
check_test_system() {
    log_message "Checking test system..."
    
    if [ ! -d ".tests" ]; then
        log_error "Tests directory not found"
        return 1
    fi
    
    # Check for required test files
    required_test_files=(
        ".tests/unit_tests.sh"
        ".tests/integration_tests.sh"
        ".tests/end_to_end_tests.sh"
    )
    
    for file in "${required_test_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Missing test file: $file"
            return 1
        fi
    done
    
    log_message "Test system check passed"
    return 0
}

# Function to check deployment system
check_deployment_system() {
    log_message "Checking deployment system..."
    
    if [ ! -d ".deployment" ]; then
        log_error "Deployment directory not found"
        return 1
    fi
    
    # Check for required deployment files
    required_deployment_files=(
        ".deployment/deploy.sh"
        ".deployment/rollback.sh"
        ".deployment/config.json"
    )
    
    for file in "${required_deployment_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Missing deployment file: $file"
            return 1
        fi
    done
    
    log_message "Deployment system check passed"
    return 0
}

# Main execution
log_message "Starting comprehensive health check..."

# Run all checks
check_directory_structure
check_file_permissions
check_build_system
check_qa_system
check_test_system
check_deployment_system

# Check for errors
if [ -s "$ERROR_LOG" ]; then
    log_message "Health check completed with errors. Please check $ERROR_LOG for details."
    exit 1
else
    log_message "Health check completed successfully. All systems operational."
    exit 0
fi 