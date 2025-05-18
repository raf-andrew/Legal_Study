#!/usr/bin/env python3

import unittest
import sys
import os
import json
from pathlib import Path
import coverage
import datetime
import logging
from test_runner import TestCoverageTracker

def run_coverage():
    """Run tests with coverage reporting."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('coverage_run.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

    # Start coverage
    cov = coverage.Coverage(
        branch=True,
        source=['.wireframe/testing'],
        omit=[
            '*/tests/*',
            '*/venv/*',
            '*/__pycache__/*',
            '*/coverage_run.py',
            '*/run_tests.py',
            '*/test_runner.py'
        ]
    )
    cov.start()

    # Run tests
    tracker = TestCoverageTracker()
    result = tracker.run_tests()

    # Stop coverage and generate report
    cov.stop()
    cov.save()

    # Generate reports
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_dir = Path('.wireframe/testing/coverage_reports')
    report_dir.mkdir(parents=True, exist_ok=True)

    # HTML report
    cov.html_report(directory=str(report_dir / f'html_{timestamp}'))

    # XML report
    cov.xml_report(outfile=str(report_dir / f'coverage_{timestamp}.xml'))

    # Console report
    cov.report()

    # Save coverage data
    coverage_data = {
        'timestamp': timestamp,
        'total_lines': cov.total_lines,
        'covered_lines': cov.covered_lines,
        'missing_lines': cov.missing_lines,
        'branch_coverage': cov.branch_coverage(),
        'file_coverage': {
            filename: {
                'total_lines': cov.analysis(filename)[1],
                'covered_lines': cov.analysis(filename)[2],
                'missing_lines': cov.analysis(filename)[3]
            }
            for filename in cov.get_file_coverage()
        }
    }

    with open(report_dir / f'coverage_data_{timestamp}.json', 'w') as f:
        json.dump(coverage_data, f, indent=2)

    # Log results
    logger.info(f"Coverage run completed at {timestamp}")
    logger.info(f"Total lines: {cov.total_lines}")
    logger.info(f"Covered lines: {cov.covered_lines}")
    logger.info(f"Missing lines: {cov.missing_lines}")
    logger.info(f"Branch coverage: {cov.branch_coverage():.2%}")

    return result

if __name__ == '__main__':
    sys.exit(run_coverage())
