#!/usr/bin/env python3
"""
Comprehensive test runner for the Legal Study Platform
"""
import os
import sys
import time
import json
import pytest
import logging
import psutil
import datetime
import subprocess
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.codespaces/logs/all_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestMetrics:
    """Test execution metrics"""
    start_time: float
    end_time: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    total_duration: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float

class TestRunner:
    """Comprehensive test runner with verification"""

    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_dir = Path('.codespaces/logs')
        self.complete_dir = Path('.codespaces/complete')
        self.verification_dir = Path('.codespaces/verification')
        self.docs_dir = Path('.codespaces/docs')

        # Create necessary directories
        for directory in [self.log_dir, self.complete_dir, self.verification_dir, self.docs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def collect_system_metrics(self) -> Dict[str, float]:
        """Collect system metrics during test execution"""
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }

    def verify_services(self) -> bool:
        """Verify all services are healthy before running tests"""
        logger.info("Verifying services...")
        try:
            result = subprocess.run(
                ['python', '.codespaces/scripts/verify_services.py'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Service verification failed: {str(e)}")
            return False

    def generate_verification_report(self) -> None:
        """Generate comprehensive verification report"""
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'test_metrics': asdict(self.metrics),
            'system_metrics': self.collect_system_metrics(),
            'verification_level': os.getenv('VERIFICATION_LEVEL', 'comprehensive'),
            'test_environment': {
                'python_version': sys.version,
                'platform': sys.platform,
                'test_runner': 'pytest'
            }
        }

        report_path = self.verification_dir / f'verification_report_{self.timestamp}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Verification report generated: {report_path}")

    def generate_summary_report(self) -> None:
        """Generate human-readable summary report"""
        summary = f"""
Test Execution Summary
====================
Start Time: {datetime.datetime.fromtimestamp(self.metrics.start_time)}
End Time: {datetime.datetime.fromtimestamp(self.metrics.end_time)}
Duration: {self.metrics.total_duration:.2f} seconds

Test Results
-----------
Total Tests: {self.metrics.total_tests}
Passed: {self.metrics.passed_tests}
Failed: {self.metrics.failed_tests}
Skipped: {self.metrics.skipped_tests}
Error: {self.metrics.error_tests}

System Metrics
-------------
CPU Usage: {self.metrics.cpu_usage:.1f}%
Memory Usage: {self.metrics.memory_usage:.1f}%
Disk Usage: {self.metrics.disk_usage:.1f}%

Verification Level: {os.getenv('VERIFICATION_LEVEL', 'comprehensive')}
"""
        summary_path = self.verification_dir / f'summary_report_{self.timestamp}.txt'
        with open(summary_path, 'w') as f:
            f.write(summary)
        logger.info(f"Summary report generated: {summary_path}")

    def run_test_suite(self, suite_name: str) -> Dict[str, Any]:
        """Run a specific test suite"""
        logger.info(f"Running {suite_name} tests...")

        try:
            result = subprocess.run(
                ['php', 'artisan', 'test', f'--testsuite={suite_name}'],
                capture_output=True,
                text=True
            )

            return {
                'suite': suite_name,
                'success': result.returncode == 0,
                'output': result.stdout + result.stderr,
                'timestamp': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"{suite_name} test execution failed: {str(e)}")
            return {
                'suite': suite_name,
                'success': False,
                'error': str(e),
                'timestamp': datetime.datetime.now().isoformat()
            }

    def save_results(self, results: List[Dict[str, Any]]) -> None:
        """Save test results to JSON file"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"all_tests_{timestamp}.json"

        # Save to verification directory
        with open(self.verification_dir / filename, 'w') as f:
            json.dump(results, f, indent=2)

        # If all suites passed, move to complete directory
        if all(suite['success'] for suite in results):
            with open(self.complete_dir / filename, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"All tests passed, results saved to {self.complete_dir / filename}")
        else:
            logger.error(f"Some tests failed, results saved to {self.verification_dir / filename}")

    def generate_docs(self, results: List[Dict[str, Any]]) -> None:
        """Generate documentation from test results"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        doc_file = self.docs_dir / f"test_results_{timestamp}.md"

        with open(doc_file, 'w') as f:
            f.write("# Test Results\n\n")
            f.write(f"Generated: {datetime.datetime.now().isoformat()}\n\n")

            for suite in results:
                f.write(f"## {suite['suite']}\n\n")
                f.write(f"Status: {'✅ Passed' if suite['success'] else '❌ Failed'}\n\n")
                f.write("### Output\n```\n")
                f.write(suite.get('output', suite.get('error', 'No output')))
                f.write("\n```\n\n")

        logger.info(f"Generated documentation at {doc_file}")

    def run_all_tests(self) -> bool:
        """Run all test suites in sequence"""
        # First verify services
        if not self.verify_services():
            logger.error("Service verification failed, aborting tests")
            return False

        # Run each test suite
        test_suites = ['Feature', 'Unit', 'Integration', 'Performance', 'Security']
        results = []

        for suite in test_suites:
            result = self.run_test_suite(suite)
            results.append(result)

            if not result['success']:
                logger.error(f"{suite} tests failed")
                break

        # Save results
        self.save_results(results)

        # Generate documentation
        self.generate_docs(results)

        # Return overall success
        return all(suite['success'] for suite in results)

def main():
    """Main entry point"""
    runner = TestRunner()
    success = runner.run_all_tests()

    if success:
        logger.info("All tests completed successfully!")
        sys.exit(0)
    else:
        logger.error("Some tests failed. Check the logs for details.")
        sys.exit(1)

if __name__ == '__main__':
    main()
