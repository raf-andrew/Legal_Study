#!/usr/bin/env python3
"""
CI/CD Test Runner

This script runs tests in a CI/CD environment with additional checks and reporting.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any
import json
import yaml
from datetime import datetime
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/ci_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CITestRunner:
    def __init__(self):
        self.config = self._load_config()
        self.results = {
            'tests': {},
            'code_quality': {},
            'security': {},
            'coverage': {}
        }
        self.error_count = 0

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = Path('.config/environment/development/config.yaml')
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def run_tests(self) -> None:
        """Run all test suites."""
        try:
            logger.info("Running test suites...")
            subprocess.run(
                ['python', '.scripts/run_tests.py'],
                check=True
            )
            self.results['tests']['status'] = 'success'
        except subprocess.CalledProcessError as e:
            logger.error(f"Tests failed: {e}")
            self.results['tests']['status'] = 'failed'
            self.error_count += 1

    def run_code_quality_checks(self) -> None:
        """Run code quality checks."""
        try:
            logger.info("Running code quality checks...")
            # Run black
            subprocess.run(['black', '--check', '.'], check=True)
            # Run flake8
            subprocess.run(['flake8', '.'], check=True)
            # Run mypy
            subprocess.run(['mypy', '.'], check=True)
            self.results['code_quality']['status'] = 'success'
        except subprocess.CalledProcessError as e:
            logger.error(f"Code quality checks failed: {e}")
            self.results['code_quality']['status'] = 'failed'
            self.error_count += 1

    def run_security_checks(self) -> None:
        """Run security checks."""
        try:
            logger.info("Running security checks...")
            # Run bandit
            subprocess.run(['bandit', '-r', '.'], check=True)
            # Run safety
            subprocess.run(['safety', 'check'], check=True)
            self.results['security']['status'] = 'success'
        except subprocess.CalledProcessError as e:
            logger.error(f"Security checks failed: {e}")
            self.results['security']['status'] = 'failed'
            self.error_count += 1

    def run_coverage_checks(self) -> None:
        """Run coverage checks."""
        try:
            logger.info("Running coverage checks...")
            subprocess.run(
                ['pytest', '--cov=.', '--cov-report=xml'],
                check=True
            )
            self.results['coverage']['status'] = 'success'
        except subprocess.CalledProcessError as e:
            logger.error(f"Coverage checks failed: {e}")
            self.results['coverage']['status'] = 'failed'
            self.error_count += 1

    def generate_report(self) -> None:
        """Generate CI/CD test report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_errors': self.error_count,
            'results': self.results
        }

        # Save JSON report
        report_path = Path('.complete') / f"ci_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Save Markdown report
        md_report_path = Path('.complete') / f"ci_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md_report_path, 'w') as f:
            f.write("# CI/CD Test Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total Errors: {self.error_count}\n\n")
            
            for check_type, result in self.results.items():
                f.write(f"## {check_type.title()} Checks\n\n")
                f.write(f"Status: {result['status']}\n\n")

    def run_all_checks(self) -> None:
        """Run all CI/CD checks."""
        try:
            self.run_tests()
            self.run_code_quality_checks()
            self.run_security_checks()
            self.run_coverage_checks()
        except Exception as e:
            logger.error(f"CI/CD checks failed: {e}")
            self.error_count += 1
        finally:
            self.generate_report()

if __name__ == "__main__":
    runner = CITestRunner()
    runner.run_all_checks()
    
    # Print summary
    print("\nCI/CD Test Summary:")
    print(f"Total Errors: {runner.error_count}")
    print(f"Reports generated in .complete/ directory")
    
    # Exit with appropriate status code
    sys.exit(1 if runner.error_count > 0 else 0) 