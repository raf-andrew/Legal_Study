#!/usr/bin/env python3

import os
import sys
import json
import logging
import subprocess
import platform
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse
import mysql.connector
import redis

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.setup/logs/deployment.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DeploymentManager:
    def __init__(self, service: Optional[str] = None):
        self.base_dir = Path('.')
        self.logs_dir = self.base_dir / '.setup' / 'logs'
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.deployment_results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'overall_status': 'pending',
            'platform': platform.system(),
            'service_deployed': service if service else 'all'
        }
        self.service = service
        self.system = platform.system().lower()

    def check_service_status(self, service_name: str) -> bool:
        """Check if a service is running."""
        try:
            if service_name == 'mysql':
                if self.system == 'windows':
                    result = subprocess.run(['sc', 'query', 'MySQL'], capture_output=True, text=True)
                    return 'RUNNING' in result.stdout
                else:
                    result = subprocess.run(['systemctl', 'is-active', 'mysql'], capture_output=True, text=True)
                    return result.returncode == 0
            elif service_name == 'redis':
                if self.system == 'windows':
                    result = subprocess.run(['sc', 'query', 'Redis'], capture_output=True, text=True)
                    return 'RUNNING' in result.stdout
                else:
                    result = subprocess.run(['systemctl', 'is-active', 'redis-server'], capture_output=True, text=True)
                    return result.returncode == 0
            return False
        except Exception as e:
            logger.error(f"Error checking {service_name} status: {str(e)}")
            return False

    def start_service(self, service_name: str) -> bool:
        """Start a service."""
        try:
            if service_name == 'mysql':
                if self.system == 'windows':
                    subprocess.run(['net', 'start', 'MySQL'], check=True)
                else:
                    subprocess.run(['sudo', 'service', 'mysql', 'start'], check=True)
            elif service_name == 'redis':
                if self.system == 'windows':
                    subprocess.run(['net', 'start', 'Redis'], check=True)
                else:
                    subprocess.run(['sudo', 'service', 'redis-server', 'start'], check=True)
            return True
        except Exception as e:
            logger.error(f"Error starting {service_name}: {str(e)}")
            return False

    def deploy_mysql(self) -> bool:
        """Deploy MySQL service."""
        if self.service and self.service != 'mysql':
            return True

        logger.info("Deploying MySQL...")
        try:
            # Check if MySQL is installed
            try:
                mysql_version = subprocess.check_output(['mysql', '--version']).decode().strip()
                logger.info(f"MySQL version: {mysql_version}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("MySQL is not installed")
                return False

            # Start MySQL if not running
            if not self.check_service_status('mysql'):
                logger.info("Starting MySQL service...")
                if not self.start_service('mysql'):
                    return False

            # Wait for MySQL to be ready
            max_retries = 30
            retry_count = 0
            while retry_count < max_retries:
                try:
                    connection = mysql.connector.connect(
                        host=os.getenv('DB_HOST', 'localhost'),
                        port=int(os.getenv('DB_PORT', '3306')),
                        user=os.getenv('DB_USERNAME', 'root'),
                        password=os.getenv('DB_PASSWORD', 'secret')
                    )
                    connection.close()
                    break
                except:
                    retry_count += 1
                    time.sleep(1)
                    logger.info(f"Waiting for MySQL... ({retry_count}/{max_retries})")

            if retry_count >= max_retries:
                raise Exception("MySQL failed to start within timeout")

            # Create database and test table
            connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '3306')),
                user=os.getenv('DB_USERNAME', 'root'),
                password=os.getenv('DB_PASSWORD', 'secret')
            )
            cursor = connection.cursor()

            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('DB_DATABASE', 'legal_study')}")
            cursor.execute(f"USE {os.getenv('DB_DATABASE', 'legal_study')}")

            # Create test table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deployment_test (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    test_column VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            connection.commit()

            # Test data operations
            cursor.execute("INSERT INTO deployment_test (test_column) VALUES ('test_value')")
            connection.commit()

            cursor.execute("SELECT * FROM deployment_test")
            result = cursor.fetchone()
            logger.info(f"Test data retrieved: {result}")

            # Cleanup
            cursor.execute("DROP TABLE IF EXISTS deployment_test")
            connection.commit()
            cursor.close()
            connection.close()

            self.deployment_results['services']['mysql'] = {
                'status': 'success',
                'version': mysql_version,
                'message': 'MySQL deployed successfully'
            }
            return True
        except Exception as e:
            logger.error(f"MySQL deployment failed: {str(e)}")
            self.deployment_results['services']['mysql'] = {
                'status': 'failure',
                'error': str(e)
            }
            return False

    def deploy_redis(self) -> bool:
        """Deploy Redis service."""
        if self.service and self.service != 'redis':
            return True

        logger.info("Deploying Redis...")
        try:
            # Check if Redis is installed
            try:
                redis_version = subprocess.check_output(['redis-cli', '--version']).decode().strip()
                logger.info(f"Redis version: {redis_version}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("Redis is not installed")
                return False

            # Start Redis if not running
            if not self.check_service_status('redis'):
                logger.info("Starting Redis service...")
                if not self.start_service('redis'):
                    return False

            # Wait for Redis to be ready
            max_retries = 30
            retry_count = 0
            while retry_count < max_retries:
                try:
                    redis_client = redis.Redis(
                        host=os.getenv('REDIS_HOST', 'localhost'),
                        port=int(os.getenv('REDIS_PORT', '6379')),
                        db=0,
                        decode_responses=True
                    )
                    redis_client.ping()
                    break
                except:
                    retry_count += 1
                    time.sleep(1)
                    logger.info(f"Waiting for Redis... ({retry_count}/{max_retries})")

            if retry_count >= max_retries:
                raise Exception("Redis failed to start within timeout")

            # Test Redis operations
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                db=0,
                decode_responses=True
            )

            # Test basic operations
            redis_client.set('test_key', 'test_value')
            value = redis_client.get('test_key')

            if value != 'test_value':
                raise Exception("Redis value mismatch")

            # Test list operations
            redis_client.lpush('test_list', 'item1', 'item2', 'item3')
            list_length = redis_client.llen('test_list')

            if list_length != 3:
                raise Exception("Redis list operation failed")

            # Cleanup
            redis_client.delete('test_key')
            redis_client.delete('test_list')
            redis_client.close()

            self.deployment_results['services']['redis'] = {
                'status': 'success',
                'version': redis_version,
                'message': 'Redis deployed successfully'
            }
            return True
        except Exception as e:
            logger.error(f"Redis deployment failed: {str(e)}")
            self.deployment_results['services']['redis'] = {
                'status': 'failure',
                'error': str(e)
            }
            return False

    def deploy_all(self) -> bool:
        """Deploy all services."""
        logger.info("Starting service deployment...")

        services = [
            self.deploy_mysql,
            self.deploy_redis
        ]

        all_success = True
        for service in services:
            if not service():
                all_success = False

        self.deployment_results['overall_status'] = 'success' if all_success else 'failure'

        # Save deployment results
        results_file = self.logs_dir / f'deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(results_file, 'w') as f:
            json.dump(self.deployment_results, f, indent=2)

        logger.info(f"Deployment completed. Results saved to {results_file}")
        return all_success

def main():
    parser = argparse.ArgumentParser(description='Service Deployment Manager')
    parser.add_argument('--service', type=str, choices=['mysql', 'redis'],
                      help='Deploy specific service only')
    args = parser.parse_args()

    manager = DeploymentManager(args.service)
    success = manager.deploy_all()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
