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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.setup/logs/requirements.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RequirementsVerifier:
    def __init__(self):
        self.base_dir = Path('.')
        self.logs_dir = self.base_dir / '.setup' / 'logs'
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.verification_results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'requirements': {},
            'overall_status': 'pending',
            'platform': platform.system()
        }
        self.system = platform.system().lower()

    def verify_python_requirements(self) -> bool:
        """Verify Python package requirements."""
        logger.info("Verifying Python requirements...")
        try:
            # Check Python version
            python_version = subprocess.check_output(['python', '--version']).decode().strip()
            logger.info(f"Python version: {python_version}")

            # Check required packages
            required_packages = {
                'mysql-connector-python': 'mysql.connector',
                'redis': 'redis',
                'flask': 'flask',
                'sqlalchemy': 'sqlalchemy',
                'pytest': 'pytest',
                'coverage': 'coverage'
            }

            missing_packages = []
            for package, import_name in required_packages.items():
                try:
                    __import__(import_name)
                    logger.info(f"Package {package} is installed")
                except ImportError:
                    missing_packages.append(package)
                    logger.error(f"Package {package} is missing")

            if missing_packages:
                raise Exception(f"Missing required packages: {', '.join(missing_packages)}")

            self.verification_results['requirements']['python'] = {
                'status': 'success',
                'version': python_version,
                'packages': list(required_packages.keys())
            }
            return True
        except Exception as e:
            logger.error(f"Python requirements verification failed: {str(e)}")
            self.verification_results['requirements']['python'] = {
                'status': 'failure',
                'error': str(e)
            }
            return False

    def verify_mysql_requirements(self) -> bool:
        """Verify MySQL requirements."""
        logger.info("Verifying MySQL requirements...")
        try:
            # Check MySQL installation
            mysql_version = subprocess.check_output(['mysql', '--version']).decode().strip()
            logger.info(f"MySQL version: {mysql_version}")

            # Check MySQL service
            if self.system == 'windows':
                result = subprocess.run(['sc', 'query', 'MySQL'], capture_output=True, text=True)
                if 'RUNNING' not in result.stdout:
                    raise Exception("MySQL service is not running")
            else:
                result = subprocess.run(['systemctl', 'is-active', 'mysql'], capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception("MySQL service is not running")

            self.verification_results['requirements']['mysql'] = {
                'status': 'success',
                'version': mysql_version,
                'service': 'running'
            }
            return True
        except Exception as e:
            logger.error(f"MySQL requirements verification failed: {str(e)}")
            self.verification_results['requirements']['mysql'] = {
                'status': 'failure',
                'error': str(e)
            }
            return False

    def verify_redis_requirements(self) -> bool:
        """Verify Redis requirements."""
        logger.info("Verifying Redis requirements...")
        try:
            # Check Redis installation
            redis_version = subprocess.check_output(['redis-cli', '--version']).decode().strip()
            logger.info(f"Redis version: {redis_version}")

            # Check Redis service
            if self.system == 'windows':
                result = subprocess.run(['sc', 'query', 'Redis'], capture_output=True, text=True)
                if 'RUNNING' not in result.stdout:
                    raise Exception("Redis service is not running")
            else:
                result = subprocess.run(['systemctl', 'is-active', 'redis-server'], capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception("Redis service is not running")

            self.verification_results['requirements']['redis'] = {
                'status': 'success',
                'version': redis_version,
                'service': 'running'
            }
            return True
        except Exception as e:
            logger.error(f"Redis requirements verification failed: {str(e)}")
            self.verification_results['requirements']['redis'] = {
                'status': 'failure',
                'error': str(e)
            }
            return False

    def verify_all(self) -> bool:
        """Verify all requirements."""
        logger.info("Starting requirements verification...")

        verifications = [
            self.verify_python_requirements,
            self.verify_mysql_requirements,
            self.verify_redis_requirements
        ]

        all_success = True
        for verification in verifications:
            if not verification():
                all_success = False

        self.verification_results['overall_status'] = 'success' if all_success else 'failure'

        # Save verification results
        results_file = self.logs_dir / f'requirements_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(results_file, 'w') as f:
            json.dump(self.verification_results, f, indent=2)

        logger.info(f"Requirements verification completed. Results saved to {results_file}")
        return all_success

def main():
    verifier = RequirementsVerifier()
    success = verifier.verify_all()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
