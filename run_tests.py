#!/usr/bin/env python3
import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

def setup_test_environment():
    """Set up the test environment."""
    logging.info("Setting up test environment...")

    # Create necessary directories
    Path("reports").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    # Install test dependencies
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"], check=True)
        logging.info("Test dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install test dependencies: {e}")
        sys.exit(1)

def run_tests():
    """Run the test suite."""
    logging.info("Running tests...")

    try:
        # Run pytest with configured options
        result = subprocess.run(
            [sys.executable, "-m", "pytest"],
            capture_output=True,
            text=True
        )

        # Log test output
        logging.info("Test output:")
        logging.info(result.stdout)

        if result.stderr:
            logging.warning("Test warnings/errors:")
            logging.warning(result.stderr)

        # Check test results
        if result.returncode == 0:
            logging.info("All tests passed successfully!")
        else:
            logging.error("Some tests failed!")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        logging.error(f"Error running tests: {e}")
        sys.exit(1)

def main():
    """Main function to run the test suite."""
    try:
        setup_test_environment()
        run_tests()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
