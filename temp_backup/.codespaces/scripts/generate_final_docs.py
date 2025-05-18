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
        logging.FileHandler('.codespaces/logs/docs_generation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class DocumentationGenerator:
    def __init__(self):
        self.log_dir = Path('.codespaces/logs')
        self.complete_dir = Path('.codespaces/complete')
        self.verification_dir = Path('.codespaces/verification')
        self.docs_dir = Path('.codespaces/docs')

        # Create necessary directories
        for directory in [self.log_dir, self.complete_dir, self.verification_dir, self.docs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def load_verification_results(self) -> Dict[str, Any]:
        """Load the latest verification results"""
        verification_files = list(self.verification_dir.glob('verification_*.json'))
        if not verification_files:
            return None

        latest_file = max(verification_files, key=lambda x: x.stat().st_mtime)
        with open(latest_file, 'r') as f:
            return json.load(f)

    def generate_main_documentation(self, results: Dict[str, Any]) -> None:
        """Generate main documentation file"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        doc_file = self.docs_dir / f"test_documentation_{timestamp}.md"

        with open(doc_file, 'w') as f:
            f.write("# Test Documentation\n\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")

            # Overall status
            all_complete = all(suite['status'] == 'complete' for suite in results['suites'].values())
            f.write(f"## Overall Status: {'✅ Complete' if all_complete else '❌ Incomplete'}\n\n")

            # Test suites
            f.write("## Test Suites\n\n")
            for suite_name, suite_results in results['suites'].items():
                f.write(f"### {suite_name} Tests\n\n")
                f.write(f"Status: {suite_results['status']}\n")
                f.write(f"Progress: {suite_results['completed_items']}/{suite_results['total_items']}\n\n")

                if suite_results['complete_files']:
                    f.write("#### Completed Test Runs\n")
                    for file in suite_results['complete_files']:
                        f.write(f"- {file}\n")
                    f.write("\n")

            # Recommendations
            f.write("## Recommendations\n\n")
            if all_complete:
                f.write("- All test suites are complete\n")
                f.write("- No further action required\n")
            else:
                f.write("- Review incomplete test suites\n")
                f.write("- Address any failed tests\n")
                f.write("- Re-run tests after fixes\n")

        logging.info(f"Generated main documentation at {doc_file}")

    def generate_suite_documentation(self, results: Dict[str, Any]) -> None:
        """Generate documentation for each test suite"""
        for suite_name, suite_results in results['suites'].items():
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            doc_file = self.docs_dir / f"{suite_name.lower()}_tests_{timestamp}.md"

            with open(doc_file, 'w') as f:
                f.write(f"# {suite_name} Tests Documentation\n\n")
                f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")

                f.write(f"## Status: {suite_results['status']}\n\n")
                f.write(f"Progress: {suite_results['completed_items']}/{suite_results['total_items']}\n\n")

                if suite_results['status'] == 'error':
                    f.write(f"Error: {suite_results['message']}\n\n")

                if suite_results['complete_files']:
                    f.write("## Completed Test Runs\n")
                    for file in suite_results['complete_files']:
                        f.write(f"- {file}\n")
                    f.write("\n")

                # Recommendations
                f.write("## Recommendations\n\n")
                if suite_results['status'] == 'complete':
                    f.write("- All tests are complete\n")
                    f.write("- No further action required\n")
                else:
                    f.write("- Review incomplete tests\n")
                    f.write("- Address any failed tests\n")
                    f.write("- Re-run tests after fixes\n")

            logging.info(f"Generated {suite_name} documentation at {doc_file}")

    def generate_summary(self, results: Dict[str, Any]) -> None:
        """Generate summary report"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = self.docs_dir / f"test_summary_{timestamp}.json"

        summary = {
            'timestamp': datetime.datetime.now().isoformat(),
            'overall_status': 'complete' if all(suite['status'] == 'complete' for suite in results['suites'].values()) else 'incomplete',
            'suites': {
                suite_name: {
                    'status': suite_results['status'],
                    'progress': f"{suite_results['completed_items']}/{suite_results['total_items']}"
                }
                for suite_name, suite_results in results['suites'].items()
            }
        }

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logging.info(f"Generated summary report at {summary_file}")

    def run(self) -> None:
        """Generate all documentation"""
        # Load verification results
        results = self.load_verification_results()
        if not results:
            logging.error("No verification results found")
            return

        # Generate documentation
        self.generate_main_documentation(results)
        self.generate_suite_documentation(results)
        self.generate_summary(results)

        logging.info("Documentation generation completed")

def main():
    generator = DocumentationGenerator()
    generator.run()

if __name__ == '__main__':
    main()
