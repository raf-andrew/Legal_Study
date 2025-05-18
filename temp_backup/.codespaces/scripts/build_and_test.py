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

class CodespaceBuilder:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.config_path = self.root_dir / "config" / "codespaces_config.yaml"
        self.data_dir = self.root_dir / "data"
        self.logs_dir = self.root_dir / "logs"

        # Setup logging
        self._setup_logging()

        # Load configuration
        self.config = self._load_config()

        # Initialize Docker client
        self.docker_client = docker.from_env()

        # Initialize deployment tracker
        self.tracker = DeploymentTracker()

    def _setup_logging(self):
        """Configure logging for the builder."""
        log_file = self.logs_dir / f"build_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
            self.tracker.add_error("command_failed", str(e), {
                "command": ' '.join(command),
                "error": e.stderr
            })
            return False

    def build_services(self):
        """Build all configured services."""
        self._print_status("Building services...", "info")

        services = self.config["services"]
        for service_name, service_config in services.items():
            if not service_config.get("enabled", True):
                continue

            self._print_status(f"Building {service_name}...", "info")

            try:
                # Build Docker image
                if not self._run_command(["docker-compose", "build", service_name]):
                    self.tracker.update_service_status(service_name, "build_failed")
                    continue

                self.tracker.update_service_status(service_name, "built")
            except Exception as e:
                self.logger.error(f"Failed to build {service_name}: {e}")
                self.tracker.update_service_status(service_name, "build_failed", {"error": str(e)})
                continue

        self._print_status("Services built successfully", "success")
        return True

    def start_services(self):
        """Start all configured services."""
        self._print_status("Starting services...", "info")

        # Start all services
        if not self._run_command(["docker-compose", "up", "-d"]):
            return False

        # Wait for services to be ready
        self._wait_for_services()

        self._print_status("Services started successfully", "success")
        return True

    def _wait_for_services(self):
        """Wait for all services to be healthy."""
        services = self.config["services"]
        for service_name, service_config in services.items():
            if not service_config.get("enabled", True):
                continue

            self._print_status(f"Waiting for {service_name} to be ready...", "info")

            # Check container health
            try:
                container = self.docker_client.containers.get(service_name)
                container.wait(condition="healthy", timeout=60)
                self.tracker.update_service_status(service_name, "healthy")
            except Exception as e:
                self.logger.error(f"Service {service_name} failed health check: {e}")
                self.tracker.update_service_status(service_name, "unhealthy", {"error": str(e)})

    def run_tests(self):
        """Run all configured tests."""
        self._print_status("Running tests...", "info")

        test_config = self.config["testing"]
        if not test_config.get("enabled", True):
            self._print_status("Testing disabled in configuration", "warning")
            return True

        test_types = test_config.get("types", ["unit"])
        for test_type in test_types:
            self._print_status(f"Running {test_type} tests...", "info")

            # Run tests using pytest
            if not self._run_command(["pytest", f"tests/{test_type}", "-v"]):
                self.tracker.update_test_results(test_type, {"status": "failed"})
                continue

            # Parse test results
            try:
                with open(f"reports/{test_type}_report.json", 'r') as f:
                    test_results = json.load(f)
                self.tracker.update_test_results(test_type, test_results)
            except Exception as e:
                self.logger.error(f"Failed to parse test results: {e}")
                self.tracker.update_test_results(test_type, {"status": "error", "error": str(e)})

        self._print_status("Tests completed", "success")
        return True

    def run_health_checks(self):
        """Run health checks for all services."""
        self._print_status("Running health checks...", "info")

        services = self.config["services"]
        for service_name, service_config in services.items():
            if not service_config.get("enabled", True):
                continue

            health_check = service_config.get("health_check")
            if not health_check:
                continue

            port = service_config.get("port")
            if not port:
                continue

            try:
                response = requests.get(f"http://localhost:{port}{health_check}")
                if response.status_code == 200:
                    self.tracker.update_health_check(service_name, "healthy")
                else:
                    self.tracker.update_health_check(service_name, "unhealthy", {
                        "status_code": response.status_code
                    })
            except Exception as e:
                self.logger.error(f"Health check failed for {service_name}: {e}")
                self.tracker.update_health_check(service_name, "unhealthy", {"error": str(e)})

        self._print_status("Health checks completed", "success")
        return True

    def setup_monitoring(self):
        """Set up monitoring and logging infrastructure."""
        self._print_status("Setting up monitoring...", "info")

        monitoring_config = self.config["monitoring"]
        if not monitoring_config.get("enabled", True):
            self._print_status("Monitoring disabled in configuration", "warning")
            return True

        # Start Prometheus
        if not self._run_command(["docker-compose", "up", "-d", "prometheus"]):
            return False

        # Start Grafana
        if not self._run_command(["docker-compose", "up", "-d", "grafana"]):
            return False

        self._print_status("Monitoring setup completed", "success")
        return True

    def run(self):
        """Run the complete build and test process."""
        try:
            # Start tracking deployment
            self.tracker.start_deployment()

            steps = [
                (self.build_services, "Building Services"),
                (self.start_services, "Starting Services"),
                (self.run_tests, "Running Tests"),
                (self.run_health_checks, "Health Checks"),
                (self.setup_monitoring, "Monitoring Setup")
            ]

            for step_func, step_name in steps:
                self._print_status(f"Starting {step_name}...", "info")
                if not step_func():
                    self._print_status(f"{step_name} failed", "error")
                    self.tracker.complete_deployment("failed")
                    return False
                self._print_status(f"{step_name} completed successfully", "success")

            self.tracker.complete_deployment("completed")
            self._print_status("Build and test process completed successfully!", "success")
            return True

        except Exception as e:
            self.logger.error(f"Build and test process failed: {e}")
            self.tracker.add_error("build_failed", str(e))
            self.tracker.complete_deployment("failed")
            return False

if __name__ == "__main__":
    builder = CodespaceBuilder()
    success = builder.run()
    sys.exit(0 if success else 1)
