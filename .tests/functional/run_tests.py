#!/usr/bin/env python3
import os
import sys
import json
import datetime
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

class TestRunner:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.reports_dir = self.base_dir / "reports"
        self.evidence_dir = self.base_dir / "evidence"
        self.verification_dir = self.reports_dir / "verification"
        self.certification_dir = self.reports_dir / "certification"

        # Create necessary directories
        for directory in [self.reports_dir, self.evidence_dir,
                         self.verification_dir, self.certification_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def run_tests(self, test_path: str = None) -> bool:
        """Run the test suite and generate reports."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Build command
        cmd = [
            "python", "-m", "pytest",
            "--verbose",
            "--cov=app",
            "--cov-report=term-missing",
            f"--cov-report=html:{self.reports_dir}/coverage",
            f"--html={self.reports_dir}/test_report_{timestamp}.html",
            "--self-contained-html",
            f"--junitxml={self.reports_dir}/junit_{timestamp}.xml",
            "--metadata",
            f"--metadata-file={self.reports_dir}/metadata_{timestamp}.json",
            "--benchmark-only",
            f"--benchmark-json={self.reports_dir}/benchmark_{timestamp}.json",
            "--profile",
            f"--profile-svg={self.reports_dir}/profile_{timestamp}.svg"
        ]

        if test_path:
            cmd.append(test_path)
        else:
            cmd.append(str(self.base_dir / "tests"))

        # Run tests
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            success = True
        except subprocess.CalledProcessError as e:
            print(f"Tests failed: {e}")
            success = False
            result = e

        # Generate verification report
        self._generate_verification_report(result, timestamp)

        # Generate certification report if tests passed
        if success:
            self._generate_certification_report(result, timestamp)

        return success

    def _generate_verification_report(self, result: subprocess.CompletedProcess, timestamp: str):
        """Generate a verification report for the test run."""
        report = {
            "timestamp": timestamp,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }

        report_path = self.verification_dir / f"verification_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

    def _generate_certification_report(self, result: subprocess.CompletedProcess, timestamp: str):
        """Generate a certification report for successful test runs."""
        report = {
            "timestamp": timestamp,
            "status": "certified",
            "verification_report": f"verification_{timestamp}.json",
            "test_report": f"test_report_{timestamp}.html",
            "coverage_report": "coverage/index.html",
            "benchmark_report": f"benchmark_{timestamp}.json",
            "performance_profile": f"profile_{timestamp}.svg"
        }

        report_path = self.certification_dir / f"certification_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

def main():
    runner = TestRunner()
    test_path = sys.argv[1] if len(sys.argv) > 1 else None
    success = runner.run_tests(test_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
