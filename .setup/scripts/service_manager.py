#!/usr/bin/env python3

import os
import sys
import json
import logging
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.setup/logs/service_manager.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self, service: Optional[str] = None):
        self.base_dir = Path('.')
        self.logs_dir = self.base_dir / '.setup' / 'logs'
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.service = service
        self.system = platform.system().lower()
        self.is_codespaces = os.getenv('CODESPACES') == 'true'
        self.management_results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'overall_status': 'pending',
            'platform': self.system,
            'is_codespaces': self.is_codespaces,
            'service_managed': service if service else 'all'
        }

    def get_service_log_path(self, service: str) -> Path:
        """Get the log file path for a service."""
        return self.logs_dir / f'{service}_service.log'

    def setup_service_logging(self, service: str) -> None:
        """Setup logging for a specific service."""
        log_file = self.get_service_log_path(service)
        service_logger = logging.getLogger(f'service.{service}')
        service_logger.setLevel(logging.INFO)

        # Remove existing handlers
        for handler in service_logger.handlers[:]:
            service_logger.removeHandler(handler)

        # Add file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        service_logger.addHandler(file_handler)

        # Add stream handler
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        service_logger.addHandler(stream_handler)

    def check_service_status(self, service: str) -> bool:
        """Check if a service is running."""
        service_logger = logging.getLogger(f'service.{service}')
        try:
            if service == 'mysql':
                if self.is_codespaces:
                    service_logger.info("Checking MySQL service status in Codespaces...")
                    result = subprocess.run(['sudo', 'service', 'mysql', 'status'], capture_output=True, text=True)
                    is_running = 'active (running)' in result.stdout.lower()
                    service_logger.info(f"MySQL service status: {'Running' if is_running else 'Stopped'}")
                    return is_running
                elif self.system == 'windows':
                    service_logger.info("Checking MySQL service status on Windows...")
                    result = subprocess.run(['sc', 'query', 'MySQL'], capture_output=True, text=True)
                    is_running = 'RUNNING' in result.stdout
                    service_logger.info(f"MySQL service status: {'Running' if is_running else 'Stopped'}")
                    return is_running
                else:
                    service_logger.info("Checking MySQL service status on Linux...")
                    result = subprocess.run(['systemctl', 'is-active', 'mysql'], capture_output=True, text=True)
                    is_running = result.returncode == 0
                    service_logger.info(f"MySQL service status: {'Running' if is_running else 'Stopped'}")
                    return is_running
            elif service == 'redis':
                if self.is_codespaces:
                    service_logger.info("Checking Redis service status in Codespaces...")
                    result = subprocess.run(['sudo', 'service', 'redis-server', 'status'], capture_output=True, text=True)
                    is_running = 'active (running)' in result.stdout.lower()
                    service_logger.info(f"Redis service status: {'Running' if is_running else 'Stopped'}")
                    return is_running
                elif self.system == 'windows':
                    service_logger.info("Checking Redis service status on Windows...")
                    result = subprocess.run(['sc', 'query', 'Redis'], capture_output=True, text=True)
                    is_running = 'RUNNING' in result.stdout
                    service_logger.info(f"Redis service status: {'Running' if is_running else 'Stopped'}")
                    return is_running
                else:
                    service_logger.info("Checking Redis service status on Linux...")
                    result = subprocess.run(['systemctl', 'is-active', 'redis-server'], capture_output=True, text=True)
                    is_running = result.returncode == 0
                    service_logger.info(f"Redis service status: {'Running' if is_running else 'Stopped'}")
                    return is_running
            return False
        except Exception as e:
            service_logger.error(f"Error checking {service} status: {str(e)}")
            return False

    def start_service(self, service: str) -> bool:
        """Start a service."""
        service_logger = logging.getLogger(f'service.{service}')
        try:
            if service == 'mysql':
                if self.is_codespaces:
                    service_logger.info("Starting MySQL service in Codespaces...")
                    subprocess.run(['sudo', 'service', 'mysql', 'start'], check=True)
                    service_logger.info("MySQL service started successfully")
                elif self.system == 'windows':
                    service_logger.info("Starting MySQL service on Windows...")
                    subprocess.run(['net', 'start', 'MySQL'], check=True)
                    service_logger.info("MySQL service started successfully")
                else:
                    service_logger.info("Starting MySQL service on Linux...")
                    subprocess.run(['sudo', 'service', 'mysql', 'start'], check=True)
                    service_logger.info("MySQL service started successfully")
            elif service == 'redis':
                if self.is_codespaces:
                    service_logger.info("Starting Redis service in Codespaces...")
                    subprocess.run(['sudo', 'service', 'redis-server', 'start'], check=True)
                    service_logger.info("Redis service started successfully")
                elif self.system == 'windows':
                    service_logger.info("Starting Redis service on Windows...")
                    subprocess.run(['net', 'start', 'Redis'], check=True)
                    service_logger.info("Redis service started successfully")
                else:
                    service_logger.info("Starting Redis service on Linux...")
                    subprocess.run(['sudo', 'service', 'redis-server', 'start'], check=True)
                    service_logger.info("Redis service started successfully")
            return True
        except Exception as e:
            service_logger.error(f"Error starting {service}: {str(e)}")
            return False

    def stop_service(self, service: str) -> bool:
        """Stop a service."""
        service_logger = logging.getLogger(f'service.{service}')
        try:
            if service == 'mysql':
                if self.is_codespaces:
                    service_logger.info("Stopping MySQL service in Codespaces...")
                    subprocess.run(['sudo', 'service', 'mysql', 'stop'], check=True)
                    service_logger.info("MySQL service stopped successfully")
                elif self.system == 'windows':
                    service_logger.info("Stopping MySQL service on Windows...")
                    subprocess.run(['net', 'stop', 'MySQL'], check=True)
                    service_logger.info("MySQL service stopped successfully")
                else:
                    service_logger.info("Stopping MySQL service on Linux...")
                    subprocess.run(['sudo', 'service', 'mysql', 'stop'], check=True)
                    service_logger.info("MySQL service stopped successfully")
            elif service == 'redis':
                if self.is_codespaces:
                    service_logger.info("Stopping Redis service in Codespaces...")
                    subprocess.run(['sudo', 'service', 'redis-server', 'stop'], check=True)
                    service_logger.info("Redis service stopped successfully")
                elif self.system == 'windows':
                    service_logger.info("Stopping Redis service on Windows...")
                    subprocess.run(['net', 'stop', 'Redis'], check=True)
                    service_logger.info("Redis service stopped successfully")
                else:
                    service_logger.info("Stopping Redis service on Linux...")
                    subprocess.run(['sudo', 'service', 'redis-server', 'stop'], check=True)
                    service_logger.info("Redis service stopped successfully")
            return True
        except Exception as e:
            service_logger.error(f"Error stopping {service}: {str(e)}")
            return False

    def restart_service(self, service: str) -> bool:
        """Restart a service."""
        service_logger = logging.getLogger(f'service.{service}')
        try:
            service_logger.info(f"Restarting {service} service...")
            if self.stop_service(service):
                time.sleep(2)  # Wait for service to stop
                return self.start_service(service)
            return False
        except Exception as e:
            service_logger.error(f"Error restarting {service}: {str(e)}")
            return False

    def verify_service(self, service: str) -> bool:
        """Verify a service is working correctly."""
        service_logger = logging.getLogger(f'service.{service}')
        try:
            if service == 'mysql':
                service_logger.info("Verifying MySQL service...")
                # Check if MySQL is installed
                try:
                    mysql_version = subprocess.check_output(['mysql', '--version']).decode().strip()
                    service_logger.info(f"MySQL version: {mysql_version}")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    service_logger.error("MySQL is not installed")
                    return False

                # Check MySQL service status
                if not self.check_service_status('mysql'):
                    service_logger.error("MySQL service is not running")
                    return False

                # Test MySQL connection
                try:
                    import mysql.connector
                    connection = mysql.connector.connect(
                        host=os.getenv('DB_HOST', 'localhost'),
                        port=int(os.getenv('DB_PORT', '3306')),
                        user=os.getenv('DB_USERNAME', 'root'),
                        password=os.getenv('DB_PASSWORD', 'secret')
                    )
                    connection.close()
                    service_logger.info("MySQL connection test successful")
                except Exception as e:
                    service_logger.error(f"MySQL connection test failed: {str(e)}")
                    return False

            elif service == 'redis':
                service_logger.info("Verifying Redis service...")
                # Check if Redis is installed
                try:
                    redis_version = subprocess.check_output(['redis-cli', '--version']).decode().strip()
                    service_logger.info(f"Redis version: {redis_version}")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    service_logger.error("Redis is not installed")
                    return False

                # Check Redis service status
                if not self.check_service_status('redis'):
                    service_logger.error("Redis service is not running")
                    return False

                # Test Redis connection
                try:
                    import redis
                    redis_client = redis.Redis(
                        host=os.getenv('REDIS_HOST', 'localhost'),
                        port=int(os.getenv('REDIS_PORT', '6379')),
                        db=0,
                        decode_responses=True
                    )
                    redis_client.ping()
                    redis_client.close()
                    service_logger.info("Redis connection test successful")
                except Exception as e:
                    service_logger.error(f"Redis connection test failed: {str(e)}")
                    return False

            return True
        except Exception as e:
            service_logger.error(f"Error verifying {service}: {str(e)}")
            return False

    def manage_service(self, service: str, action: str) -> bool:
        """Manage a specific service."""
        self.setup_service_logging(service)
        service_logger = logging.getLogger(f'service.{service}')

        service_logger.info(f"Managing {service} service: {action}")

        if action == 'start':
            if not self.check_service_status(service):
                return self.start_service(service)
            return True
        elif action == 'stop':
            if self.check_service_status(service):
                return self.stop_service(service)
            return True
        elif action == 'restart':
            return self.restart_service(service)
        elif action == 'verify':
            return self.verify_service(service)
        else:
            service_logger.error(f"Unknown action: {action}")
            return False

    def manage_all_services(self, action: str) -> bool:
        """Manage all services."""
        services = ['mysql', 'redis']
        all_success = True

        for service in services:
            if not self.manage_service(service, action):
                all_success = False

        return all_success

def main():
    parser = argparse.ArgumentParser(description='Service Manager')
    parser.add_argument('--service', type=str, choices=['mysql', 'redis'],
                      help='Manage specific service only')
    parser.add_argument('--action', type=str, choices=['start', 'stop', 'restart', 'verify'],
                      required=True, help='Action to perform')
    args = parser.parse_args()

    manager = ServiceManager(args.service)

    if args.service:
        success = manager.manage_service(args.service, args.action)
    else:
        success = manager.manage_all_services(args.action)

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
