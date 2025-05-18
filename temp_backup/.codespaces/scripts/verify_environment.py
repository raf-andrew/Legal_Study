#!/usr/bin/env python3

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.codespaces/logs/environment_verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class EnvironmentVerifier:
    def __init__(self):
        self.log_dir = Path('.codespaces/logs')
        self.verification_dir = Path('.codespaces/verification')
        self.complete_dir = Path('.codespaces/complete')

        # Create necessary directories
        for directory in [self.log_dir, self.verification_dir, self.complete_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def verify_php(self) -> Dict[str, Any]:
        """Verify PHP installation and version"""
        try:
            result = subprocess.run(['php', '-v'], capture_output=True, text=True)
            return {
                'status': 'success',
                'version': result.stdout.split('\n')[0],
                'message': 'PHP is installed and working'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'PHP verification failed: {str(e)}'
            }

    def verify_composer(self) -> Dict[str, Any]:
        """Verify Composer installation"""
        try:
            result = subprocess.run(['composer', '--version'], capture_output=True, text=True)
            return {
                'status': 'success',
                'version': result.stdout.split('\n')[0],
                'message': 'Composer is installed and working'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Composer verification failed: {str(e)}'
            }

    def verify_laravel(self) -> Dict[str, Any]:
        """Verify Laravel installation"""
        try:
            result = subprocess.run(['php', 'artisan', '--version'], capture_output=True, text=True)
            return {
                'status': 'success',
                'version': result.stdout.split('\n')[0],
                'message': 'Laravel is installed and working'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Laravel verification failed: {str(e)}'
            }

    def verify_environment(self) -> Dict[str, Any]:
        """Verify the entire environment"""
        logging.info("Starting environment verification...")

        results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'components': {
                'php': self.verify_php(),
                'composer': self.verify_composer(),
                'laravel': self.verify_laravel()
            }
        }

        # Save results
        self.save_results(results)

        # Check overall status
        all_success = all(comp['status'] == 'success' for comp in results['components'].values())

        if all_success:
            logging.info("Environment verification completed successfully")
            return True
        else:
            logging.error("Environment verification failed")
            return False

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save verification results"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"environment_verification_{timestamp}.json"

        # Save to verification directory
        with open(self.verification_dir / filename, 'w') as f:
            json.dump(results, f, indent=2)

        # If all components are successful, move to complete directory
        if all(comp['status'] == 'success' for comp in results['components'].values()):
            with open(self.complete_dir / filename, 'w') as f:
                json.dump(results, f, indent=2)
            logging.info(f"All components verified, results saved to {self.complete_dir / filename}")
        else:
            logging.error(f"Some components failed, results saved to {self.verification_dir / filename}")

def main():
    verifier = EnvironmentVerifier()
    success = verifier.verify_environment()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
