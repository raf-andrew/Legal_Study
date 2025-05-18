#!/usr/bin/env python3

import os
import sys
import json
import logging
import subprocess
import datetime
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.codespaces/logs/feature_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class FeatureTestRunner:
    def __init__(self):
        self.log_dir = Path('.codespaces/logs')
        self.complete_dir = Path('.codespaces/complete')
        self.verification_dir = Path('.codespaces/verification')
        self.checklist_path = Path('.test/feature_test_checklist.md')

        # Create necessary directories
        for directory in [self.log_dir, self.complete_dir, self.verification_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def run_tests(self) -> Dict[str, Any]:
        """Run Laravel feature tests"""
        logging.info("Running feature tests...")

        try:
            # Run tests with output capture
            result = subprocess.run(
                ['php', 'artisan', 'test', '--testsuite=Feature'],
                capture_output=True,
                text=True
            )

            # Parse test results
            success = result.returncode == 0
            output = result.stdout + result.stderr

            return {
                'success': success,
                'output': output,
                'timestamp': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Test execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            }

    def save_results(self, results: Dict[str, Any]) -> None:
        """Save test results to JSON file"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"feature_tests_{timestamp}.json"

        # Save to verification directory
        with open(self.verification_dir / filename, 'w') as f:
            json.dump(results, f, indent=2)

        # If successful, move to complete directory
        if results['success']:
            with open(self.complete_dir / filename, 'w') as f:
                json.dump(results, f, indent=2)
            logging.info(f"Tests passed, results saved to {self.complete_dir / filename}")
        else:
            logging.error(f"Tests failed, results saved to {self.verification_dir / filename}")

    def update_checklist(self, results: Dict[str, Any]) -> None:
        """Update checklist with test results"""
        if not results['success']:
            return

        # Read current checklist
        with open(self.checklist_path, 'r') as f:
            checklist = f.read()

        # Update checklist items
        for line in checklist.split('\n'):
            if line.startswith('- [ ]'):
                # Extract test name from line
                test_name = line[6:].strip()

                # Check if test passed
                if test_name in results['output']:
                    # Replace unchecked with checked
                    checklist = checklist.replace(line, f"- [x] {test_name}")

        # Write updated checklist
        with open(self.checklist_path, 'w') as f:
            f.write(checklist)

        logging.info("Updated checklist with test results")

    def run(self) -> bool:
        """Run feature tests and handle results"""
        # Run tests
        results = self.run_tests()

        # Save results
        self.save_results(results)

        # Update checklist if tests passed
        if results['success']:
            self.update_checklist(results)

        return results['success']

def main():
    runner = FeatureTestRunner()
    success = runner.run()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
