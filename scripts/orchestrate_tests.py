#!/usr/bin/env python3
"""
Test Orchestration Script
This script coordinates the execution of all platform tests and generates comprehensive reports.
"""

import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_orchestration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TestOrchestrator:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "pending",
            "execution_time": 0,
            "summary": {}
        }
        
        # Define test scripts and their priorities
        self.test_scripts = {
            "smoke_tests": {
                "script": "run_smoke_tests.py",
                "priority": 1,
                "required": True
            },
            "platform_tests": {
                "script": "run_platform_tests.py",
                "priority": 2,
                "required": True
            },
            "ai_tests": {
                "script": "test_ai_features.py",
                "priority": 3,
                "required": True
            },
            "notification_tests": {
                "script": "test_notifications.py",
                "priority": 3,
                "required": True
            }
        }

    def run_test_script(self, script_name: str, script_info: Dict) -> Dict:
        """Run a test script and return its results"""
        try:
            logger.info(f"Running {script_name}...")
            start_time = time.time()
            
            # Run the script and capture output
            result = subprocess.run(
                [sys.executable, f"scripts/{script_info['script']}"],
                capture_output=True,
                text=True
            )
            
            execution_time = time.time() - start_time
            
            # Try to parse JSON output if available
            try:
                test_results = json.loads(result.stdout)
            except json.JSONDecodeError:
                test_results = {
                    "output": result.stdout,
                    "error": result.stderr if result.stderr else None
                }
            
            return {
                "status": "pass" if result.returncode == 0 else "fail",
                "execution_time": execution_time,
                "results": test_results,
                "error": result.stderr if result.stderr else None
            }
        except Exception as e:
            logger.error(f"Error running {script_name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time
            }

    def run_all_tests(self):
        """Run all test scripts in priority order"""
        start_time = time.time()
        
        # Sort test scripts by priority
        sorted_scripts = sorted(
            self.test_scripts.items(),
            key=lambda x: x[1]["priority"]
        )
        
        # Run each test script
        for script_name, script_info in sorted_scripts:
            self.results["tests"][script_name] = self.run_test_script(script_name, script_info)
            
            # If a required test fails, stop testing
            if (script_info["required"] and 
                self.results["tests"][script_name]["status"] != "pass"):
                logger.error(f"Required test {script_name} failed. Stopping tests.")
                break
        
        self.results["execution_time"] = time.time() - start_time
        
        # Calculate overall status
        failed_tests = [test for test in self.results["tests"].values() 
                       if test["status"] != "pass"]
        self.results["overall_status"] = "fail" if failed_tests else "pass"
        
        # Generate summary
        self.generate_summary()
        
        return self.results

    def generate_summary(self):
        """Generate test execution summary"""
        total_tests = len(self.results["tests"])
        passed_tests = sum(1 for test in self.results["tests"].values() 
                          if test["status"] == "pass")
        failed_tests = total_tests - passed_tests
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "execution_time": self.results["execution_time"]
        }

    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_results/orchestration_{timestamp}.json"
        
        os.makedirs("test_results", exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")

    def generate_report(self) -> str:
        """Generate a human-readable test report"""
        report = f"""
Test Orchestration Report
========================
Generated at: {self.results['timestamp']}
Overall Status: {self.results['overall_status'].upper()}
Total Execution Time: {self.results['execution_time']:.2f} seconds

Summary:
--------
Total Tests: {self.results['summary']['total_tests']}
Passed Tests: {self.results['summary']['passed_tests']}
Failed Tests: {self.results['summary']['failed_tests']}
Success Rate: {self.results['summary']['success_rate']:.2f}%

Detailed Results:
---------------
"""
        
        for test_name, result in self.results["tests"].items():
            report += f"\n{test_name.upper()}:"
            report += f"\n  Status: {result['status'].upper()}"
            report += f"\n  Execution Time: {result['execution_time']:.2f} seconds"
            
            if result.get("error"):
                report += f"\n  Error: {result['error']}"
            
            if result.get("results"):
                report += "\n  Results:"
                if isinstance(result["results"], dict):
                    for key, value in result["results"].items():
                        report += f"\n    - {key}: {value}"
                else:
                    report += f"\n    {result['results']}"
            
            report += "\n"
        
        return report

def main():
    orchestrator = TestOrchestrator()
    results = orchestrator.run_all_tests()
    orchestrator.save_results()
    
    # Print report
    print(orchestrator.generate_report())
    
    # Exit with appropriate status code
    sys.exit(0 if results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main() 