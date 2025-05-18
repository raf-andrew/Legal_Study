#!/usr/bin/env python3
import os
import sys
import yaml
import json
import logging
import subprocess
import docker
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from colorama import init, Fore, Style

# Initialize colorama
init()

class TestRunner:
    """Test runner for Codespaces tests."""

    def __init__(self):
        """Initialize the test runner."""
        self.root_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.root_dir / ".codespaces" / "config"
        self.data_dir = self.root_dir / ".codespaces" / "data"
        self.logs_dir = self.root_dir / ".codespaces" / "logs"
        self.reports_dir = self.root_dir / ".codespaces" / "reports"

        # Create necessary directories
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.logs_dir / f"test_run_{timestamp}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.config = self._load_config()

        # Initialize Docker client
        self.docker_client = docker.from_env()

        # Track test codespaces
        self.test_codespaces = set()

    def _load_config(self):
        """Load test configuration from YAML file."""
        config_file = self.config_dir / "codespaces_test_config.yaml"
        if not config_file.exists():
            self.logger.error(f"Configuration file not found: {config_file}")
            sys.exit(1)

        with open(config_file) as f:
            return yaml.safe_load(f)

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

    def setup_test_environment(self):
        """Set up the test environment."""
        self.logger.info("Setting up test environment...")

        # Create virtual environment
        venv_dir = self.root_dir / ".venv"
        if not venv_dir.exists():
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

        # Install test dependencies
        requirements_file = self.root_dir / "requirements-test.txt"
        if requirements_file.exists():
            subprocess.run([
                str(venv_dir / "bin" / "pip"),
                "install",
                "-r",
                str(requirements_file)
            ], check=True)

    def run_tests(self):
        """Run the test suite."""
        self.logger.info("Running tests...")

        # Run pytest with coverage
        result = subprocess.run([
            sys.executable,
            "-m",
            "pytest",
            "tests/codespaces",
            "--cov=src",
            "--cov-report=html",
            "--cov-report=xml",
            "-v"
        ], capture_output=True, text=True)

        # Save test results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"test_results_{timestamp}.txt"
        with open(report_file, "w") as f:
            f.write(result.stdout)
            f.write("\n\nSTDERR:\n")
            f.write(result.stderr)

        # Copy coverage reports
        if os.path.exists("htmlcov"):
            subprocess.run(["cp", "-r", "htmlcov", str(self.reports_dir / f"coverage_html_{timestamp}")])
        if os.path.exists("coverage.xml"):
            subprocess.run(["cp", "coverage.xml", str(self.reports_dir / f"coverage_xml_{timestamp}.xml")])

        return result.returncode == 0

    def cleanup_test_codespaces(self):
        """Clean up test codespaces."""
        self.logger.info("Cleaning up test codespaces...")

        # Stop and remove test containers
        subprocess.run([
            "docker",
            "ps",
            "-a",
            "--filter",
            "name=test_",
            "-q",
            "|",
            "xargs",
            "-r",
            "docker",
            "stop"
        ], shell=True)

        subprocess.run([
            "docker",
            "ps",
            "-a",
            "--filter",
            "name=test_",
            "-q",
            "|",
            "xargs",
            "-r",
            "docker",
            "rm"
        ], shell=True)

        # Remove test volumes
        subprocess.run([
            "docker",
            "volume",
            "ls",
            "-q",
            "--filter",
            "name=test_",
            "|",
            "xargs",
            "-r",
            "docker",
            "volume",
            "rm"
        ], shell=True)

        # Remove test networks
        subprocess.run([
            "docker",
            "network",
            "ls",
            "-q",
            "--filter",
            "name=test_",
            "|",
            "xargs",
            "-r",
            "docker",
            "network",
            "rm"
        ], shell=True)

    def run(self):
        """Run the complete test suite."""
        try:
            self.setup_test_environment()
            success = self.run_tests()
            self.cleanup_test_codespaces()

            if success:
                self.logger.info("All tests completed successfully!")
                return 0
            else:
                self.logger.error("Some tests failed. Check the reports for details.")
                return 1

        except Exception as e:
            self.logger.error(f"Error during test execution: {str(e)}")
            self.cleanup_test_codespaces()
            return 1

if __name__ == "__main__":
    runner = TestRunner()
    sys.exit(runner.run())
