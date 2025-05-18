#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import unittest
import argparse
from pathlib import Path
from datetime import datetime
from test_suite import TestWireframeRefinement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.wireframe/testing/logs/test_run.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class TestRunner:
    def __init__(self, iterations=10):
        self.iterations = iterations
        self.results_dir = Path('.wireframe/testing/results')
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.start_time = datetime.now()

    def run_iteration(self, iteration_number):
        """Run a single iteration of tests."""
        logging.info(f"Starting iteration {iteration_number}")

        # Create a test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(TestWireframeRefinement)

        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Generate iteration report
        self._generate_iteration_report(iteration_number, result)

        return result

    def _generate_iteration_report(self, iteration_number, result):
        """Generate a report for a single iteration."""
        report = {
            "iteration": iteration_number,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": result.testsRun,
                "passed": result.testsRun - len(result.failures) - len(result.errors),
                "failures": len(result.failures),
                "errors": len(result.errors)
            },
            "failures": [
                {
                    "test": str(failure[0]),
                    "message": str(failure[1])
                }
                for failure in result.failures
            ],
            "errors": [
                {
                    "test": str(error[0]),
                    "message": str(error[1])
                }
                for error in result.errors
            ]
        }

        # Save report as JSON
        report_path = self.results_dir / f"iteration_{iteration_number:02d}_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Generate HTML report
        self._generate_html_report(iteration_number, report)

    def _generate_html_report(self, iteration_number, report):
        """Generate an HTML report for the iteration."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Iteration {iteration_number} Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .failure, .error {{
            background-color: #fff3f3;
            padding: 15px;
            border-left: 4px solid #dc3545;
            margin-bottom: 10px;
        }}
        .success {{
            color: #28a745;
        }}
        .failure-header, .error-header {{
            color: #dc3545;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1>Test Iteration {iteration_number} Report</h1>
    <p>Generated at: {report['timestamp']}</p>

    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: {report['summary']['total_tests']}</p>
        <p class="success">Passed: {report['summary']['passed']}</p>
        <p class="failure-header">Failures: {report['summary']['failures']}</p>
        <p class="error-header">Errors: {report['summary']['errors']}</p>
    </div>

    {self._generate_failures_section(report)}
    {self._generate_errors_section(report)}
</body>
</html>"""

        report_path = self.results_dir / f"iteration_{iteration_number:02d}_report.html"
        with open(report_path, 'w') as f:
            f.write(html_content)

    def _generate_failures_section(self, report):
        """Generate HTML for failures section."""
        if not report['failures']:
            return ""

        failures_html = "<h2>Failures</h2>"
        for failure in report['failures']:
            failures_html += f"""
            <div class="failure">
                <h3>{failure['test']}</h3>
                <pre>{failure['message']}</pre>
            </div>"""
        return failures_html

    def _generate_errors_section(self, report):
        """Generate HTML for errors section."""
        if not report['errors']:
            return ""

        errors_html = "<h2>Errors</h2>"
        for error in report['errors']:
            errors_html += f"""
            <div class="error">
                <h3>{error['test']}</h3>
                <pre>{error['message']}</pre>
            </div>"""
        return errors_html

    def run_all_iterations(self):
        """Run all iterations and generate final report."""
        all_results = []

        for i in range(1, self.iterations + 1):
            result = self.run_iteration(i)
            all_results.append(result)

            # If there are failures or errors, log them
            if result.failures or result.errors:
                logging.warning(f"Iteration {i} had issues:")
                for failure in result.failures:
                    logging.warning(f"Failure in {failure[0]}: {failure[1]}")
                for error in result.errors:
                    logging.error(f"Error in {error[0]}: {error[1]}")

            # Add a small delay between iterations
            time.sleep(1)

        # Generate final summary report
        self._generate_final_report(all_results)

    def _generate_final_report(self, all_results):
        """Generate a final summary report of all iterations."""
        summary = {
            "total_iterations": self.iterations,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "iterations": []
        }

        for i, result in enumerate(all_results, 1):
            iteration_summary = {
                "iteration": i,
                "total_tests": result.testsRun,
                "passed": result.testsRun - len(result.failures) - len(result.errors),
                "failures": len(result.failures),
                "errors": len(result.errors)
            }
            summary["iterations"].append(iteration_summary)

        # Save summary as JSON
        summary_path = self.results_dir / "final_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        # Generate HTML summary
        self._generate_html_summary(summary)

    def _generate_html_summary(self, summary):
        """Generate an HTML summary of all iterations."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Final Test Summary</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
        }}
        .success {{
            color: #28a745;
        }}
        .failure {{
            color: #dc3545;
        }}
    </style>
</head>
<body>
    <h1>Final Test Summary</h1>
    <p>Start Time: {summary['start_time']}</p>
    <p>End Time: {summary['end_time']}</p>

    <div class="summary">
        <h2>Overall Summary</h2>
        <p>Total Iterations: {summary['total_iterations']}</p>
    </div>

    <h2>Iteration Results</h2>
    <table>
        <tr>
            <th>Iteration</th>
            <th>Total Tests</th>
            <th>Passed</th>
            <th>Failures</th>
            <th>Errors</th>
        </tr>
        {self._generate_iteration_rows(summary['iterations'])}
    </table>
</body>
</html>"""

        summary_path = self.results_dir / "final_summary.html"
        with open(summary_path, 'w') as f:
            f.write(html_content)

    def _generate_iteration_rows(self, iterations):
        """Generate HTML table rows for iterations."""
        rows = ""
        for iteration in iterations:
            status_class = "success" if iteration['failures'] == 0 and iteration['errors'] == 0 else "failure"
            rows += f"""
            <tr class="{status_class}">
                <td>{iteration['iteration']}</td>
                <td>{iteration['total_tests']}</td>
                <td>{iteration['passed']}</td>
                <td>{iteration['failures']}</td>
                <td>{iteration['errors']}</td>
            </tr>"""
        return rows

def main():
    parser = argparse.ArgumentParser(description='Run wireframe refinement tests')
    parser.add_argument('--iterations', type=int, default=10,
                      help='Number of test iterations to run')
    args = parser.parse_args()

    runner = TestRunner(iterations=args.iterations)
    runner.run_all_iterations()

if __name__ == '__main__':
    main()
