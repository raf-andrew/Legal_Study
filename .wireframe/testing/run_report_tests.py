#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import unittest
from pathlib import Path
from datetime import datetime
import webbrowser
from test_report_suite import TestReportGeneration

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_run.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ReportTestRunner:
    """Test runner for report generation tests."""

    def __init__(self, iterations=10):
        """Initialize test runner."""
        self.iterations = iterations
        self.results_dir = Path(".wireframe/testing/results")
        self.results_dir.mkdir(exist_ok=True)

        # Initialize results
        self.results = {
            "start_time": datetime.now().isoformat(),
            "iterations": [],
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "errors": 0
            }
        }

    def run_iteration(self, iteration):
        """Run a single test iteration."""
        logger.info(f"Starting iteration {iteration}")

        # Create iteration directory
        iteration_dir = self.results_dir / f"iteration_{iteration}"
        iteration_dir.mkdir(exist_ok=True)

        # Run tests
        suite = unittest.TestLoader().loadTestsFromTestCase(TestReportGeneration)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Save iteration results
        iteration_results = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped)
        }

        # Update summary
        self.results["summary"]["total_tests"] += result.testsRun
        self.results["summary"]["passed_tests"] += (result.testsRun - len(result.failures) - len(result.errors))
        self.results["summary"]["failed_tests"] += len(result.failures)
        self.results["summary"]["errors"] += len(result.errors)

        # Add iteration results
        self.results["iterations"].append(iteration_results)

        # Generate iteration report
        self._generate_iteration_report(iteration, iteration_dir, result)

        logger.info(f"Completed iteration {iteration}")
        return iteration_results

    def _generate_iteration_report(self, iteration, iteration_dir, result):
        """Generate HTML report for an iteration."""
        report_path = iteration_dir / "report.html"

        with open(report_path, "w") as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Results - Iteration {iteration}</title>
                <style>
                    body {{ font-family: Arial; margin: 20px; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                    .summary {{ background: #f5f5f5; padding: 20px; margin: 20px 0; }}
                    .failure {{ color: red; }}
                    .error {{ color: orange; }}
                    .success {{ color: green; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Test Results - Iteration {iteration}</h1>
                    <div class="summary">
                        <h2>Summary</h2>
                        <p>Tests Run: {result.testsRun}</p>
                        <p>Failures: {len(result.failures)}</p>
                        <p>Errors: {len(result.errors)}</p>
                        <p>Skipped: {len(result.skipped)}</p>
                    </div>
                    <div class="details">
                        <h2>Test Details</h2>
            """)

            # Add failures
            if result.failures:
                f.write("<h3>Failures</h3>")
                for failure in result.failures:
                    f.write(f"<div class='failure'><p>{failure[0]}</p><pre>{failure[1]}</pre></div>")

            # Add errors
            if result.errors:
                f.write("<h3>Errors</h3>")
                for error in result.errors:
                    f.write(f"<div class='error'><p>{error[0]}</p><pre>{error[1]}</pre></div>")

            f.write("""
                    </div>
                </div>
            </body>
            </html>
            """)

        # Open report in browser
        webbrowser.open(f"file://{report_path.absolute()}")

    def run_all_iterations(self):
        """Run all test iterations."""
        logger.info(f"Starting test run with {self.iterations} iterations")

        for iteration in range(1, self.iterations + 1):
            try:
                self.run_iteration(iteration)
            except Exception as e:
                logger.error(f"Error in iteration {iteration}: {str(e)}")
                self.results["iterations"].append({
                    "iteration": iteration,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                })

        # Save final results
        self.results["end_time"] = datetime.now().isoformat()
        with open(self.results_dir / "final_results.json", "w") as f:
            json.dump(self.results, f, indent=2)

        # Generate final report
        self._generate_final_report()

        logger.info("Test run completed")

    def _generate_final_report(self):
        """Generate final HTML report."""
        report_path = self.results_dir / "final_report.html"

        with open(report_path, "w") as f:
            f.write(f"""
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
                        <p>Total Tests: {self.results['summary']['total_tests']}</p>
                        <p>Passed Tests: {self.results['summary']['passed_tests']}</p>
                        <p>Failed Tests: {self.results['summary']['failed_tests']}</p>
                        <p>Errors: {self.results['summary']['errors']}</p>
                        <p>Start Time: {self.results['start_time']}</p>
                        <p>End Time: {self.results['end_time']}</p>
                    </div>
                    <div class="iterations">
                        <h2>Iteration Details</h2>
            """)

            # Add iteration details
            for iteration in self.results["iterations"]:
                status = "success" if iteration.get("failures", 0) == 0 and iteration.get("errors", 0) == 0 else "failure"
                f.write(f"""
                        <div class="iteration {status}">
                            <h3>Iteration {iteration['iteration']}</h3>
                            <p>Tests Run: {iteration.get('tests_run', 0)}</p>
                            <p>Failures: {iteration.get('failures', 0)}</p>
                            <p>Errors: {iteration.get('errors', 0)}</p>
                            <p>Skipped: {iteration.get('skipped', 0)}</p>
                            <p>Timestamp: {iteration['timestamp']}</p>
                        </div>
                """)

            f.write("""
                    </div>
                </div>
            </body>
            </html>
            """)

        # Open final report in browser
        webbrowser.open(f"file://{report_path.absolute()}")

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Run report generation tests")
    parser.add_argument("--iterations", type=int, default=10, help="Number of test iterations")
    args = parser.parse_args()

    # Run tests
    runner = ReportTestRunner(iterations=args.iterations)
    runner.run_all_iterations()
