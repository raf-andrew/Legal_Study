#!/usr/bin/env python3
"""
Test runner script for process documentation tests.
"""
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

class TestRunner:
    """Test runner for process documentation."""

    def __init__(self):
        """Initialize the test runner."""
        self.process_dir = Path(".process")
        self.complete_dir = Path(".complete")
        self.test_results_dir = Path("test_results")
        self.current_test_report = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "PENDING",
            "coverage": 0.0
        }

    def setup_environment(self):
        """Set up the test environment."""
        print("Setting up test environment...")

        # Create required directories
        self.test_results_dir.mkdir(exist_ok=True)
        self.complete_dir.mkdir(exist_ok=True)

        # Install requirements
        requirements_file = Path("requirements-test.txt")
        if requirements_file.exists():
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], check=True)
        else:
            print("Warning: requirements-test.txt not found")

    def run_test_suite(self) -> Dict[str, Any]:
        """Run the test suite and return results."""
        print("\nRunning test suite...")

        # Import and run the test implementation
        sys.path.append(str(self.process_dir / "testing"))
        from test_implementation import ProcessDocumentationTester

        tester = ProcessDocumentationTester()
        results = tester.run_all_tests()

        # Update current test report
        self.current_test_report["tests"] = results["test_results"]
        self.current_test_report["overall_status"] = "PASSED" if results["passed"] else "FAILED"

        return results

    def generate_test_report(self) -> Path:
        """Generate a detailed test report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.test_results_dir / f"test_report_{timestamp}.json"

        # Calculate coverage
        total_tests = len(self.current_test_report["tests"])
        passed_tests = sum(1 for test in self.current_test_report["tests"].values() if test["passed"])
        self.current_test_report["coverage"] = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # Save report
        with open(report_file, "w") as f:
            json.dump(self.current_test_report, f, indent=2)

        return report_file

    def check_completion_criteria(self, results: Dict[str, Any]) -> bool:
        """Check if all completion criteria are met."""
        if not results["passed"]:
            return False

        # Check for required test coverage
        if self.current_test_report["coverage"] < 100:
            return False

        # Check for any errors in test results
        for test_result in results["test_results"].values():
            if test_result.get("errors"):
                return False

        return True

    def move_to_complete(self, report_file: Path):
        """Move completed items to .complete directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        complete_dir = self.complete_dir / f"completed_{timestamp}"
        complete_dir.mkdir(exist_ok=True)

        # Copy test report
        with open(report_file, "r") as src, open(complete_dir / "test_report.json", "w") as dst:
            dst.write(src.read())

        # Copy relevant process files
        for file in self.process_dir.rglob("*"):
            if file.is_file() and not file.name.startswith("."):
                rel_path = file.relative_to(self.process_dir)
                target_path = complete_dir / rel_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file, "r") as src, open(target_path, "w") as dst:
                    dst.write(src.read())

    def run(self):
        """Run the complete test process."""
        try:
            # Setup
            self.setup_environment()

            # Run tests
            results = self.run_test_suite()

            # Generate report
            report_file = self.generate_test_report()

            # Check completion
            if self.check_completion_criteria(results):
                print("\nAll tests passed with 100% coverage!")
                self.move_to_complete(report_file)
                print(f"Completed items moved to: {self.complete_dir}")
            else:
                print("\nTests did not meet completion criteria.")
                print("Please fix the following issues:")
                for test_name, test_result in results["test_results"].items():
                    if not test_result["passed"]:
                        print(f"\n{test_name}:")
                        for error in test_result.get("errors", []):
                            print(f"- {error}")

            # Print summary
            print(f"\nTest report generated: {report_file}")
            print(f"Overall status: {self.current_test_report['overall_status']}")
            print(f"Coverage: {self.current_test_report['coverage']:.2f}%")

        except Exception as e:
            print(f"Error during test execution: {str(e)}")
            sys.exit(1)

def main():
    """Main function to run the test suite."""
    runner = TestRunner()
    runner.run()

if __name__ == "__main__":
    main()
