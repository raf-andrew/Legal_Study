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

class Utils:
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
        """Configure logging for the utilities."""
        log_file = self.logs_dir / f"utils_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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

    def backup_data(self):
        """Backup all data."""
        self._print_status("Backing up data...", "info")

        try:
            # Create backup directory
            backup_dir = self.data_dir / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup database
            if not self._run_command([
                "docker-compose",
                "exec",
                "db",
                "pg_dump",
                "-U", "postgres",
                "-d", "legal_study",
                "-f", "/backup/db_backup.sql"
            ]):
                return False

            # Backup Redis data
            if not self._run_command([
                "docker-compose",
                "exec",
                "redis",
                "redis-cli",
                "SAVE"
            ]):
                return False

            # Copy backup files
            if not self._run_command([
                "docker",
                "cp",
                "db:/backup/db_backup.sql",
                str(backup_dir / "db_backup.sql")
            ]):
                return False

            if not self._run_command([
                "docker",
                "cp",
                "redis:/data/dump.rdb",
                str(backup_dir / "redis_backup.rdb")
            ]):
                return False

            self._print_status("Data backup completed successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup data: {e}")
            return False

    def restore_data(self, backup_dir: str):
        """Restore data from backup."""
        self._print_status("Restoring data...", "info")

        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                self._print_status(f"Backup directory not found: {backup_dir}", "error")
                return False

            # Restore database
            if not self._run_command([
                "docker",
                "cp",
                str(backup_path / "db_backup.sql"),
                "db:/backup/db_backup.sql"
            ]):
                return False

            if not self._run_command([
                "docker-compose",
                "exec",
                "db",
                "psql",
                "-U", "postgres",
                "-d", "legal_study",
                "-f", "/backup/db_backup.sql"
            ]):
                return False

            # Restore Redis data
            if not self._run_command([
                "docker",
                "cp",
                str(backup_path / "redis_backup.rdb"),
                "redis:/data/dump.rdb"
            ]):
                return False

            if not self._run_command([
                "docker-compose",
                "restart",
                "redis"
            ]):
                return False

            self._print_status("Data restore completed successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to restore data: {e}")
            return False

    def cleanup_old_data(self):
        """Clean up old data and logs."""
        self._print_status("Cleaning up old data...", "info")

        try:
            # Get retention policy from config
            retention_days = self.config.get("data_retention", {}).get("days", 30)

            # Clean up old logs
            for log_file in self.logs_dir.glob("*.log"):
                if (datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)).days > retention_days:
                    log_file.unlink()

            # Clean up old backups
            backup_dir = self.data_dir / "backups"
            if backup_dir.exists():
                for backup in backup_dir.glob("*"):
                    if (datetime.now() - datetime.fromtimestamp(backup.stat().st_mtime)).days > retention_days:
                        if backup.is_dir():
                            for file in backup.glob("*"):
                                file.unlink()
                            backup.rmdir()
                        else:
                            backup.unlink()

            self._print_status("Data cleanup completed successfully", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cleanup data: {e}")
            return False

    def check_disk_space(self):
        """Check available disk space."""
        self._print_status("Checking disk space...", "info")

        try:
            # Get disk usage
            if not self._run_command(["df", "-h"]):
                return False

            self._print_status("Disk space check completed", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to check disk space: {e}")
            return False

    def check_memory_usage(self):
        """Check memory usage."""
        self._print_status("Checking memory usage...", "info")

        try:
            # Get memory usage
            if not self._run_command(["free", "-h"]):
                return False

            self._print_status("Memory usage check completed", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to check memory usage: {e}")
            return False

    def check_network_status(self):
        """Check network status."""
        self._print_status("Checking network status...", "info")

        try:
            # Check network connectivity
            if not self._run_command(["ping", "-c", "4", "8.8.8.8"]):
                return False

            # Check DNS resolution
            if not self._run_command(["nslookup", "github.com"]):
                return False

            self._print_status("Network status check completed", "success")
            return True
        except Exception as e:
            self.logger.error(f"Failed to check network status: {e}")
            return False

    def run(self, action: str, **kwargs):
        """Run the specified utility action."""
        try:
            actions = {
                "backup": self.backup_data,
                "restore": lambda: self.restore_data(kwargs.get("backup_dir")),
                "cleanup": self.cleanup_old_data,
                "disk": self.check_disk_space,
                "memory": self.check_memory_usage,
                "network": self.check_network_status
            }

            if action not in actions:
                self._print_status(f"Invalid action: {action}", "error")
                return False

            return actions[action]()

        except Exception as e:
            self.logger.error(f"Utility action failed: {e}")
            return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python utils.py [backup|restore|cleanup|disk|memory|network] [options]")
        sys.exit(1)

    action = sys.argv[1]
    kwargs = {}

    if action == "restore" and len(sys.argv) > 2:
        kwargs["backup_dir"] = sys.argv[2]

    utils = Utils()
    success = utils.run(action, **kwargs)
    sys.exit(0 if success else 1)
