#!/bin/bash

# Legal Study System Compile Script
# This script compiles the system components and generates artifacts

# Configuration
LOG_DIR="../.logs"
COMPILE_LOG="$LOG_DIR/compile_$(date +%Y%m%d_%H%M%S).log"
ARTIFACTS_DIR="../.build/artifacts"
CACHE_DIR="../.build/cache"
TEMP_DIR="../.build/temp"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$COMPILE_LOG"
}

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$ARTIFACTS_DIR"
mkdir -p "$CACHE_DIR"
mkdir -p "$TEMP_DIR"

# Activate Python virtual environment
log_message "Activating Python virtual environment..."
source "../.build/venv/bin/activate"

# Compile Python components
log_message "Compiling Python components..."
python3 -m compileall ../.cursor ../.prompts ../.jobs ../.qa ../.research

# Build frontend assets
log_message "Building frontend assets..."
cd "../"
npm run build
cd ".build/build_scripts"

# Generate documentation
log_message "Generating documentation..."
mkdir -p "$ARTIFACTS_DIR/docs"
pdoc --html ../.cursor ../.prompts ../.jobs ../.qa ../.research -o "$ARTIFACTS_DIR/docs"

# Create deployment package
log_message "Creating deployment package..."
tar -czf "$ARTIFACTS_DIR/legal_study_system_$(date +%Y%m%d_%H%M%S).tar.gz" \
    ../.cursor \
    ../.prompts \
    ../.jobs \
    ../.qa \
    ../.research \
    ../.build/venv \
    ../node_modules \
    ../package.json \
    ../requirements.txt

# Verify compilation
log_message "Verifying compilation..."
if [ -f "$ARTIFACTS_DIR/legal_study_system_*.tar.gz" ] && [ -d "$ARTIFACTS_DIR/docs" ]; then
    log_message "Compilation completed successfully"
    exit 0
else
    log_message "ERROR: Compilation verification failed"
    exit 1
fi 