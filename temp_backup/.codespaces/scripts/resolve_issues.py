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
        logging.FileHandler('.codespaces/logs/issue_resolution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class IssueResolver:
    def __init__(self):
        self.log_dir = Path('.codespaces/logs')
        self.complete_dir = Path('.codespaces/complete')
        self.verification_dir = Path('.codespaces/verification')
        self.issues_dir = Path('.codespaces/issues')

        # Create necessary directories
        for directory in [self.log_dir, self.complete_dir, self.verification_dir, self.issues_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def load_verification_results(self) -> Dict[str, Any]:
        """Load the latest verification results"""
        verification_files = list(self.verification_dir.glob('verification_*.json'))
        if not verification_files:
            return None

        latest_file = max(verification_files, key=lambda x: x.stat().st_mtime)
        with open(latest_file, 'r') as f:
            return json.load(f)

    def resolve_issues(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve issues found in test results"""
        logging.info("Resolving issues...")

        resolution_results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'suites': {}
        }

        for suite_name, suite_results in results['suites'].items():
            if suite_results['status'] == 'complete':
                resolution_results['suites'][suite_name] = {
                    'status': 'resolved',
                    'message': 'No issues to resolve'
                }
                continue

            # Resolve issues for this suite
            suite_resolution = self._resolve_suite_issues(suite_name, suite_results)
            resolution_results['suites'][suite_name] = suite_resolution

        return resolution_results

    def _resolve_suite_issues(self, suite_name: str, suite_results: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve issues for a specific test suite"""
        if suite_results['status'] == 'error':
            return {
                'status': 'error',
                'message': suite_results['message'],
                'resolution': 'Manual intervention required'
            }

        # Check for test failures
        log_files = [Path(f) for f in suite_results['log_files']]
        if not log_files:
            return {
                'status': 'error',
                'message': 'No log files found',
                'resolution': 'Manual intervention required'
            }

        # Read latest log file
        latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
        with open(latest_log, 'r') as f:
            log_content = f.read()

        # Check for common issues
        issues = []
        resolutions = []

        if 'FAILURES' in log_content:
            issues.append('Test failures found')
            resolutions.append('Review failed tests and fix issues')

        if 'ERRORS' in log_content:
            issues.append('Test errors found')
            resolutions.append('Review error logs and fix issues')

        if 'SKIPPED' in log_content:
            issues.append('Skipped tests found')
            resolutions.append('Review skipped tests and ensure they are necessary')

        if not issues:
            return {
                'status': 'resolved',
                'message': 'No specific issues found',
                'resolution': 'Review test implementation'
            }

        return {
            'status': 'issues_found',
            'issues': issues,
            'resolutions': resolutions
        }

    def save_resolution_results(self, results: Dict[str, Any]) -> None:
        """Save resolution results to JSON file"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"issue_resolution_{timestamp}.json"

        # Save to verification directory
        with open(self.verification_dir / filename, 'w') as f:
            json.dump(results, f, indent=2)

        # If all issues are resolved, move to complete directory
        if all(suite['status'] in ['resolved', 'no_issues'] for suite in results['suites'].values()):
            with open(self.complete_dir / filename, 'w') as f:
                json.dump(results, f, indent=2)
            logging.info(f"All issues resolved, results saved to {self.complete_dir / filename}")
        else:
            logging.error(f"Some issues remain, results saved to {self.verification_dir / filename}")

    def generate_resolution_report(self, results: Dict[str, Any]) -> None:
        """Generate resolution report"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.issues_dir / f"resolution_report_{timestamp}.md"

        with open(report_file, 'w') as f:
            f.write("# Issue Resolution Report\n\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")

            # Overall status
            all_resolved = all(suite['status'] in ['resolved', 'no_issues'] for suite in results['suites'].values())
            f.write(f"## Overall Status: {'✅ Resolved' if all_resolved else '❌ Issues Remain'}\n\n")

            # Suite status
            f.write("## Test Suites\n\n")
            for suite_name, suite_results in results['suites'].items():
                f.write(f"### {suite_name} Tests\n\n")
                f.write(f"Status: {suite_results['status']}\n")
                f.write(f"Message: {suite_results['message']}\n\n")

                if suite_results.get('issues'):
                    f.write("#### Issues Found\n")
                    for issue in suite_results['issues']:
                        f.write(f"- {issue}\n")
                    f.write("\n")

                if suite_results.get('resolutions'):
                    f.write("#### Recommended Resolutions\n")
                    for resolution in suite_results['resolutions']:
                        f.write(f"- {resolution}\n")
                    f.write("\n")

            # Recommendations
            f.write("## Recommendations\n\n")
            if all_resolved:
                f.write("- All issues have been resolved\n")
                f.write("- No further action required\n")
            else:
                f.write("- Review remaining issues\n")
                f.write("- Implement recommended resolutions\n")
                f.write("- Re-run tests after fixes\n")

        logging.info(f"Generated resolution report at {report_file}")

    def run(self) -> bool:
        """Run issue resolution process"""
        # Load verification results
        results = self.load_verification_results()
        if not results:
            logging.error("No verification results found")
            return False

        # Resolve issues
        resolution_results = self.resolve_issues(results)

        # Save results
        self.save_resolution_results(resolution_results)

        # Generate report
        self.generate_resolution_report(resolution_results)

        # Return overall success
        return all(suite['status'] in ['resolved', 'no_issues'] for suite in resolution_results['suites'].values())

def main():
    resolver = IssueResolver()
    success = resolver.run()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
