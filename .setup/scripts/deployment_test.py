#!/usr/bin/env python3

import os
import sys
import json
import logging
import subprocess
import platform
import time
import mysql.connector
import redis
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.setup/logs/deployment_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DeploymentTester:
    def __init__(self, component: Optional[str] = None):
        self.base_dir = Path('.')
        self.logs_dir = self.base_dir / '.setup' / 'logs'
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.test_results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'components': {},
            'overall_status': 'pending',
            'platform': platform.system(),
            'component_tested': component if component else 'all'
        }
        self.component = component

    def test_environment(self) -> bool:
        """Test the development environment setup."""
        if self.component and self.component != 'environment':
            return True

        logger.info("Testing development environment...")
        try:
            # Check Python version
            python_version = subprocess.check_output(['python', '--version']).decode().strip()
            logger.info(f"Python version: {python_version}")

            # Check required Python packages
            required_packages = [
                'flask', 'sqlalchemy', 'mysql-connector-python',
                'redis', 'pytest', 'coverage'
            ]
            pip_list = subprocess.check_output(['pip', 'list']).decode()
            missing_packages = []
            for package in required_packages:
                if package not in pip_list:
                    missing_packages.append(package)

            if missing_packages:
                raise Exception(f"Missing required packages: {', '.join(missing_packages)}")

            self.test_results['components']['environment'] = {
                'status': 'success',
                'python_version': python_version,
                'installed_packages': pip_list
            }
            return True
        except Exception as e:
            logger.error(f"Environment test failed: {str(e)}")
            self.test_results['components']['environment'] = {
                'status': 'failure',
                'error': str(e)
            }
            return False

    def test_database(self) -> bool:
        """Test database connectivity and setup."""
        if self.component and self.component != 'database':
            return True

        logger.info("Testing database setup...")
        try:
            # Test MySQL connection
            logger.info("Testing MySQL connection...")
            connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '3306')),
                user=os.getenv('DB_USERNAME', 'root'),
                password=os.getenv('DB_PASSWORD', 'secret'),
                database=os.getenv('DB_DATABASE', 'legal_study')
            )

            # Test database operations
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            logger.info(f"MySQL version: {version}")

            # Test table creation
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    test_column VARCHAR(255)
                )
            """)
            connection.commit()

            # Test data insertion
            cursor.execute("""
                INSERT INTO test_table (test_column) VALUES ('test_value')
            """)
            connection.commit()

            # Test data retrieval
            cursor.execute("SELECT * FROM test_table")
            result = cursor.fetchone()
            logger.info(f"Test data retrieved: {result}")

            # Cleanup
            cursor.execute("DROP TABLE IF EXISTS test_table")
            connection.commit()
            cursor.close()
            connection.close()

            self.test_results['components']['database'] = {
                'status': 'success',
                'message': 'MySQL connection and operations successful',
                'version': version
            }
            return True
        except Exception as e:
            logger.error(f"Database test failed: {str(e)}")
            self.test_results['components']['database'] = {
                'status': 'failure',
                'error': str(e)
            }
            return False

    def test_redis(self) -> bool:
        """Test Redis connectivity."""
        if self.component and self.component != 'redis':
            return True

        logger.info("Testing Redis setup...")
        try:
            # Test Redis connection
            logger.info("Testing Redis connection...")
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                db=0,
                decode_responses=True
            )

            # Test Redis operations
            logger.info("Testing Redis operations...")
            redis_client.set('test_key', 'test_value')
            value = redis_client.get('test_key')

            if value != 'test_value':
                raise Exception("Redis value mismatch")

            # Cleanup
            redis_client.delete('test_key')
            redis_client.close()

            self.test_results['components']['redis'] = {
                'status': 'success',
                'message': 'Redis connection and operations successful'
            }
            return True
        except Exception as e:
            logger.error(f"Redis test failed: {str(e)}")
            self.test_results['components']['redis'] = {
                'status': 'failure',
                'error': str(e)
            }
            return False

    def test_application(self) -> bool:
        """Test application setup and dependencies."""
        if self.component and self.component != 'application':
            return True

        logger.info("Testing application setup...")
        try:
            # Check if requirements are installed
            logger.info("Checking installed packages...")
            pip_list = subprocess.check_output(['pip', 'list']).decode()

            # Check if application can start
            logger.info("Testing application startup...")
            app_test = subprocess.run([
                'python',
                '.setup/main.py',
                '--test'
            ], capture_output=True, text=True)

            if app_test.returncode == 0:
                self.test_results['components']['application'] = {
                    'status': 'success',
                    'dependencies': pip_list,
                    'startup_test': 'success'
                }
                return True
            else:
                raise Exception(f"Application test failed: {app_test.stderr}")
        except Exception as e:
            logger.error(f"Application test failed: {str(e)}")
            self.test_results['components']['application'] = {
                'status': 'failure',
                'error': str(e)
            }
            return False

    def run_all_tests(self) -> bool:
        """Run all deployment tests."""
        logger.info("Starting deployment tests...")

        tests = [
            self.test_environment,
            self.test_database,
            self.test_redis,
            self.test_application
        ]

        all_passed = True
        for test in tests:
            if not test():
                all_passed = False

        self.test_results['overall_status'] = 'success' if all_passed else 'failure'

        # Save test results
        results_file = self.logs_dir / f'deployment_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)

        logger.info(f"Deployment tests completed. Results saved to {results_file}")
        return all_passed

def main():
    parser = argparse.ArgumentParser(description='Deployment Testing Tool')
    parser.add_argument('--component', type=str, choices=['environment', 'database', 'redis', 'application'],
                      help='Test specific component only')
    args = parser.parse_args()

    tester = DeploymentTester(args.component)
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
