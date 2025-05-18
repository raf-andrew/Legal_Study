#!/usr/bin/env python3
import pytest
import json
import datetime
import os
from pathlib import Path
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('health_check.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_health_checks():
    """Run all health checks and generate a report."""
    logging.info("Starting platform health checks...")
    
    # Create reports directory if it doesn't exist
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Run smoke tests
    try:
        pytest.main([
            "tests/smoke/test_platform_health.py",
            "-v",
            "--json-report",
            "--json-report-file=reports/health_check.json"
        ])
    except Exception as e:
        logging.error(f"Error running health checks: {str(e)}")
        return False

    # Generate human-readable report
    try:
        with open("reports/health_check.json", "r") as f:
            test_results = json.load(f)
        
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": {
                "total_tests": test_results["summary"]["total"],
                "passed": test_results["summary"]["passed"],
                "failed": test_results["summary"]["failed"],
                "skipped": test_results["summary"]["skipped"],
                "duration": test_results["summary"]["duration"]
            },
            "test_results": []
        }

        for test in test_results["tests"]:
            result = {
                "name": test["nodeid"],
                "outcome": test["outcome"],
                "duration": test["duration"],
                "message": test.get("message", "")
            }
            report["test_results"].append(result)

        # Save human-readable report
        with open("reports/health_check_report.json", "w") as f:
            json.dump(report, f, indent=2)

        # Generate HTML report
        html_report = generate_html_report(report)
        with open("reports/health_check_report.html", "w") as f:
            f.write(html_report)

        logging.info("Health check report generated successfully")
        return True

    except Exception as e:
        logging.error(f"Error generating report: {str(e)}")
        return False

def generate_html_report(report):
    """Generate an HTML report from the test results."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Platform Health Check Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .summary {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
            .test-result {{ margin: 10px 0; padding: 10px; border-radius: 3px; }}
            .passed {{ background-color: #dff0d8; }}
            .failed {{ background-color: #f2dede; }}
            .skipped {{ background-color: #fcf8e3; }}
            .timestamp {{ color: #666; }}
        </style>
    </head>
    <body>
        <h1>Platform Health Check Report</h1>
        <p class="timestamp">Generated at: {report['timestamp']}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>Total Tests: {report['summary']['total']}</p>
            <p>Passed: {report['summary']['passed']}</p>
            <p>Failed: {report['summary']['failed']}</p>
            <p>Skipped: {report['summary']['skipped']}</p>
            <p>Duration: {report['summary']['duration']:.2f} seconds</p>
        </div>

        <h2>Test Results</h2>
    """

    for test in report['test_results']:
        status_class = test['outcome']
        html += f"""
        <div class="test-result {status_class}">
            <h3>{test['name']}</h3>
            <p>Status: {test['outcome']}</p>
            <p>Duration: {test['duration']:.2f} seconds</p>
            {f'<p>Message: {test["message"]}</p>' if test['message'] else ''}
        </div>
        """

    html += """
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    success = run_health_checks()
    sys.exit(0 if success else 1) 