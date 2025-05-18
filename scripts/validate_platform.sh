#!/bin/bash

# Platform Validation Script
# This script runs the complete platform validation process

# Set error handling
set -e

# Print banner
echo "================================"
echo "Platform Validation"
echo "================================"
echo "Starting validation at $(date)"
echo

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Run validation
echo "Running platform validation..."
python scripts/run_platform_validation.py

# Deactivate virtual environment
deactivate

echo
echo "Validation completed at $(date)"
echo "================================" 