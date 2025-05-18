#!/usr/bin/env python3

import os
import sys
import json
import yaml
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import git
import docker
import requests
from colorama import init, Fore, Style

# Initialize colorama
init()

class DeploymentTracker:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.config_path = self.root_dir / "config" / "codespaces_config.yaml"
        self.data_dir = self.root_dir / "data"
        self.logs_dir = self.root_dir / "logs"
        self.audit_dir = self.root_dir / "audit"

        # Create data directory if it doesn't exist
        self.data_dir.mkdir(exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Load configuration
        self.config = self._load_config()

        # Initialize deployment data
        self.deployment_data = self._load_deployment_data()

    def _setup_logging(self):
        """Configure logging for the deployment tracker."""
        log_file = self.logs_dir / f"deployment_tracker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

    def _load_deployment_data(self) -> Dict:
        """Load deployment data from file."""
        deployment_file = self.data_dir / "deployment_history.json"
        if deployment_file.exists():
            try:
                with open(deployment_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load deployment data: {e}")
                return {"deployments": []}
        return {"deployments": []}

    def _save_deployment_data(self):
        """Save deployment data to file."""
        deployment_file = self.data_dir / "deployment_history.json"
        try:
            with open(deployment_file, 'w') as f:
                json.dump(self.deployment_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save deployment data: {e}")

    def _get_git_info(self) -> Dict:
        """Get current git repository information."""
        try:
            repo = git.Repo(self.root_dir.parent)
            return {
                "commit": repo.head.commit.hexsha,
                "branch": repo.active_branch.name,
                "message": repo.head.commit.message,
                "author": repo.head.commit.author.name,
                "timestamp": repo.head.commit.committed_datetime.isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get git info: {e}")
            return {}

    def _create_audit_entry(self, action: str, details: Dict):
        """Create an audit log entry."""
        timestamp = datetime.now().isoformat()
        audit_entry = {
            "timestamp": timestamp,
            "action": action,
            "details": details
        }

        audit_file = self.audit_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.json"
        try:
            if audit_file.exists():
                with open(audit_file, 'r') as f:
                    audit_log = json.load(f)
            else:
                audit_log = []

            audit_log.append(audit_entry)

            with open(audit_file, 'w') as f:
                json.dump(audit_log, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to create audit entry: {e}")

    def start_deployment(self):
        """Start tracking a new deployment."""
        deployment = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "start_time": datetime.now().isoformat(),
            "status": "in_progress",
            "services": {},
            "tests": {},
            "health_checks": {},
            "errors": []
        }

        self.deployment_data["deployments"].append(deployment)
        self._save_deployment_data()

        self.logger.info(f"Started tracking deployment {deployment['id']}")
        return deployment["id"]

    def update_service_status(self, service_name: str, status: str, details: Optional[Dict] = None):
        """Update the status of a service in the current deployment."""
        if not self.deployment_data["deployments"]:
            self.logger.error("No active deployment")
            return

        current_deployment = self.deployment_data["deployments"][-1]
        current_deployment["services"][service_name] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }

        self._save_deployment_data()
        self.logger.info(f"Updated service {service_name} status to {status}")

    def update_test_results(self, test_type: str, results: Dict):
        """Update test results in the current deployment."""
        if not self.deployment_data["deployments"]:
            self.logger.error("No active deployment")
            return

        current_deployment = self.deployment_data["deployments"][-1]
        current_deployment["tests"][test_type] = {
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

        self._save_deployment_data()
        self.logger.info(f"Updated {test_type} test results")

    def update_health_check(self, service_name: str, status: str, details: Optional[Dict] = None):
        """Update health check results in the current deployment."""
        if not self.deployment_data["deployments"]:
            self.logger.error("No active deployment")
            return

        current_deployment = self.deployment_data["deployments"][-1]
        current_deployment["health_checks"][service_name] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }

        self._save_deployment_data()
        self.logger.info(f"Updated health check for {service_name} to {status}")

    def add_error(self, error_type: str, message: str, details: Optional[Dict] = None):
        """Add an error to the current deployment."""
        if not self.deployment_data["deployments"]:
            self.logger.error("No active deployment")
            return

        current_deployment = self.deployment_data["deployments"][-1]
        current_deployment["errors"].append({
            "type": error_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        })

        self._save_deployment_data()
        self.logger.error(f"Added error: {error_type} - {message}")

    def complete_deployment(self, status: str):
        """Mark the current deployment as complete."""
        if not self.deployment_data["deployments"]:
            self.logger.error("No active deployment")
            return

        current_deployment = self.deployment_data["deployments"][-1]
        current_deployment["status"] = status
        current_deployment["end_time"] = datetime.now().isoformat()

        self._save_deployment_data()
        self.logger.info(f"Completed deployment with status: {status}")

    def get_deployment_summary(self) -> Dict:
        """Get a summary of all deployments."""
        summary = {
            "total_deployments": len(self.deployment_data["deployments"]),
            "successful_deployments": 0,
            "failed_deployments": 0,
            "in_progress_deployments": 0,
            "recent_deployments": []
        }

        for deployment in reversed(self.deployment_data["deployments"][-5:]):
            deployment_summary = {
                "id": deployment["id"],
                "start_time": deployment["start_time"],
                "status": deployment["status"],
                "services": len(deployment["services"]),
                "tests": len(deployment["tests"]),
                "errors": len(deployment["errors"])
            }

            if "end_time" in deployment:
                deployment_summary["end_time"] = deployment["end_time"]

            summary["recent_deployments"].append(deployment_summary)

            if deployment["status"] == "completed":
                summary["successful_deployments"] += 1
            elif deployment["status"] == "failed":
                summary["failed_deployments"] += 1
            elif deployment["status"] == "in_progress":
                summary["in_progress_deployments"] += 1

        return summary

    def get_deployment_details(self, deployment_id: str) -> Optional[Dict]:
        """Get detailed information about a specific deployment."""
        for deployment in self.deployment_data["deployments"]:
            if deployment["id"] == deployment_id:
                return deployment
        return None

    def cleanup_old_deployments(self, days: int = 30):
        """Remove deployment records older than the specified number of days."""
        cutoff_date = datetime.now() - datetime.timedelta(days=days)

        self.deployment_data["deployments"] = [
            deployment for deployment in self.deployment_data["deployments"]
            if datetime.fromisoformat(deployment["start_time"]) > cutoff_date
        ]

        self._save_deployment_data()
        self.logger.info(f"Cleaned up deployments older than {days} days")

if __name__ == "__main__":
    tracker = DeploymentTracker()

    # Example usage
    deployment_id = tracker.start_deployment()

    # Update service status
    tracker.update_service_status("api", "deployed", {"version": "1.0.0"})

    # Update test results
    tracker.update_test_results("unit", {"status": "passed", "coverage": 85})

    # Update health check
    tracker.update_health_check("api", "healthy", {"response_time": 100})

    # Add error
    tracker.add_error("deployment", "Service failed to start", {"service": "api"})

    # Complete deployment
    tracker.complete_deployment("completed")

    # Get summary
    summary = tracker.get_deployment_summary()
    print(json.dumps(summary, indent=2))
