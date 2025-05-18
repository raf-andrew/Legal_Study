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

# Initialize colorama
init()

class CodespaceSetup:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.config_path = self.root_dir / "config" / "codespaces_config.yaml"
        self.data_dir = self.root_dir / "data"
        self.logs_dir = self.root_dir / "logs"
        self.audit_dir = self.root_dir / "audit"

        # Setup logging
        self._setup_logging()

        # Load configuration
        self.config = self._load_config()

        # Initialize Docker client
        self.docker_client = docker.from_env()

        # Track deployment status
        self.deployment_status = {
            "start_time": datetime.now().isoformat(),
            "services": {},
            "tests": {},
            "health_checks": {},
            "errors": []
        }

    def _setup_logging(self):
        """Configure logging for the setup process."""
        log_file = self.logs_dir / f"setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

    def _save_deployment_status(self):
        """Save the current deployment status to a JSON file."""
        status_file = self.data_dir / "deployment_status.json"
        with open(status_file, 'w') as f:
            json.dump(self.deployment_status, f, indent=2)

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
            self.deployment_status["errors"].append({
                "command": ' '.join(command),
                "error": e.stderr,
                "timestamp": datetime.now().isoformat()
            })
            return False

    def setup_environment(self):
        """Set up the Codespaces environment."""
        self._print_status("Setting up Codespaces environment...", "info")

        # Create necessary directories
        for directory in [self.data_dir, self.logs_dir, self.audit_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Install dependencies
        if not self._run_command(["pip", "install", "-r", "requirements.txt"]):
            return False

        self._print_status("Environment setup completed", "success")
        return True

    def setup_services(self):
        """Set up and start all configured services."""
        self._print_status("Setting up services...", "info")

        # Build and start Docker services
        if not self._run_command(["docker-compose", "build"]):
            return False

        if not self._run_command(["docker-compose", "up", "-d"]):
            return False

        # Wait for services to be ready
        self._wait_for_services()

        self._print_status("Services setup completed", "success")
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
                self.deployment_status["services"][service_name] = "healthy"
            except Exception as e:
                self.logger.error(f"Service {service_name} failed health check: {e}")
                self.deployment_status["services"][service_name] = "unhealthy"
                self.deployment_status["errors"].append({
                    "service": service_name,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })

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
                self.deployment_status["tests"][test_type] = "failed"
                continue

            self.deployment_status["tests"][test_type] = "passed"

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
                    self.deployment_status["health_checks"][service_name] = "healthy"
                else:
                    self.deployment_status["health_checks"][service_name] = "unhealthy"
            except Exception as e:
                self.logger.error(f"Health check failed for {service_name}: {e}")
                self.deployment_status["health_checks"][service_name] = "unhealthy"

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
        """Run the complete setup process."""
        try:
            steps = [
                (self.setup_environment, "Environment Setup"),
                (self.setup_services, "Services Setup"),
                (self.run_tests, "Testing"),
                (self.run_health_checks, "Health Checks"),
                (self.setup_monitoring, "Monitoring Setup")
            ]

            for step_func, step_name in steps:
                self._print_status(f"Starting {step_name}...", "info")
                if not step_func():
                    self._print_status(f"{step_name} failed", "error")
                    self._save_deployment_status()
                    return False
                self._print_status(f"{step_name} completed successfully", "success")

            self._save_deployment_status()
            self._print_status("Setup completed successfully!", "success")
            return True

        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            self.deployment_status["errors"].append({
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            self._save_deployment_status()
            return False

if __name__ == "__main__":
    setup = CodespaceSetup()
    success = setup.run()
    sys.exit(0 if success else 1)
