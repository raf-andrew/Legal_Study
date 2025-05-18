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

class EnvironmentSwitch:
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
        """Configure logging for the environment switch."""
        log_file = self.logs_dir / f"env_switch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

    def stop_services(self):
        """Stop all running services."""
        self._print_status("Stopping services...", "info")

        try:
            if not self._run_command(["docker-compose", "down"]):
                return False

            self._print_status("Services stopped successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop services: {e}")
            return False

    def start_local_services(self):
        """Start services in local mode."""
        self._print_status("Starting local services...", "info")

        try:
            # Update environment variables for local mode
            env_file = self.root_dir / ".env.local"
            with open(env_file, 'w') as f:
                f.write("ENVIRONMENT=local\n")
                f.write("API_URL=http://localhost:8000\n")
                f.write("FRONTEND_URL=http://localhost:3000\n")

            # Start services using local configuration
            if not self._run_command(["docker-compose", "-f", "docker-compose.local.yml", "up", "-d"]):
                return False

            self._print_status("Local services started successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start local services: {e}")
            return False

    def start_codespace_services(self):
        """Start services in Codespaces mode."""
        self._print_status("Starting Codespaces services...", "info")

        try:
            # Update environment variables for Codespaces mode
            env_file = self.root_dir / ".env.codespaces"
            with open(env_file, 'w') as f:
                f.write("ENVIRONMENT=codespaces\n")
                f.write("API_URL=https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}\n")
                f.write("FRONTEND_URL=https://${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}\n")

            # Start services using Codespaces configuration
            if not self._run_command(["docker-compose", "-f", "docker-compose.codespaces.yml", "up", "-d"]):
                return False

            self._print_status("Codespaces services started successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start Codespaces services: {e}")
            return False

    def switch_to_local(self):
        """Switch to local environment."""
        self._print_status("Switching to local environment...", "info")

        try:
            # Stop current services
            if not self.stop_services():
                return False

            # Start local services
            if not self.start_local_services():
                return False

            self._print_status("Successfully switched to local environment", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to switch to local environment: {e}")
            return False

    def switch_to_codespaces(self):
        """Switch to Codespaces environment."""
        self._print_status("Switching to Codespaces environment...", "info")

        try:
            # Stop current services
            if not self.stop_services():
                return False

            # Start Codespaces services
            if not self.start_codespace_services():
                return False

            self._print_status("Successfully switched to Codespaces environment", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to switch to Codespaces environment: {e}")
            return False

    def run(self, target_env: str):
        """Run the environment switch process."""
        try:
            if target_env.lower() == "local":
                return self.switch_to_local()
            elif target_env.lower() == "codespaces":
                return self.switch_to_codespaces()
            else:
                self._print_status(f"Invalid target environment: {target_env}", "error")
                return False

        except Exception as e:
            self.logger.error(f"Environment switch failed: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python environment_switch.py [local|codespaces]")
        sys.exit(1)

    target_env = sys.argv[1]
    switch = EnvironmentSwitch()
    success = switch.run(target_env)
    sys.exit(0 if success else 1)
