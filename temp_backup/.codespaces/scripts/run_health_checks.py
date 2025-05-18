import os
import sys
import json
import logging
import requests
import datetime
from pathlib import Path
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.codespaces/logs/health_checks.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class HealthChecker:
    def __init__(self):
        self.base_url = os.getenv('APP_URL', 'http://localhost:8000')
        self.log_dir = Path('.codespaces/logs')
        self.complete_dir = Path('.codespaces/complete')
        self.verification_dir = Path('.codespaces/verification')

        # Create necessary directories
        for directory in [self.log_dir, self.complete_dir, self.verification_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def check_health(self) -> Dict[str, Any]:
        """Run health checks and return results"""
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            }

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save health check results to JSON file"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"health_check_{timestamp}.json"

        # Save to verification directory
        with open(self.verification_dir / filename, 'w') as f:
            json.dump(results, f, indent=2)

        # If healthy, move to complete directory
        if results.get('status') == 'healthy':
            with open(self.complete_dir / filename, 'w') as f:
                json.dump(results, f, indent=2)
            logging.info(f"Health check passed, results saved to {self.complete_dir / filename}")
        else:
            logging.error(f"Health check failed, results saved to {self.verification_dir / filename}")

    def run_checks(self) -> bool:
        """Run health checks and handle results"""
        logging.info("Starting health checks...")
        results = self.check_health()
        self.save_results(results)

        if results.get('status') == 'healthy':
            logging.info("All services are healthy")
            return True
        else:
            logging.error("Health check failed")
            return False

def main():
    checker = HealthChecker()
    success = checker.run_checks()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
