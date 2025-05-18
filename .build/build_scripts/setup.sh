#!/bin/bash

# Legal Study System Setup Script
# This script sets up the build environment and dependencies

# Configuration
LOG_DIR="../.logs"
SETUP_LOG="$LOG_DIR/setup_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$SETUP_LOG"
}

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check for required tools
log_message "Checking for required tools..."
required_tools=("git" "python3" "pip" "node" "npm")
for tool in "${required_tools[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        log_message "ERROR: Required tool $tool is not installed"
        exit 1
    fi
done

# Create necessary directories
log_message "Creating build directories..."
mkdir -p "../.build/artifacts"
mkdir -p "../.build/cache"
mkdir -p "../.build/temp"

# Set up Python virtual environment
log_message "Setting up Python virtual environment..."
python3 -m venv "../.build/venv"
source "../.build/venv/bin/activate"

# Install Python dependencies
log_message "Installing Python dependencies..."
pip install -r "../requirements.txt"

# Set up Node.js environment
log_message "Setting up Node.js environment..."
cd "../"
npm install
cd ".build/build_scripts"

# Verify setup
log_message "Verifying setup..."
if [ -d "../.build/venv" ] && [ -d "../node_modules" ]; then
    log_message "Setup completed successfully"
    exit 0
else
    log_message "ERROR: Setup verification failed"
    exit 1
fi 