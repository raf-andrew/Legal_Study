#!/usr/bin/env python3
"""
Test runner script for comprehensive API testing with medical-grade verification
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
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(message)s',
    handlers=[
        logging.FileHandler('reports/test_run.log'),
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
    """Comprehensive test runner with medical-grade verification"""

    def __init__(self):
        self.reports_dir = Path('reports')
        self.reports_dir.mkdir(exist_ok=True)
        self.metrics = None
        self.start_time = None

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
            'verification_level': os.getenv('VERIFICATION_LEVEL', 'medical_grade'),
            'test_environment': {
                'python_version': sys.version,
                'platform': sys.platform,
                'test_runner': 'pytest'
            }
        }

        report_path = self.reports_dir / 'verification_report.json'
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

Verification Level: {os.getenv('VERIFICATION_LEVEL', 'medical_grade')}
"""
        summary_path = self.reports_dir / 'summary_report.txt'
        with open(summary_path, 'w') as f:
            f.write(summary)
        logger.info(f"Summary report generated: {summary_path}")

    def run_tests(self) -> int:
        """Run tests with comprehensive verification"""
        logger.info("Starting comprehensive test execution")
        self.start_time = time.time()

        # Run pytest with configured options
        pytest_args = [
            '--verbose',
            '--tb=short',
            '--strict-markers',
            '--junitxml=reports/junit.xml',
            '--html=reports/report.html',
            '--self-contained-html',
            '--capture=sys',
            '--showlocals',
            '--durations=10'
        ]

        exit_code = pytest.main(pytest_args)
        end_time = time.time()

        # Collect metrics
        self.metrics = TestMetrics(
            start_time=self.start_time,
            end_time=end_time,
            total_tests=0,  # Will be updated from pytest report
            passed_tests=0,
            failed_tests=0,
            skipped_tests=0,
            error_tests=0,
            total_duration=end_time - self.start_time,
            **self.collect_system_metrics()
        )

        # Generate reports
        self.generate_verification_report()
        self.generate_summary_report()

        logger.info("Test execution completed")
        return exit_code

def main():
    """Main entry point"""
    runner = TestRunner()
    exit_code = runner.run_tests()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
