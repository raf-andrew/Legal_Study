#!/usr/bin/env python3
"""
Test Runner Script

This script runs all test suites and generates comprehensive reports.
"""

import os
import sys
import pytest
import logging
import datetime
from pathlib import Path
import json
import subprocess
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/test_execution.log'),
        logging.StreamHandler()
    ]
)

class TestRunner:
    def __init__(self):
        self.test_results: Dict[str, Any] = {}
        self.error_log: List[Dict[str, str]] = []
        self.completed_tests: List[str] = []
        self.base_dir = Path(__file__).parent.parent
        self.errors_dir = self.base_dir / '.errors'
        self.complete_dir = self.base_dir / '.complete'
        self.setup_directories()

    def setup_directories(self):
        """Ensure all required directories exist"""
        for directory in [self.errors_dir, self.complete_dir]:
            directory.mkdir(exist_ok=True)

    def run_test_suite(self, test_file: str) -> Dict[str, Any]:
        """Run a specific test suite and return results"""
        logging.info(f"Running test suite: {test_file}")
        try:
            result = pytest.main([
                f".tests/{test_file}",
                "--verbose",
                "--tb=short",
                "--junitxml=.logs/junit.xml",
                "--html=.logs/report.html"
            ])
            return {
                "status": "passed" if result == 0 else "failed",
                "timestamp": datetime.datetime.now().isoformat(),
                "test_file": test_file
            }
        except Exception as e:
            logging.error(f"Error running test suite {test_file}: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat(),
                "test_file": test_file
            }

    def record_error(self, test_file: str, error: str):
        """Record an error to the errors directory"""
        error_file = self.errors_dir / f"{test_file}.error"
        with open(error_file, 'w') as f:
            f.write(f"Test: {test_file}\n")
            f.write(f"Time: {datetime.datetime.now().isoformat()}\n")
            f.write(f"Error: {error}\n")

    def mark_complete(self, test_file: str):
        """Mark a test as completed"""
        complete_file = self.complete_dir / f"{test_file}.complete"
        with open(complete_file, 'w') as f:
            f.write(f"Test: {test_file}\n")
            f.write(f"Completed: {datetime.datetime.now().isoformat()}\n")

    def run_all_tests(self):
        """Run all test suites in sequence"""
        test_files = [
            "test_smoke.py",
            "test_acid.py",
            "test_chaos.py",
            "test_security.py"
        ]

        for test_file in test_files:
            result = self.run_test_suite(test_file)
            self.test_results[test_file] = result

            if result["status"] != "passed":
                self.record_error(test_file, result.get("error", "Unknown error"))
            else:
                self.mark_complete(test_file)

        # Save overall results
        with open('.logs/test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)

    def check_security_requirements(self):
        """Run security checks"""
        try:
            subprocess.run(['bandit', '-r', '.'], check=True)
            subprocess.run(['safety', 'check'], check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Security check failed: {str(e)}")
            self.record_error("security_checks", str(e))

def main():
    runner = TestRunner()
    runner.check_security_requirements()
    runner.run_all_tests()

if __name__ == "__main__":
    main() 