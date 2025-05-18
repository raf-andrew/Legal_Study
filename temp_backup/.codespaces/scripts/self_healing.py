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

class SelfHealing:
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
        """Configure logging for the self-healing system."""
        log_file = self.logs_dir / f"self_healing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

    def check_service_health(self, service_name: str, service_config: Dict) -> bool:
        """Check the health of a specific service."""
        health_check = service_config.get("health_check")
        if not health_check:
            return True

        port = service_config.get("port")
        if not port:
            return True

        try:
            response = requests.get(f"http://localhost:{port}{health_check}")
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Health check failed for {service_name}: {e}")
            return False

    def restart_service(self, service_name: str) -> bool:
        """Restart a specific service."""
        self._print_status(f"Restarting service {service_name}...", "info")

        try:
            # Stop the service
            if not self._run_command(["docker-compose", "stop", service_name]):
                return False

            # Start the service
            if not self._run_command(["docker-compose", "up", "-d", service_name]):
                return False

            # Wait for service to be healthy
            container = self.docker_client.containers.get(service_name)
            container.wait(condition="healthy", timeout=60)

            self._print_status(f"Service {service_name} restarted successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restart service {service_name}: {e}")
            return False

    def check_database_health(self) -> bool:
        """Check the health of the database service."""
        db_config = self.config["services"].get("db")
        if not db_config:
            return True

        try:
            # Check if database container is running
            container = self.docker_client.containers.get("db")
            if container.status != "running":
                return False

            # Check database connection
            if not self._run_command(["docker-compose", "exec", "db", "pg_isready"]):
                return False

            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False

    def repair_database(self) -> bool:
        """Attempt to repair the database service."""
        self._print_status("Attempting to repair database...", "info")

        try:
            # Stop database
            if not self._run_command(["docker-compose", "stop", "db"]):
                return False

            # Remove database volume
            if not self._run_command(["docker-compose", "down", "-v"]):
                return False

            # Start database
            if not self._run_command(["docker-compose", "up", "-d", "db"]):
                return False

            # Wait for database to be ready
            container = self.docker_client.containers.get("db")
            container.wait(condition="healthy", timeout=60)

            self._print_status("Database repaired successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to repair database: {e}")
            return False

    def check_cache_health(self) -> bool:
        """Check the health of the cache service."""
        cache_config = self.config["services"].get("redis")
        if not cache_config:
            return True

        try:
            # Check if cache container is running
            container = self.docker_client.containers.get("redis")
            if container.status != "running":
                return False

            # Check cache connection
            if not self._run_command(["docker-compose", "exec", "redis", "redis-cli", "ping"]):
                return False

            return True
        except Exception as e:
            self.logger.error(f"Cache health check failed: {e}")
            return False

    def repair_cache(self) -> bool:
        """Attempt to repair the cache service."""
        self._print_status("Attempting to repair cache...", "info")

        try:
            # Stop cache
            if not self._run_command(["docker-compose", "stop", "redis"]):
                return False

            # Remove cache volume
            if not self._run_command(["docker-compose", "down", "-v"]):
                return False

            # Start cache
            if not self._run_command(["docker-compose", "up", "-d", "redis"]):
                return False

            # Wait for cache to be ready
            container = self.docker_client.containers.get("redis")
            container.wait(condition="healthy", timeout=60)

            self._print_status("Cache repaired successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to repair cache: {e}")
            return False

    def run_health_checks(self):
        """Run health checks for all services."""
        self._print_status("Running health checks...", "info")

        services = self.config["services"]
        for service_name, service_config in services.items():
            if not service_config.get("enabled", True):
                continue

            if not self.check_service_health(service_name, service_config):
                self._print_status(f"Service {service_name} is unhealthy", "error")
                if not self.restart_service(service_name):
                    self._print_status(f"Failed to restart service {service_name}", "error")
                    return False

        # Check database health
        if not self.check_database_health():
            self._print_status("Database is unhealthy", "error")
            if not self.repair_database():
                self._print_status("Failed to repair database", "error")
                return False

        # Check cache health
        if not self.check_cache_health():
            self._print_status("Cache is unhealthy", "error")
            if not self.repair_cache():
                self._print_status("Failed to repair cache", "error")
                return False

        self._print_status("All services are healthy", "success")
        return True

    def run(self):
        """Run the self-healing process."""
        try:
            self._print_status("Starting self-healing process...", "info")

            if not self.run_health_checks():
                self._print_status("Self-healing process failed", "error")
                return False

            self._print_status("Self-healing process completed successfully", "success")
            return True

        except Exception as e:
            self.logger.error(f"Self-healing process failed: {e}")
            return False

if __name__ == "__main__":
    healing = SelfHealing()
    success = healing.run()
    sys.exit(0 if success else 1)
