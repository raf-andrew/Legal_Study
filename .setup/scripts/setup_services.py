#!/usr/bin/env python3

import os
import sys
import logging
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.setup/logs/setup_services.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ServiceSetup:
    def __init__(self):
        self.system = platform.system().lower()
        self.setup_results: Dict[str, Any] = {
            'mysql': {'status': 'pending'},
            'redis': {'status': 'pending'}
        }

    def setup_mysql(self) -> bool:
        """Set up MySQL service."""
        logger.info("Setting up MySQL...")
        try:
            if self.system == 'windows':
                # Check if MySQL is installed
                try:
                    subprocess.run(['mysql', '--version'], capture_output=True, check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    logger.info("MySQL not found. Please install MySQL Server from https://dev.mysql.com/downloads/mysql/")
                    return False

                # Start MySQL service
                subprocess.run(['net', 'start', 'MySQL'], check=True)
            else:
                # For Linux/Mac
                subprocess.run(['sudo', 'service', 'mysql', 'start'], check=True)

            # Create database if it doesn't exist
            subprocess.run([
                'mysql',
                '-u', 'root',
                '-e', f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_DATABASE', 'legal_study')};"
            ], check=True)

            self.setup_results['mysql']['status'] = 'success'
            logger.info("MySQL setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"MySQL setup failed: {str(e)}")
            self.setup_results['mysql']['status'] = 'failure'
            self.setup_results['mysql']['error'] = str(e)
            return False

    def setup_redis(self) -> bool:
        """Set up Redis service."""
        logger.info("Setting up Redis...")
        try:
            if self.system == 'windows':
                # Check if Redis is installed
                try:
                    subprocess.run(['redis-cli', '--version'], capture_output=True, check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    logger.info("Redis not found. Please install Redis for Windows from https://github.com/microsoftarchive/redis/releases")
                    return False

                # Start Redis service
                subprocess.run(['net', 'start', 'Redis'], check=True)
            else:
                # For Linux/Mac
                subprocess.run(['sudo', 'service', 'redis-server', 'start'], check=True)

            self.setup_results['redis']['status'] = 'success'
            logger.info("Redis setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Redis setup failed: {str(e)}")
            self.setup_results['redis']['status'] = 'failure'
            self.setup_results['redis']['error'] = str(e)
            return False

    def setup_all(self) -> bool:
        """Set up all required services."""
        logger.info("Starting service setup...")

        mysql_success = self.setup_mysql()
        redis_success = self.setup_redis()

        return mysql_success and redis_success

def main():
    setup = ServiceSetup()
    success = setup.setup_all()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
