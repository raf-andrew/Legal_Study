#!/usr/bin/env python3

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
import json
import datetime
import coverage
import pytest

logger = logging.getLogger(__name__)

def setup_test_environment() -> bool:
    """Setup test environment."""
    try:
        # Create test directories
        test_dirs = [
            'tests/unit',
            'tests/integration',
            'tests/functional',
            'tests/e2e',
            'reports/coverage',
            'reports/junit',
            'reports/html'
        ]

        for directory in test_dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)

        # Install test dependencies
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements-test.txt'], check=True)

        logger.info("Test environment setup completed")
        return True

    except Exception as e:
        logger.error(f"Failed to setup test environment: {str(e)}")
        return False

def run_unit_tests(config: Dict[str, Any]) -> bool:
    """Run unit tests."""
    try:
        # Start coverage
        cov = coverage.Coverage()
        cov.start()

        # Run pytest for unit tests
        result = pytest.main([
            'tests/unit',
            '--junitxml=reports/junit/unit_tests.xml',
            '--html=reports/html/unit_tests.html',
            '-v'
        ])

        # Stop coverage and generate report
        cov.stop()
        cov.save()
        cov.html_report(directory='reports/coverage/unit')

        if result == 0:
            logger.info("Unit tests completed successfully")
            return True
        else:
            logger.error("Unit tests failed")
            return False

    except Exception as e:
        logger.error(f"Failed to run unit tests: {str(e)}")
        return False

def run_integration_tests(config: Dict[str, Any]) -> bool:
    """Run integration tests."""
    try:
        # Start coverage
        cov = coverage.Coverage()
        cov.start()

        # Run pytest for integration tests
        result = pytest.main([
            'tests/integration',
            '--junitxml=reports/junit/integration_tests.xml',
            '--html=reports/html/integration_tests.html',
            '-v'
        ])

        # Stop coverage and generate report
        cov.stop()
        cov.save()
        cov.html_report(directory='reports/coverage/integration')

        if result == 0:
            logger.info("Integration tests completed successfully")
            return True
        else:
            logger.error("Integration tests failed")
            return False

    except Exception as e:
        logger.error(f"Failed to run integration tests: {str(e)}")
        return False

def run_functional_tests(config: Dict[str, Any]) -> bool:
    """Run functional tests."""
    try:
        # Start coverage
        cov = coverage.Coverage()
        cov.start()

        # Run pytest for functional tests
        result = pytest.main([
            'tests/functional',
            '--junitxml=reports/junit/functional_tests.xml',
            '--html=reports/html/functional_tests.html',
            '-v'
        ])

        # Stop coverage and generate report
        cov.stop()
        cov.save()
        cov.html_report(directory='reports/coverage/functional')

        if result == 0:
            logger.info("Functional tests completed successfully")
            return True
        else:
            logger.error("Functional tests failed")
            return False

    except Exception as e:
        logger.error(f"Failed to run functional tests: {str(e)}")
        return False

def generate_test_report() -> bool:
    """Generate comprehensive test report."""
    try:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'reports/test_report_{timestamp}.html'

        # Collect test results
        test_results = {
            'unit': {
                'junit': 'reports/junit/unit_tests.xml',
                'coverage': 'reports/coverage/unit/index.html'
            },
            'integration': {
                'junit': 'reports/junit/integration_tests.xml',
                'coverage': 'reports/coverage/integration/index.html'
            },
            'functional': {
                'junit': 'reports/junit/functional_tests.xml',
                'coverage': 'reports/coverage/functional/index.html'
            }
        }

        # Generate HTML report
        with open(report_file, 'w') as f:
            f.write('<!DOCTYPE html>\n<html>\n<head>\n')
            f.write('<title>Test Report</title>\n')
            f.write('<style>\n')
            f.write('body { font-family: Arial, sans-serif; margin: 20px; }\n')
            f.write('h1 { color: #333; }\n')
            f.write('.section { margin: 20px 0; padding: 10px; border: 1px solid #ddd; }\n')
            f.write('</style>\n')
            f.write('</head>\n<body>\n')

            f.write('<h1>Test Report</h1>\n')
            f.write(f'<p>Generated: {timestamp}</p>\n')

            for test_type, results in test_results.items():
                f.write(f'<div class="section">\n')
                f.write(f'<h2>{test_type.title()} Tests</h2>\n')
                f.write(f'<p><a href="{results["junit"]}">JUnit Report</a></p>\n')
                f.write(f'<p><a href="{results["coverage"]}">Coverage Report</a></p>\n')
                f.write('</div>\n')

            f.write('</body>\n</html>')

        logger.info(f"Test report generated: {report_file}")
        return True

    except Exception as e:
        logger.error(f"Failed to generate test report: {str(e)}")
        return False

def run_tests(config: Dict[str, Any]) -> bool:
    """Main test execution function."""
    try:
        # Setup test environment
        if not setup_test_environment():
            return False

        success = True

        # Run unit tests if configured
        if config['testing']['run_unit_tests']:
            if not run_unit_tests(config):
                success = False

        # Run integration tests if configured
        if config['testing']['run_integration_tests']:
            if not run_integration_tests(config):
                success = False

        # Run functional tests
        if not run_functional_tests(config):
            success = False

        # Generate test report
        if not generate_test_report():
            success = False

        return success

    except Exception as e:
        logger.error(f"Failed to run tests: {str(e)}")
        return False

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test configuration
    test_config = {
        'testing': {
            'run_unit_tests': True,
            'run_integration_tests': True,
            'generate_coverage': True
        }
    }

    success = run_tests(test_config)
    sys.exit(0 if success else 1)
