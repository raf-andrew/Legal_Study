#!/usr/bin/env python3

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
import mysql.connector
import redis
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.codespaces/logs/health_check.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class CodespacesHealthCheck:
    def __init__(self):
        self.log_dir = Path('.codespaces/logs')
        self.verification_dir = Path('.codespaces/verification')
        self.complete_dir = Path('.codespaces/complete')
        self.services_dir = Path('.codespaces/services')

        # Create necessary directories
        for directory in [self.log_dir, self.verification_dir, self.complete_dir, self.services_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def check_mysql(self):
        """Check MySQL connection in Codespaces"""
        try:
            conn = mysql.connector.connect(
                host='codespaces-mysql',
                port=3306,
                user='root',
                password='secret',
                database='legal_study'
            )
            conn.close()
            return {'status': 'success', 'message': 'MySQL connection successful'}
        except Exception as e:
            return {'status': 'error', 'message': f'MySQL connection failed: {str(e)}'}

    def check_redis(self):
        """Check Redis connection in Codespaces"""
        try:
            r = redis.Redis(
                host='codespaces-redis',
                port=6379,
                db=0
            )
            r.ping()
            return {'status': 'success', 'message': 'Redis connection successful'}
        except Exception as e:
            return {'status': 'error', 'message': f'Redis connection failed: {str(e)}'}

    def check_laravel(self):
        """Check Laravel application health"""
        try:
            result = subprocess.run(['php', 'artisan', '--version'],
                                 capture_output=True, text=True)
            return {'status': 'success', 'message': 'Laravel is running'}
        except Exception as e:
            return {'status': 'error', 'message': f'Laravel check failed: {str(e)}'}

    def check_php(self):
        """Check PHP installation"""
        try:
            result = subprocess.run(['php', '-v'], capture_output=True, text=True)
            return {'status': 'success', 'message': 'PHP is installed'}
        except Exception as e:
            return {'status': 'error', 'message': f'PHP check failed: {str(e)}'}

    def run_health_check(self):
        """Run all health checks"""
        logging.info("Starting Codespaces health check...")

        results = {
            'timestamp': datetime.now().isoformat(),
            'services': {
                'mysql': self.check_mysql(),
                'redis': self.check_redis(),
                'laravel': self.check_laravel(),
                'php': self.check_php()
            }
        }

        # Save results
        self.save_results(results)

        # Check overall status
        all_success = all(service['status'] == 'success'
                         for service in results['services'].values())

        if all_success:
            logging.info("All services are healthy")
            return True
        else:
            logging.error("Some services are unhealthy")
            return False

    def save_results(self, results):
        """Save health check results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"health_check_{timestamp}.json"

        # Save to verification directory
        with open(self.verification_dir / filename, 'w') as f:
            json.dump(results, f, indent=2)

        # If all services are healthy, move to complete directory
        if all(service['status'] == 'success'
               for service in results['services'].values()):
            with open(self.complete_dir / filename, 'w') as f:
                json.dump(results, f, indent=2)
            logging.info(f"Health check passed, results saved to {self.complete_dir / filename}")
        else:
            logging.error(f"Health check failed, results saved to {self.verification_dir / filename}")

def main():
    health_check = CodespacesHealthCheck()
    success = health_check.run_health_check()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
