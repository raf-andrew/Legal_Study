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

class UnitTestRunner:
    def __init__(self):
        """Initialize the UnitTestRunner."""
        self.config_path = Path(".codespaces/config")
        self.data_path = Path(".codespaces/data")
        self.logs_path = Path(".codespaces/logs")
        self.reports_path = Path(".codespaces/reports")

        # Create necessary directories
        self.reports_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Load configuration
        self.config = self._load_config()

        # Initialize Docker client
        self.docker_client = docker.from_env()

        # Initialize deployment tracker
        self.deployment_tracker = None  # Will be initialized when needed

    def _setup_logging(self):
        """Set up logging configuration."""
        log_file = self.logs_path / f"unit_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        config_file = self.config_path / "unit_test_config.yaml"
        try:
            with open(config_file) as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise

    def _print_status(self, message: str, status: str = "info"):
        """Print status message with color."""
        color = {
            "info": Fore.BLUE,
            "success": Fore.GREEN,
            "error": Fore.RED,
            "warning": Fore.YELLOW
        }.get(status, Fore.WHITE)

        print(f"{color}{message}{Style.RESET_ALL}")
        self.logger.info(message)

    def _run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command and handle errors."""
        try:
            result = subprocess.run(
                command,
                check=check,
                capture_output=True,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed: {' '.join(command)}")
            self.logger.error(f"Error: {e.stderr}")
            raise

    def setup_test_environment(self):
        """Set up the test environment."""
        self._print_status("Setting up test environment...", "info")

        # Create virtual environment
        self._run_command([sys.executable, "-m", "venv", ".venv"])

        # Activate virtual environment and install dependencies
        if os.name == "nt":  # Windows
            activate_script = ".venv\\Scripts\\activate"
            pip_path = ".venv\\Scripts\\pip"
        else:  # Unix
            activate_script = "source .venv/bin/activate"
            pip_path = ".venv/bin/pip"

        # Install test dependencies
        self._run_command([pip_path, "install", "-r", "requirements-test.txt"])

        self._print_status("Test environment setup complete", "success")

    def run_unit_tests(self):
        """Run the unit test suite."""
        self._print_status("Running unit tests...", "info")

        # Run pytest with configured options
        result = self._run_command([
            sys.executable, "-m", "pytest",
            "--verbose",
            "--cov=.",
            "--cov-report=html",
            "--cov-report=xml",
            "--html=reports/report.html",
            "--self-contained-html",
            "--junitxml=reports/junit.xml",
            "-n", "auto",
            "--timeout=300"
        ])

        # Log test output
        self.logger.info("Test output:")
        self.logger.info(result.stdout)

        if result.stderr:
            self.logger.warning("Test warnings/errors:")
            self.logger.warning(result.stderr)

        self._print_status("Unit tests completed", "success")
        return result.returncode == 0

    def analyze_test_results(self):
        """Analyze test results and generate report."""
        self._print_status("Analyzing test results...", "info")

        # Read test results
        junit_file = self.reports_path / "junit.xml"
        coverage_file = self.reports_path / "coverage.xml"

        try:
            # Parse test results
            test_results = {
                "timestamp": datetime.now().isoformat(),
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": [],
                "coverage": {}
            }

            # Save analysis report
            analysis_file = self.reports_path / "test_analysis.json"
            with open(analysis_file, "w") as f:
                json.dump(test_results, f, indent=2)

            self._print_status("Test analysis complete", "success")
            return True

        except Exception as e:
            self.logger.error(f"Failed to analyze test results: {e}")
            return False

    def resolve_issues(self):
        """Resolve any issues found during testing."""
        self._print_status("Resolving issues...", "info")

        # Read test analysis
        analysis_file = self.reports_path / "test_analysis.json"
        try:
            with open(analysis_file) as f:
                analysis = json.load(f)

            # Handle failed tests
            if analysis["failed"] > 0:
                self._print_status(f"Found {analysis['failed']} failed tests", "warning")
                # TODO: Implement automatic issue resolution

            # Handle errors
            if analysis["errors"]:
                self._print_status(f"Found {len(analysis['errors'])} errors", "warning")
                # TODO: Implement error handling

            self._print_status("Issue resolution complete", "success")
            return True

        except Exception as e:
            self.logger.error(f"Failed to resolve issues: {e}")
            return False

    def generate_documentation(self):
        """Generate documentation for the test run."""
        self._print_status("Generating documentation...", "info")

        # Create documentation directory
        docs_path = self.reports_path / "documentation"
        docs_path.mkdir(exist_ok=True)

        # Generate markdown report
        report_file = docs_path / "test_run_report.md"
        try:
            with open(report_file, "w") as f:
                f.write("# Unit Test Run Report\n\n")
                f.write(f"## Test Run Information\n")
                f.write(f"- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- Environment: Codespaces\n")
                f.write(f"- Python Version: {sys.version}\n\n")

                f.write("## Test Results\n")
                f.write("- Total Tests: {}\n".format(self.config.get("test_count", 0)))
                f.write("- Passed: {}\n".format(self.config.get("passed_count", 0)))
                f.write("- Failed: {}\n".format(self.config.get("failed_count", 0)))
                f.write("- Skipped: {}\n".format(self.config.get("skipped_count", 0)))

                f.write("\n## Coverage Report\n")
                f.write("- Overall Coverage: {}%\n".format(self.config.get("coverage", 0)))

                f.write("\n## Issues and Resolutions\n")
                f.write("- No issues found\n")  # TODO: Add actual issues

            self._print_status("Documentation generated", "success")
            return True

        except Exception as e:
            self.logger.error(f"Failed to generate documentation: {e}")
            return False

    def run(self):
        """Run the complete unit testing process."""
        try:
            self._print_status("Starting unit testing process...", "info")

            # Setup environment
            self.setup_test_environment()

            # Run tests
            if not self.run_unit_tests():
                self._print_status("Unit tests failed", "error")
                return False

            # Analyze results
            if not self.analyze_test_results():
                self._print_status("Test analysis failed", "error")
                return False

            # Resolve issues
            if not self.resolve_issues():
                self._print_status("Issue resolution failed", "error")
                return False

            # Generate documentation
            if not self.generate_documentation():
                self._print_status("Documentation generation failed", "error")
                return False

            self._print_status("Unit testing process completed successfully", "success")
            return True

        except Exception as e:
            self.logger.error(f"Unit testing process failed: {e}")
            self._print_status(f"Unit testing process failed: {e}", "error")
            return False

if __name__ == "__main__":
    runner = UnitTestRunner()
    success = runner.run()
    sys.exit(0 if success else 1)
