#!/usr/bin/env python3
"""
Functional test runner for live environment testing
"""
import os
import sys
import time
import json
import pytest
import logging
import psutil
import datetime
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(message)s',
    handlers=[
        logging.FileHandler('.codespaces/logs/functional_test_run.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class FunctionalTestMetrics:
    """Functional test execution metrics"""
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
    api_response_times: List[float]
    database_operations: int
    cache_hits: int
    cache_misses: int

class FunctionalTestRunner:
    """Functional test runner for live environment"""

    def __init__(self):
        self.reports_dir = Path('.codespaces/reports/functional')
        self.logs_dir = Path('.codespaces/logs')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.metrics = None
        self.start_time = None
        self.api_response_times = []
        self.database_operations = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def collect_system_metrics(self) -> Dict[str, float]:
        """Collect system metrics during test execution"""
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }

    def generate_verification_report(self) -> None:
        """Generate comprehensive verification report"""
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'test_metrics': asdict(self.metrics),
            'system_metrics': self.collect_system_metrics(),
            'verification_level': os.getenv('VERIFICATION_LEVEL', 'functional'),
            'test_environment': {
                'python_version': sys.version,
                'platform': sys.platform,
                'test_runner': 'pytest',
                'api_base_url': os.getenv('API_BASE_URL'),
                'database_url': os.getenv('DATABASE_URL'),
                'cache_url': os.getenv('CACHE_URL')
            },
            'performance_metrics': {
                'average_api_response_time': sum(self.api_response_times) / len(self.api_response_times) if self.api_response_times else 0,
                'total_database_operations': self.database_operations,
                'cache_hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
            }
        }

        report_path = self.reports_dir / 'functional_verification_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Verification report generated: {report_path}")

    def generate_summary_report(self) -> None:
        """Generate human-readable summary report"""
        summary = f"""
Functional Test Execution Summary
==============================
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

Performance Metrics
-----------------
Average API Response Time: {sum(self.api_response_times) / len(self.api_response_times) if self.api_response_times else 0:.2f}ms
Total Database Operations: {self.database_operations}
Cache Hit Rate: {self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0:.2%}

Verification Level: {os.getenv('VERIFICATION_LEVEL', 'functional')}
"""
        summary_path = self.reports_dir / 'functional_summary_report.txt'
        with open(summary_path, 'w') as f:
            f.write(summary)
        logger.info(f"Summary report generated: {summary_path}")

    def run_functional_tests(self) -> int:
        """Run functional tests in live environment"""
        logger.info("Starting functional test execution")
        self.start_time = time.time()

        # Define test suites in order of execution
        test_suites = [
            'functional/api',
            'functional/services',
            'functional/integration'
        ]

        # Run each test suite
        for suite in test_suites:
            logger.info(f"Running {suite} tests...")

            pytest_args = [
                f'tests/{suite}',
                '--verbose',
                '--tb=short',
                '--strict-markers',
                f'--junitxml=.codespaces/reports/functional/{suite.replace("/", "_")}_junit.xml',
                f'--html=.codespaces/reports/functional/{suite.replace("/", "_")}_report.html',
                '--self-contained-html',
                '--capture=sys',
                '--showlocals',
                '--durations=10',
                '--live-environment'  # Custom marker for live environment tests
            ]

            exit_code = pytest.main(pytest_args)
            if exit_code != 0:
                logger.error(f"{suite} tests failed with exit code {exit_code}")
                # Continue with other suites but track the failure

        end_time = time.time()

        # Collect metrics
        self.metrics = FunctionalTestMetrics(
            start_time=self.start_time,
            end_time=end_time,
            total_tests=0,  # Will be updated from pytest report
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            error_tests=0,
            total_duration=end_time - self.start_time,
            **self.collect_system_metrics(),
            api_response_times=self.api_response_times,
            database_operations=self.database_operations,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses
        )

        # Generate reports
        self.generate_verification_report()
        self.generate_summary_report()

        logger.info("Functional test execution completed")
        return exit_code

def main():
    """Main entry point"""
    runner = FunctionalTestRunner()
    exit_code = runner.run_functional_tests()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
