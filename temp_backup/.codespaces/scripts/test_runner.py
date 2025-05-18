#!/usr/bin/env python3

import os
import sys
import yaml
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import docker
import requests
from colorama import init, Fore, Style
from deployment_tracker import DeploymentTracker

# Initialize colorama
init()

class TestRunner:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.config_path = self.root_dir / "config" / "codespaces_config.yaml"
        self.data_dir = self.root_dir / "data"
        self.logs_dir = self.root_dir / "logs"
        self.reports_dir = self.root_dir / "reports"

        # Create reports directory if it doesn't exist
        self.reports_dir.mkdir(exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Load configuration
        self.config = self._load_config()

        # Initialize Docker client
        self.docker_client = docker.from_env()

        # Initialize deployment tracker
        self.tracker = DeploymentTracker()

    def _setup_logging(self):
        """Configure logging for the test runner."""
        log_file = self.logs_dir / f"test_runner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self) -> Dict:
        """Load the Codespaces configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def _print_status(self, message: str, status: str = "info"):
        """Print a formatted status message."""
        colors = {
            "info": Fore.BLUE,
            "success": Fore.GREEN,
            "error": Fore.RED,
            "warning": Fore.YELLOW
        }
        color = colors.get(status, Fore.WHITE)
        print(f"{color}[{status.upper()}] {message}{Style.RESET_ALL}")

    def _run_command(self, command: List[str], cwd: Optional[str] = None) -> bool:
        """Run a shell command and return its success status."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True
            )
            self.logger.info(f"Command succeeded: {' '.join(command)}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(command)}")
            self.logger.error(f"Error: {e.stderr}")
            return False

    def run_unit_tests(self) -> bool:
        """Run unit tests."""
        self._print_status("Running unit tests...", "info")

        try:
            # Run pytest with coverage
            if not self._run_command([
                "pytest",
                "tests/unit",
                "-v",
                "--cov=.",
                "--cov-report=json:reports/unit_coverage.json",
                "--junitxml=reports/unit_tests.xml"
            ]):
                return False

            # Parse test results
            with open("reports/unit_tests.xml", 'r') as f:
                test_results = f.read()

            # Parse coverage results
            with open("reports/unit_coverage.json", 'r') as f:
                coverage_results = json.load(f)

            # Update deployment tracker
            self.tracker.update_test_results("unit", {
                "status": "completed",
                "results": test_results,
                "coverage": coverage_results
            })

            self._print_status("Unit tests completed successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Unit tests failed: {e}")
            self.tracker.update_test_results("unit", {
                "status": "failed",
                "error": str(e)
            })
            return False

    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        self._print_status("Running integration tests...", "info")

        try:
            # Run pytest with coverage
            if not self._run_command([
                "pytest",
                "tests/integration",
                "-v",
                "--cov=.",
                "--cov-report=json:reports/integration_coverage.json",
                "--junitxml=reports/integration_tests.xml"
            ]):
                return False

            # Parse test results
            with open("reports/integration_tests.xml", 'r') as f:
                test_results = f.read()

            # Parse coverage results
            with open("reports/integration_coverage.json", 'r') as f:
                coverage_results = json.load(f)

            # Update deployment tracker
            self.tracker.update_test_results("integration", {
                "status": "completed",
                "results": test_results,
                "coverage": coverage_results
            })

            self._print_status("Integration tests completed successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Integration tests failed: {e}")
            self.tracker.update_test_results("integration", {
                "status": "failed",
                "error": str(e)
            })
            return False

    def run_e2e_tests(self) -> bool:
        """Run end-to-end tests."""
        self._print_status("Running end-to-end tests...", "info")

        try:
            # Run pytest with coverage
            if not self._run_command([
                "pytest",
                "tests/e2e",
                "-v",
                "--cov=.",
                "--cov-report=json:reports/e2e_coverage.json",
                "--junitxml=reports/e2e_tests.xml"
            ]):
                return False

            # Parse test results
            with open("reports/e2e_tests.xml", 'r') as f:
                test_results = f.read()

            # Parse coverage results
            with open("reports/e2e_coverage.json", 'r') as f:
                coverage_results = json.load(f)

            # Update deployment tracker
            self.tracker.update_test_results("e2e", {
                "status": "completed",
                "results": test_results,
                "coverage": coverage_results
            })

            self._print_status("End-to-end tests completed successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"End-to-end tests failed: {e}")
            self.tracker.update_test_results("e2e", {
                "status": "failed",
                "error": str(e)
            })
            return False

    def run_performance_tests(self) -> bool:
        """Run performance tests."""
        self._print_status("Running performance tests...", "info")

        try:
            # Run locust for performance testing
            if not self._run_command([
                "locust",
                "--host=http://localhost:8000",
                "--headless",
                "--users=100",
                "--spawn-rate=10",
                "--run-time=1m",
                "--json=reports/performance_results.json"
            ]):
                return False

            # Parse performance results
            with open("reports/performance_results.json", 'r') as f:
                performance_results = json.load(f)

            # Update deployment tracker
            self.tracker.update_test_results("performance", {
                "status": "completed",
                "results": performance_results
            })

            self._print_status("Performance tests completed successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Performance tests failed: {e}")
            self.tracker.update_test_results("performance", {
                "status": "failed",
                "error": str(e)
            })
            return False

    def generate_test_report(self):
        """Generate a comprehensive test report."""
        self._print_status("Generating test report...", "info")

        try:
            # Collect all test results
            test_results = {}
            for test_type in ["unit", "integration", "e2e", "performance"]:
                try:
                    with open(f"reports/{test_type}_tests.xml", 'r') as f:
                        test_results[test_type] = f.read()
                except FileNotFoundError:
                    test_results[test_type] = "No results available"

            # Collect all coverage results
            coverage_results = {}
            for test_type in ["unit", "integration", "e2e"]:
                try:
                    with open(f"reports/{test_type}_coverage.json", 'r') as f:
                        coverage_results[test_type] = json.load(f)
                except FileNotFoundError:
                    coverage_results[test_type] = "No coverage data available"

            # Generate HTML report
            report_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .section { margin-bottom: 20px; }
                    .success { color: green; }
                    .failure { color: red; }
                    .warning { color: orange; }
                </style>
            </head>
            <body>
                <h1>Test Report</h1>
                <div class="section">
                    <h2>Test Results</h2>
                    <pre>{test_results}</pre>
                </div>
                <div class="section">
                    <h2>Coverage Results</h2>
                    <pre>{coverage_results}</pre>
                </div>
            </body>
            </html>
            """

            with open("reports/test_report.html", 'w') as f:
                f.write(report_template.format(
                    test_results=json.dumps(test_results, indent=2),
                    coverage_results=json.dumps(coverage_results, indent=2)
                ))

            self._print_status("Test report generated successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to generate test report: {e}")
            return False

    def run(self):
        """Run all tests and generate report."""
        try:
            self._print_status("Starting test suite...", "info")

            test_types = {
                "unit": self.run_unit_tests,
                "integration": self.run_integration_tests,
                "e2e": self.run_e2e_tests,
                "performance": self.run_performance_tests
            }

            success = True
            for test_type, test_func in test_types.items():
                self._print_status(f"Running {test_type} tests...", "info")
                if not test_func():
                    success = False
                    self._print_status(f"{test_type} tests failed", "error")

            if success:
                self._print_status("All tests completed successfully", "success")
            else:
                self._print_status("Some tests failed", "error")

            # Generate test report
            self.generate_test_report()

            return success

        except Exception as e:
            self.logger.error(f"Test suite failed: {e}")
            return False

if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run()
    sys.exit(0 if success else 1)
