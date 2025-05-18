#!/usr/bin/env python3

import os
import sys
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.codespaces/logs/verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class TestVerifier:
    def __init__(self):
        self.log_dir = Path('.codespaces/logs')
        self.complete_dir = Path('.codespaces/complete')
        self.verification_dir = Path('.codespaces/verification')
        self.docs_dir = Path('.codespaces/docs')

        # Create necessary directories
        for directory in [self.log_dir, self.complete_dir, self.verification_dir, self.docs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def verify_test_completion(self) -> Dict[str, Any]:
        """Verify completion status of all test suites"""
        logging.info("Verifying test completion...")

        results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'suites': {}
        }

        # Check each test suite
        test_suites = ['Feature', 'Unit', 'Integration', 'Performance', 'Security']

        for suite in test_suites:
            suite_results = self._verify_suite(suite)
            results['suites'][suite] = suite_results

        return results

    def _verify_suite(self, suite_name: str) -> Dict[str, Any]:
        """Verify completion status of a specific test suite"""
        # Check for checklist file
        checklist_path = Path(f'.test/{suite_name.lower()}_test_checklist.md')
        if not checklist_path.exists():
            return {
                'status': 'error',
                'message': f'Checklist file not found: {checklist_path}'
            }

        # Check for test logs
        log_files = list(self.log_dir.glob(f'{suite_name.lower()}_tests_*.log'))
        if not log_files:
            return {
                'status': 'error',
                'message': f'No test logs found for {suite_name}'
            }

        # Check for completed tests
        complete_files = list(self.complete_dir.glob(f'{suite_name.lower()}_tests_*.json'))

        # Read checklist
        with open(checklist_path, 'r') as f:
            checklist = f.read()

        # Count checklist items
        total_items = checklist.count('- [ ]')
        completed_items = checklist.count('- [x]')

        return {
            'status': 'complete' if completed_items == total_items else 'incomplete',
            'total_items': total_items,
            'completed_items': completed_items,
            'log_files': [str(f) for f in log_files],
            'complete_files': [str(f) for f in complete_files]
        }

    def save_verification_results(self, results: Dict[str, Any]) -> None:
        """Save verification results to JSON file"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"verification_{timestamp}.json"

        # Save to verification directory
        with open(self.verification_dir / filename, 'w') as f:
            json.dump(results, f, indent=2)

        # If all suites are complete, move to complete directory
        if all(suite['status'] == 'complete' for suite in results['suites'].values()):
            with open(self.complete_dir / filename, 'w') as f:
                json.dump(results, f, indent=2)
            logging.info(f"All suites complete, results saved to {self.complete_dir / filename}")
        else:
            logging.error(f"Some suites incomplete, results saved to {self.verification_dir / filename}")

    def generate_documentation(self, results: Dict[str, Any]) -> None:
        """Generate documentation from verification results"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        doc_file = self.docs_dir / f"verification_{timestamp}.md"

        with open(doc_file, 'w') as f:
            f.write("# Test Verification Results\n\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")

            for suite_name, suite_results in results['suites'].items():
                f.write(f"## {suite_name} Tests\n\n")
                f.write(f"Status: {suite_results['status']}\n")
                f.write(f"Completed: {suite_results['completed_items']}/{suite_results['total_items']}\n\n")

                if suite_results['status'] == 'error':
                    f.write(f"Error: {suite_results['message']}\n\n")

                if suite_results['complete_files']:
                    f.write("### Completed Test Runs\n")
                    for file in suite_results['complete_files']:
                        f.write(f"- {file}\n")
                    f.write("\n")

        logging.info(f"Generated documentation at {doc_file}")

    def run(self) -> bool:
        """Run verification and generate documentation"""
        # Verify test completion
        results = self.verify_test_completion()

        # Save results
        self.save_verification_results(results)

        # Generate documentation
        self.generate_documentation(results)

        # Return overall success
        return all(suite['status'] == 'complete' for suite in results['suites'].values())

def main():
    verifier = TestVerifier()
    success = verifier.run()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
