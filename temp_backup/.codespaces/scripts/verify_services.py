#!/usr/bin/env python3

import os
import sys
import json
import logging
import requests
import mysql.connector
import redis
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.codespaces/logs/service_verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ServiceVerifier:
    def __init__(self):
        self.config_path = Path('.codespaces/services')
        self.log_dir = Path('.codespaces/logs')
        self.complete_dir = Path('.codespaces/complete')
        self.verification_dir = Path('.codespaces/verification')

        # Create necessary directories
        for directory in [self.log_dir, self.complete_dir, self.verification_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Load service configurations
        self.services = self._load_service_configs()

    def _load_service_configs(self) -> Dict[str, Any]:
        """Load service configurations from JSON files"""
        configs = {}
        for config_file in self.config_path.glob('*.json'):
            with open(config_file, 'r') as f:
                configs[config_file.stem] = json.load(f)
        return configs

    def verify_database(self) -> Dict[str, Any]:
        """Verify database connection"""
        try:
            config = self.services['database']
            conn = mysql.connector.connect(
                host=config['host'],
                port=config['port'],
                user=config['username'],
                password=config['password'],
                database=config['database']
            )
            conn.close()
            return {'status': 'healthy', 'message': 'Database connection successful'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Database connection failed: {str(e)}'}

    def verify_redis(self) -> Dict[str, Any]:
        """Verify Redis connection"""
        try:
            config = self.services['redis']
            r = redis.Redis(
                host=config['host'],
                port=config['port'],
                password=config['password']
            )
            r.ping()
            return {'status': 'healthy', 'message': 'Redis connection successful'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Redis connection failed: {str(e)}'}

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save verification results to JSON file"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"service_verification_{timestamp}.json"

        # Save to verification directory
        with open(self.verification_dir / filename, 'w') as f:
            json.dump(results, f, indent=2)

        # If all services are healthy, move to complete directory
        if all(service['status'] == 'healthy' for service in results['services'].values()):
            with open(self.complete_dir / filename, 'w') as f:
                json.dump(results, f, indent=2)
            logging.info(f"All services healthy, results saved to {self.complete_dir / filename}")
        else:
            logging.error(f"Some services unhealthy, results saved to {self.verification_dir / filename}")

    def verify_services(self) -> bool:
        """Verify all services and return overall status"""
        logging.info("Starting service verification...")

        results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'services': {
                'database': self.verify_database(),
                'redis': self.verify_redis()
            }
        }

        self.save_results(results)

        # Check overall status
        all_healthy = all(service['status'] == 'healthy' for service in results['services'].values())

        if all_healthy:
            logging.info("All services are healthy")
            return True
        else:
            logging.error("Some services are unhealthy")
            return False

def main():
    verifier = ServiceVerifier()
    success = verifier.verify_services()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
