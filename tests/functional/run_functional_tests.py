"""
Test runner for functional tests with comprehensive reporting.
"""
import os
import sys
import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TEST_DIR = Path(__file__).parent
REPORT_DIR = Path("reports/functional_tests")
COVERAGE_DIR = Path("reports/coverage")

def ensure_directories():
    """Ensure all required directories exist."""
    for directory in [REPORT_DIR, COVERAGE_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def run_tests() -> Dict:
    """Run all functional tests and collect results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Run tests with coverage
    pytest_args = [
        str(TEST_DIR),
        "-v",
        "--cov=sniffing",
        f"--cov-report=html:{COVERAGE_DIR}/functional_{timestamp}",
        f"--cov-report=term-missing",
        "--junitxml=reports/functional_tests/junit.xml",
        "--html=reports/functional_tests/report.html"
    ]

    exit_code = pytest.main(pytest_args)

    # Collect test results
    results = {
        "timestamp": datetime.now().isoformat(),
        "exit_code": exit_code,
        "coverage_report": f"{COVERAGE_DIR}/functional_{timestamp}/index.html",
        "junit_report": "reports/functional_tests/junit.xml",
        "html_report": "reports/functional_tests/report.html"
    }

    return results

def save_summary_report(results: Dict):
    """Save summary report of all test runs."""
    summary_file = REPORT_DIR / "test_summary.json"

    # Load existing summary if it exists
    if summary_file.exists():
        with open(summary_file) as f:
            summary = json.load(f)
    else:
        summary = {"test_runs": []}

    # Add new results
    summary["test_runs"].append(results)

    # Save updated summary
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Summary report saved to {summary_file}")

def main():
    """Main entry point for running functional tests."""
    try:
        # Ensure directories exist
        ensure_directories()

        # Run tests
        logger.info("Starting functional test suite...")
        results = run_tests()

        # Save summary report
        save_summary_report(results)

        # Log completion
        if results["exit_code"] == 0:
            logger.info("All functional tests passed successfully!")
        else:
            logger.error("Some functional tests failed. Check the reports for details.")

        return results["exit_code"]

    except Exception as e:
        logger.error(f"Error running functional tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
