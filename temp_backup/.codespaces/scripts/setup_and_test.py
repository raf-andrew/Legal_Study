#!/usr/bin/env python3
"""
Setup and test execution script for the Legal Study Platform
"""
import os
import sys
import time
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(message)s',
    handlers=[
        logging.FileHandler('.codespaces/logs/setup_and_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SetupAndTest:
    """Setup and test execution handler"""

    def __init__(self):
        self.reports_dir = Path('.codespaces/reports')
        self.logs_dir = Path('.codespaces/logs')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    def setup_environment(self) -> bool:
        """Setup the test environment"""
        logger.info("Setting up test environment...")

        try:
            # Create virtual environment if it doesn't exist
            venv_path = Path(".venv")
            if not venv_path.exists():
                logger.info("Creating virtual environment...")
                subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)

            # Install dependencies
            logger.info("Installing dependencies...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True)
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
            ], check=True)

            # Setup environment variables
            os.environ["TEST_ENV"] = "comprehensive"
            os.environ["VERIFICATION_LEVEL"] = "comprehensive"
            os.environ["API_BASE_URL"] = "http://localhost:8000"
            os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/legal_study"
            os.environ["CACHE_URL"] = "redis://localhost:6379/0"

            logger.info("Test environment setup complete")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to setup environment: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during setup: {e}")
            return False

    def run_unit_tests(self) -> bool:
        """Run unit tests"""
        logger.info("Running unit tests...")
        try:
            result = subprocess.run([
                sys.executable, ".codespaces/scripts/run_all_tests.py"
            ], check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            logger.error(f"Unit tests failed: {e}")
            return False

    def run_functional_tests(self) -> bool:
        """Run functional tests in live environment"""
        logger.info("Running functional tests...")
        try:
            result = subprocess.run([
                sys.executable, ".codespaces/scripts/run_functional_tests.py"
            ], check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            logger.error(f"Functional tests failed: {e}")
            return False

    def generate_setup_report(self, success: bool) -> None:
        """Generate setup and test execution report"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'success': success,
            'environment': {
                'python_version': sys.version,
                'platform': sys.platform,
                'test_env': os.getenv('TEST_ENV'),
                'verification_level': os.getenv('VERIFICATION_LEVEL')
            },
            'setup_steps': {
                'virtual_environment': Path('.venv').exists(),
                'dependencies_installed': Path('.venv/Lib/site-packages').exists(),
                'environment_variables_set': all([
                    os.getenv('TEST_ENV'),
                    os.getenv('VERIFICATION_LEVEL'),
                    os.getenv('API_BASE_URL'),
                    os.getenv('DATABASE_URL'),
                    os.getenv('CACHE_URL')
                ])
            }
        }

        report_path = self.reports_dir / 'setup_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Setup report generated: {report_path}")

    def run(self) -> bool:
        """Run the complete setup and test sequence"""
        logger.info("Starting setup and test sequence...")

        # Setup environment
        if not self.setup_environment():
            logger.error("Environment setup failed")
            self.generate_setup_report(False)
            return False

        # Run unit tests
        if not self.run_unit_tests():
            logger.error("Unit tests failed")
            self.generate_setup_report(False)
            return False

        # Run functional tests
        if not self.run_functional_tests():
            logger.error("Functional tests failed")
            self.generate_setup_report(False)
            return False

        # Generate success report
        self.generate_setup_report(True)
        logger.info("Setup and test sequence completed successfully")
        return True

def main():
    """Main entry point"""
    runner = SetupAndTest()
    success = runner.run()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
