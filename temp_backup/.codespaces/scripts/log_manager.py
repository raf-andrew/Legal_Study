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

class LogManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.config_path = self.root_dir / "config" / "codespaces_config.yaml"
        self.data_dir = self.root_dir / "data"
        self.logs_dir = self.root_dir / "logs"
        self.audit_dir = self.root_dir / "audit"

        # Create audit directory if it doesn't exist
        self.audit_dir.mkdir(exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Load configuration
        self.config = self._load_config()

        # Initialize Docker client
        self.docker_client = docker.from_env()

        # Initialize deployment tracker
        self.tracker = DeploymentTracker()

    def _setup_logging(self):
        """Configure logging for the log manager."""
        log_file = self.logs_dir / f"log_manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

    def setup_elasticsearch(self):
        """Set up Elasticsearch for log storage."""
        self._print_status("Setting up Elasticsearch...", "info")

        try:
            # Start Elasticsearch
            if not self._run_command(["docker-compose", "up", "-d", "elasticsearch"]):
                return False

            # Wait for Elasticsearch to be ready
            container = self.docker_client.containers.get("elasticsearch")
            container.wait(condition="healthy", timeout=60)

            # Create index for logs
            if not self._run_command([
                "curl",
                "-X", "PUT",
                "http://localhost:9200/logs",
                "-H", "Content-Type: application/json",
                "-d", '{"mappings": {"properties": {"timestamp": {"type": "date"}, "level": {"type": "keyword"}, "service": {"type": "keyword"}, "message": {"type": "text"}}}}'
            ]):
                return False

            self._print_status("Elasticsearch setup completed", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Elasticsearch: {e}")
            return False

    def setup_kibana(self):
        """Set up Kibana for log visualization."""
        self._print_status("Setting up Kibana...", "info")

        try:
            # Start Kibana
            if not self._run_command(["docker-compose", "up", "-d", "kibana"]):
                return False

            # Wait for Kibana to be ready
            container = self.docker_client.containers.get("kibana")
            container.wait(condition="healthy", timeout=60)

            self._print_status("Kibana setup completed", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup Kibana: {e}")
            return False

    def collect_service_logs(self):
        """Collect logs from all services."""
        self._print_status("Collecting service logs...", "info")

        try:
            services = self.config["services"]
            for service_name, service_config in services.items():
                if not service_config.get("enabled", True):
                    continue

                # Get container logs
                container = self.docker_client.containers.get(service_name)
                logs = container.logs().decode('utf-8')

                # Save logs to file
                log_file = self.logs_dir / f"{service_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                with open(log_file, 'w') as f:
                    f.write(logs)

                # Send logs to Elasticsearch
                for line in logs.split('\n'):
                    if line.strip():
                        log_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "level": "INFO",
                            "service": service_name,
                            "message": line
                        }

                        if not self._run_command([
                            "curl",
                            "-X", "POST",
                            "http://localhost:9200/logs/_doc",
                            "-H", "Content-Type: application/json",
                            "-d", json.dumps(log_entry)
                        ]):
                            self.logger.warning(f"Failed to send log to Elasticsearch: {line}")

            self._print_status("Service logs collected successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to collect service logs: {e}")
            return False

    def generate_audit_report(self):
        """Generate an audit report."""
        self._print_status("Generating audit report...", "info")

        try:
            # Collect deployment history
            deployment_history = self.tracker.get_deployment_summary()

            # Collect service statuses
            service_statuses = {}
            services = self.config["services"]
            for service_name, service_config in services.items():
                if not service_config.get("enabled", True):
                    continue

                try:
                    container = self.docker_client.containers.get(service_name)
                    service_statuses[service_name] = {
                        "status": container.status,
                        "health": container.attrs.get("State", {}).get("Health", {}).get("Status", "unknown")
                    }
                except Exception as e:
                    service_statuses[service_name] = {
                        "status": "error",
                        "error": str(e)
                    }

            # Generate HTML report
            report_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Audit Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .section { margin-bottom: 20px; }
                    .success { color: green; }
                    .failure { color: red; }
                    .warning { color: orange; }
                </style>
            </head>
            <body>
                <h1>Audit Report</h1>
                <div class="section">
                    <h2>Deployment History</h2>
                    <pre>{deployment_history}</pre>
                </div>
                <div class="section">
                    <h2>Service Statuses</h2>
                    <pre>{service_statuses}</pre>
                </div>
            </body>
            </html>
            """

            with open("audit/audit_report.html", 'w') as f:
                f.write(report_template.format(
                    deployment_history=json.dumps(deployment_history, indent=2),
                    service_statuses=json.dumps(service_statuses, indent=2)
                ))

            self._print_status("Audit report generated successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to generate audit report: {e}")
            return False

    def run(self):
        """Run the log management process."""
        try:
            self._print_status("Starting log management process...", "info")

            steps = [
                (self.setup_elasticsearch, "Setting up Elasticsearch"),
                (self.setup_kibana, "Setting up Kibana"),
                (self.collect_service_logs, "Collecting Service Logs"),
                (self.generate_audit_report, "Generating Audit Report")
            ]

            for step_func, step_name in steps:
                self._print_status(f"Starting {step_name}...", "info")
                if not step_func():
                    self._print_status(f"{step_name} failed", "error")
                    return False
                self._print_status(f"{step_name} completed successfully", "success")

            self._print_status("Log management process completed successfully", "success")
            return True

        except Exception as e:
            self.logger.error(f"Log management process failed: {e}")
            return False

if __name__ == "__main__":
    manager = LogManager()
    success = manager.run()
    sys.exit(0 if success else 1)
