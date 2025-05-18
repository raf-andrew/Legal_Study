#!/usr/bin/env python3
"""
Platform Test Orchestration Script
This script orchestrates all platform tests
"""

import os
import sys
import logging
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('platform_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TestOrchestrator:
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "overall_status": "pending"
        }
        self.test_scripts = [
            "validate_checklists.py",
            "test_ai_features.py",
            "test_notifications.py",
            "run_integration_tests.py",
            "run_platform_validation.py"
        ]

    def setup_environment(self):
        """Set up the test environment"""
        logger.info("Setting up test environment")
        try:
            # Ensure we're in the correct directory
            os.chdir(Path(__file__).parent.parent)

            # Create necessary directories
            os.makedirs("tests/data", exist_ok=True)
            os.makedirs("test_results", exist_ok=True)

            # Set up test data if needed
            self._setup_test_data()

            logger.info("Test environment setup completed")
            return True
        except Exception as e:
            logger.error(f"Error setting up test environment: {e}")
            return False

    def _setup_test_data(self):
        """Set up test data files"""
        test_data = {
            "ai_test_data.json": {
                "prompts": [
                    "Generate a test response",
                    "Summarize this text",
                    "Translate to Spanish"
                ],
                "expected_formats": [
                    "text",
                    "json",
                    "markdown"
                ]
            },
            "notification_test_data.json": {
                "email": {
                    "to": "test@example.com",
                    "subject": "Test Email",
                    "body": "This is a test email"
                },
                "push": {
                    "user_id": "test_user",
                    "title": "Test Notification",
                    "message": "This is a test notification"
                }
            }
        }

        for filename, data in test_data.items():
            file_path = Path("tests/data") / filename
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)

    def run_test_script(self, script_name: str) -> Dict:
        """Run a single test script"""
        logger.info(f"Running {script_name}")
        try:
            result = subprocess.run(
                [sys.executable, f"scripts/{script_name}"],
                capture_output=True,
                text=True,
                check=True
            )
            return {
                "status": "success" if result.returncode == 0 else "failure",
                "output": result.stdout,
                "error": result.stderr if result.stderr else None
            }
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running {script_name}: {e}")
            return {
                "status": "error",
                "output": e.stdout if e.stdout else None,
                "error": e.stderr if e.stderr else str(e)
            }

    def run_all_tests(self):
        """Run all test scripts"""
        logger.info("Starting platform tests")

        if not self.setup_environment():
            logger.error("Failed to set up test environment")
            return False

        for script in self.test_scripts:
            self.results["tests"][script] = self.run_test_script(script)

        # Update overall status
        self._update_overall_status()

        # Save results
        self._save_results()

        logger.info("Platform tests completed")
        return self.results

    def _update_overall_status(self):
        """Update the overall status based on test results"""
        statuses = [test["status"] for test in self.results["tests"].values()]

        if not statuses:
            self.results["overall_status"] = "unknown"
        elif all(status == "success" for status in statuses):
            self.results["overall_status"] = "success"
        elif any(status == "success" for status in statuses):
            self.results["overall_status"] = "partial"
        else:
            self.results["overall_status"] = "failure"

    def _save_results(self):
        """Save test results to file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"test_results/platform_test_results_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {output_file}")

    def generate_report(self) -> str:
        """Generate a human-readable test report"""
        report = [
            "Platform Test Report",
            "===================",
            f"Generated at: {self.results['timestamp']}",
            f"Overall Status: {self.results['overall_status'].upper()}",
            "",
            "Test Results:",
            "------------"
        ]

        for script, result in self.results["tests"].items():
            report.append(f"\n{script}:")
            report.append(f"  Status: {result['status'].upper()}")
            if result.get("error"):
                report.append(f"  Error: {result['error']}")

        return "\n".join(report)

def main():
    """Main function"""
    try:
        orchestrator = TestOrchestrator()
        results = orchestrator.run_all_tests()

        # Print report
        print(orchestrator.generate_report())

        # Exit with appropriate status code
        sys.exit(0 if results["overall_status"] == "success" else 1)

    except Exception as e:
        logger.error(f"Test orchestration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
