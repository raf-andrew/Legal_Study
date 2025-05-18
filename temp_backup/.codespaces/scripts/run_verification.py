#!/usr/bin/env python3
import argparse
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class VerificationRunner:
    def __init__(self):
        """Initialize the VerificationRunner."""
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        self._setup_paths()

    def _setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'verification_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            ]
        )

    def _setup_paths(self):
        """Set up directory paths for verification process."""
        self.base_dir = Path(".codespaces")
        self.scripts_dir = self.base_dir / "scripts"
        self.reports_dir = self.base_dir / "reports"
        self.verification_dir = self.base_dir / "verification"

        # Create necessary directories
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.verification_dir.mkdir(parents=True, exist_ok=True)

    def run_tests(self) -> bool:
        """Run the unit tests."""
        try:
            self.logger.info("Running unit tests...")
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / "run_unit_tests.py")],
                check=True,
                capture_output=True,
                text=True
            )
            self.logger.info("Unit tests completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Unit tests failed: {e.stderr}")
            return False

    def generate_verification_reports(self) -> bool:
        """Generate verification reports for each test suite."""
        try:
            self.logger.info("Generating verification reports...")

            # Find all test report directories
            test_dirs = list(self.reports_dir.glob("**/test_*"))

            for test_dir in test_dirs:
                test_report = test_dir / "report.html"
                coverage_report = test_dir / "coverage.xml"

                if test_report.exists() and coverage_report.exists():
                    output_file = self.verification_dir / f"verification_{test_dir.name}.json"

                    result = subprocess.run(
                        [
                            sys.executable,
                            str(self.scripts_dir / "generate_verification_report.py"),
                            "--test-report", str(test_report),
                            "--coverage-report", str(coverage_report),
                            "--output", str(output_file)
                        ],
                        check=True,
                        capture_output=True,
                        text=True
                    )

                    self.logger.info(f"Generated verification report for {test_dir.name}")

            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to generate verification reports: {e.stderr}")
            return False

    def generate_summary(self) -> bool:
        """Generate the verification summary."""
        try:
            self.logger.info("Generating verification summary...")

            summary_file = self.verification_dir / "verification_summary.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(self.scripts_dir / "generate_verification_summary.py"),
                    "--reports-dir", str(self.verification_dir),
                    "--output", str(summary_file)
                ],
                check=True,
                capture_output=True,
                text=True
            )

            self.logger.info("Generated verification summary")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to generate verification summary: {e.stderr}")
            return False

    def generate_markdown_report(self) -> bool:
        """Generate the markdown report."""
        try:
            self.logger.info("Generating markdown report...")

            summary_file = self.verification_dir / "verification_summary.json"
            markdown_file = self.verification_dir / "verification_report.md"

            result = subprocess.run(
                [
                    sys.executable,
                    str(self.scripts_dir / "generate_markdown_report.py"),
                    "--summary", str(summary_file),
                    "--output", str(markdown_file)
                ],
                check=True,
                capture_output=True,
                text=True
            )

            self.logger.info("Generated markdown report")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to generate markdown report: {e.stderr}")
            return False

    def run(self) -> bool:
        """Run the complete verification process."""
        try:
            # Run tests
            if not self.run_tests():
                return False

            # Generate verification reports
            if not self.generate_verification_reports():
                return False

            # Generate summary
            if not self.generate_summary():
                return False

            # Generate markdown report
            if not self.generate_markdown_report():
                return False

            self.logger.info("Verification process completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Verification process failed: {e}")
            return False

def main():
    """Main function to run the verification process."""
    parser = argparse.ArgumentParser(description="Run the complete verification process")
    args = parser.parse_args()

    runner = VerificationRunner()
    success = runner.run()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
