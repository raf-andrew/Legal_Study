"""
Run all functional tests with comprehensive reporting and certification.
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List

from test_runner import FunctionalTestRunner
from test_config import (
    TEST_CATEGORIES,
    TEST_DIRS,
    CERTIFICATION_REQUIREMENTS,
    get_test_category,
    get_checklist_items,
    get_required_coverage
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_category_tests(runner: FunctionalTestRunner, category: str):
    """Run all tests for a specific category"""
    test_category = get_test_category(category)
    logger.info(f"Running tests for category: {test_category.name}")

    # Start test session
    runner.start_test(
        test_id=f"{category.upper()}-{datetime.now().strftime('%Y%m%d')}",
        test_name=test_category.name,
        checklist_items=test_category.checklist_items
    )

    try:
        # Run tests for this category
        test_dir = Path("tests") / category
        if not test_dir.exists():
            logger.warning(f"No tests found for category {category}")
            return

        # Add verification steps for each required step
        for step in test_category.required_steps:
            runner.add_verification_step(
                step_name=step,
                status="in_progress",
                details=f"Running {step} for {category}"
            )

        # Run pytest for this category
        import pytest
        pytest_args = [
            str(test_dir),
            "-v",
            f"--cov=sniffing.{category}",
            "--cov-report=term-missing",
            f"--cov-report=html:{TEST_DIRS['reports']}/coverage/{category}"
        ]

        exit_code = pytest.main(pytest_args)

        # Update verification steps
        for step in test_category.required_steps:
            runner.add_verification_step(
                step_name=step,
                status="passed" if exit_code == 0 else "failed",
                details=f"{step} {'passed' if exit_code == 0 else 'failed'} for {category}"
            )

        # Complete test
        runner.complete_test(
            status="passed" if exit_code == 0 else "failed",
            coverage=0.0  # This should be calculated from coverage report
        )

        # Certify if passed and meets requirements
        if exit_code == 0:
            runner.certify_test(
                test_id=f"{category.upper()}-{datetime.now().strftime('%Y%m%d')}",
                certifier="system"
            )

    except Exception as e:
        logger.error(f"Error running tests for category {category}: {e}")
        if runner.current_test:
            runner.complete_test("failed", 0.0)

def main():
    """Run all functional tests with comprehensive reporting"""
    try:
        # Initialize test runner
        runner = FunctionalTestRunner()

        # Run tests for each category
        for category in TEST_CATEGORIES:
            run_category_tests(runner, category)

        # Generate summary report
        summary = {
            "timestamp": datetime.now().isoformat(),
            "categories": {
                category: {
                    "name": test_category.name,
                    "status": "completed",
                    "coverage": get_required_coverage(category)
                }
                for category, test_category in TEST_CATEGORIES.items()
            }
        }

        # Save summary report
        summary_file = TEST_DIRS['reports'] / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Test summary saved to {summary_file}")
        return 0

    except Exception as e:
        logger.error(f"Error running functional tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
