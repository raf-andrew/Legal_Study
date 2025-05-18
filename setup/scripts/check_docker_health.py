#!/usr/bin/env python3

import os
import sys
import json
import time
import requests
from pathlib import Path
import docker
from docker.errors import DockerException
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

class DockerHealthChecker:
    def __init__(self):
        self.client = docker.from_env()
        self.services = {
            "api": {"port": 8000, "path": "/health"},
            "frontend": {"port": 3000, "path": "/health"},
            "database": {"port": 5432},
            "cache": {"port": 6379},
            "queue": {"port": 5672}
        }
        self.health_status = {}

    def _print_success(self, text: str):
        """Print a success message"""
        print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

    def _print_error(self, text: str):
        """Print an error message"""
        print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

    def check_container_health(self, container_name: str) -> bool:
        """Check the health status of a Docker container"""
        try:
            container = self.client.containers.get(container_name)
            health = container.attrs.get("State", {}).get("Health", {})

            if not health:
                return True  # Container doesn't have health check configured

            status = health.get("Status")
            if status == "healthy":
                self._print_success(f"Container {container_name} is healthy")
                return True
            else:
                self._print_error(f"Container {container_name} is {status}")
                return False
        except DockerException as e:
            self._print_error(f"Error checking container {container_name}: {str(e)}")
            return False

    def check_service_health(self, service_name: str, config: dict) -> bool:
        """Check the health of a service using its health endpoint"""
        if "path" not in config:
            return True  # Service doesn't have a health endpoint

        try:
            response = requests.get(
                f"http://localhost:{config['port']}{config['path']}",
                timeout=5
            )
            if response.status_code == 200:
                self._print_success(f"Service {service_name} is healthy")
                return True
            else:
                self._print_error(f"Service {service_name} returned status {response.status_code}")
                return False
        except requests.RequestException as e:
            self._print_error(f"Error checking service {service_name}: {str(e)}")
            return False

    def check_port_availability(self, port: int) -> bool:
        """Check if a port is available and listening"""
        try:
            response = requests.get(f"http://localhost:{port}", timeout=5)
            return True
        except requests.RequestException:
            return False

    def run_health_checks(self) -> bool:
        """Run all health checks"""
        print("\nRunning Docker health checks...")

        all_healthy = True

        # Check container health
        for container in self.client.containers.list():
            if not self.check_container_health(container.name):
                all_healthy = False

        # Check service health
        for service_name, config in self.services.items():
            if not self.check_service_health(service_name, config):
                all_healthy = False

            # Check port availability
            if not self.check_port_availability(config["port"]):
                self._print_error(f"Port {config['port']} for {service_name} is not available")
                all_healthy = False

        # Save health status
        self.health_status = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "all_healthy": all_healthy,
            "services": {
                service: {
                    "healthy": self.check_service_health(service, config),
                    "port_available": self.check_port_availability(config["port"])
                }
                for service, config in self.services.items()
            }
        }

        # Save to file
        status_file = Path("setup/checks/docker_health.json")
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, "w") as f:
            json.dump(self.health_status, f, indent=2)

        return all_healthy

def main():
    checker = DockerHealthChecker()
    if not checker.run_health_checks():
        sys.exit(1)

if __name__ == "__main__":
    main()
