#!/usr/bin/env python3

import os
import sys
import json
import logging
import datetime
import subprocess
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('compliance_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ComplianceTestRunner:
    def __init__(self):
        self.results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }

        # Define test categories and their corresponding scripts
        self.test_categories = {
            'security': 'security_checks.py',
            'availability': 'availability_checks.py',
            'processing': 'processing_checks.py',
            'confidentiality': 'confidentiality_checks.py',
            'privacy': 'privacy_checks.py'
        }

    def run_test_script(self, category: str, script: str) -> Dict[str, Any]:
        """Run a specific test script and return its results."""
        try:
            script_path = Path(__file__).parent / category / script
            if not script_path.exists():
                return {
                    'status': 'failed',
                    'details': {'error': f'Script not found: {script_path}'}
                }

            # Run the script and capture output
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                try:
                    # Try to parse JSON output
                    output = json.loads(result.stdout)
                    return {
                        'status': 'passed',
                        'details': output
                    }
                except json.JSONDecodeError:
                    # If not JSON, return the raw output
                    return {
                        'status': 'passed',
                        'details': {'output': result.stdout}
                    }
            else:
                return {
                    'status': 'failed',
                    'details': {
                        'error': result.stderr,
                        'return_code': result.returncode
                    }
                }
        except Exception as e:
            return {
                'status': 'failed',
                'details': {'error': str(e)}
            }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all compliance tests."""
        for category, script in self.test_categories.items():
            logger.info(f"Running {category} tests...")
            result = self.run_test_script(category, script)
            self.results['tests'][category] = result

            # Update summary
            self.results['summary']['total'] += 1
            if result['status'] == 'passed':
                self.results['summary']['passed'] += 1
            elif result['status'] == 'failed':
                self.results['summary']['failed'] += 1
            else:
                self.results['summary']['warnings'] += 1

        return self.results

    def save_results(self, output_path: str):
        """Save test results to a JSON file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(self.results, f, indent=2)
            logger.info(f"Results saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    def generate_report(self, output_path: str):
        """Generate a human-readable report."""
        try:
            with open(output_path, 'w') as f:
                f.write("# Compliance Test Report\n\n")
                f.write(f"Generated: {self.results['timestamp']}\n\n")

                f.write("## Summary\n\n")
                f.write(f"- Total Tests: {self.results['summary']['total']}\n")
                f.write(f"- Passed: {self.results['summary']['passed']}\n")
                f.write(f"- Failed: {self.results['summary']['failed']}\n")
                f.write(f"- Warnings: {self.results['summary']['warnings']}\n\n")

                f.write("## Detailed Results\n\n")
                for category, result in self.results['tests'].items():
                    f.write(f"### {category.title()}\n\n")
                    f.write(f"Status: {result['status']}\n\n")
                    f.write("Details:\n")
                    f.write("```json\n")
                    f.write(json.dumps(result['details'], indent=2))
                    f.write("\n```\n\n")

            logger.info(f"Report generated at {output_path}")
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")

def main():
    runner = ComplianceTestRunner()
    results = runner.run_all_tests()

    # Create reports directory
    reports_dir = Path(__file__).parent.parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    # Save results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = reports_dir / f'compliance_results_{timestamp}.json'
    runner.save_results(str(results_file))

    # Generate report
    report_file = reports_dir / f'compliance_report_{timestamp}.md'
    runner.generate_report(str(report_file))

    # Print summary
    print("\nCompliance Test Summary:")
    print(f"Total Tests: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Warnings: {results['summary']['warnings']}")
    print(f"\nDetailed report available at: {report_file}")

if __name__ == '__main__':
    main()
