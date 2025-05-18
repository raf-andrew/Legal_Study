#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import unittest
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import shutil
import tempfile
import webbrowser
import argparse

# Add tests directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'tests'))
from test_wireframe_refinement import TestWireframeRefinement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_runner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def flush_reports():
    """Clear all test results and reports."""
    results_dir = Path(".wireframe/testing/results")
    if results_dir.exists():
        for file in results_dir.glob("*"):
            if file.is_file():
                file.unlink()
        logger.info("All test reports cleared")
    else:
        logger.info("No test reports to clear")

def run_tests(iterations=1, flush=False):
    """Run the test suite for the specified number of iterations."""
    if flush:
        flush_reports()

    start_time = datetime.now()
    total_tests = 0
    total_failures = 0
    total_errors = 0

    # Create results directory if it doesn't exist
    results_dir = Path(".wireframe/testing/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Run tests for specified number of iterations
    for i in range(iterations):
        logger.info(f"Starting iteration {i + 1}")

        # Create test suite
        suite = unittest.TestSuite()
        suite.addTest(TestWireframeRefinement('test_initialization'))
        suite.addTest(TestWireframeRefinement('test_version_tracking'))
        suite.addTest(TestWireframeRefinement('test_improvement_tracking'))
        suite.addTest(TestWireframeRefinement('test_refinement_loop'))
        suite.addTest(TestWireframeRefinement('test_report_generation'))
        suite.addTest(TestWireframeRefinement('test_screenshot_capture'))

        # Run tests
        runner = unittest.TextTestRunner()
        result = runner.run(suite)

        # Update totals
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)

        logger.info(f"Completed iteration {i + 1}")

    end_time = datetime.now()

    # Generate final report
    generate_final_report(start_time, end_time, total_tests, total_failures, total_errors)

def generate_final_report(start_time, end_time, total_tests, total_failures, total_errors):
    """Generate an HTML report of the test results."""
    report_path = Path(".wireframe/testing/results/final_report.html")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Final Test Results</title>
        <style>
            body {{ font-family: Arial; margin: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .summary {{ background: #f5f5f5; padding: 20px; margin: 20px 0; }}
            .iteration {{ margin: 20px 0; padding: 10px; border: 1px solid #ccc; }}
            .success {{ color: green; }}
            .failure {{ color: red; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Final Test Results</h1>
            <div class="summary">
                <h2>Overall Summary</h2>
                <p>Total Tests: {total_tests}</p>
                <p>Passed Tests: {total_tests - total_failures - total_errors}</p>
                <p>Failed Tests: {total_failures}</p>
                <p>Errors: {total_errors}</p>
                <p>Start Time: {start_time}</p>
                <p>End Time: {end_time}</p>
            </div>
        </div>
    </body>
    </html>
    """

    report_path.write_text(html_content)
    logger.info(f"Final report generated at {report_path}")

def main():
    parser = argparse.ArgumentParser(description='Run wireframe refinement tests')
    parser.add_argument('--iterations', type=int, default=1,
                      help='Number of test iterations to run')
    parser.add_argument('--flush', action='store_true',
                      help='Clear all test results before running')
    args = parser.parse_args()

    logger.info(f"Starting test run with {args.iterations} iterations")
    run_tests(args.iterations, args.flush)
    logger.info("Test run completed")

if __name__ == '__main__':
    main()
