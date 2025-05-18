#!/usr/bin/env python3
"""
Parallel Test Runner Script
This script executes tests in parallel to improve test execution time.
"""

import os
import sys
import json
import logging
import subprocess
import time
import multiprocessing
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parallel_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ParallelTestRunner:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "pending",
            "execution_time": 0,
            "summary": {}
        }
        
        # Define test suites and their configurations
        self.test_suites = {
            "unit_tests": {
                "directory": "tests/unit",
                "pattern": "test_*.py",
                "parallel": True,
                "priority": 1,
                "required": True
            },
            "integration_tests": {
                "directory": "tests/integration",
                "pattern": "test_*.py",
                "parallel": True,
                "priority": 2,
                "required": True
            },
            "api_tests": {
                "directory": "tests/api",
                "pattern": "test_*.py",
                "parallel": True,
                "priority": 2,
                "required": True
            },
            "ai_tests": {
                "directory": "tests/ai",
                "pattern": "test_*.py",
                "parallel": False,  # AI tests might need sequential execution
                "priority": 3,
                "required": True
            },
            "notification_tests": {
                "directory": "tests/notifications",
                "pattern": "test_*.py",
                "parallel": True,
                "priority": 3,
                "required": True
            },
            "performance_tests": {
                "directory": "tests/performance",
                "pattern": "test_*.py",
                "parallel": False,  # Performance tests should run sequentially
                "priority": 4,
                "required": False
            }
        }
        
        # Set maximum parallel workers
        self.max_workers = multiprocessing.cpu_count()

    def discover_tests(self, suite_name: str, suite_config: Dict) -> List[str]:
        """Discover test files in a suite"""
        try:
            test_dir = Path(suite_config["directory"])
            if not test_dir.exists():
                logger.warning(f"Test directory {test_dir} does not exist")
                return []
            
            test_files = list(test_dir.glob(suite_config["pattern"]))
            logger.info(f"Discovered {len(test_files)} test files in {suite_name}")
            return [str(f) for f in test_files]
        except Exception as e:
            logger.error(f"Error discovering tests for {suite_name}: {e}")
            return []

    def run_test_file(self, test_file: str) -> Dict:
        """Run a single test file"""
        try:
            start_time = time.time()
            
            # Run test with pytest
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--json-report"],
                capture_output=True,
                text=True
            )
            
            execution_time = time.time() - start_time
            
            # Try to parse JSON report
            try:
                report_file = Path(".report.json")
                if report_file.exists():
                    with open(report_file) as f:
                        test_report = json.load(f)
                    report_file.unlink()  # Clean up report file
                else:
                    test_report = None
            except Exception:
                test_report = None
            
            return {
                "file": test_file,
                "status": "pass" if result.returncode == 0 else "fail",
                "execution_time": execution_time,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "report": test_report
            }
        except Exception as e:
            logger.error(f"Error running test file {test_file}: {e}")
            return {
                "file": test_file,
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time
            }

    def run_test_suite(self, suite_name: str, suite_config: Dict) -> Dict:
        """Run a test suite"""
        try:
            start_time = time.time()
            
            # Discover tests
            test_files = self.discover_tests(suite_name, suite_config)
            if not test_files:
                return {
                    "status": "skip",
                    "execution_time": 0,
                    "error": "No test files found"
                }
            
            # Run tests
            results = []
            if suite_config["parallel"]:
                # Run tests in parallel
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    future_to_test = {
                        executor.submit(self.run_test_file, test_file): test_file
                        for test_file in test_files
                    }
                    for future in as_completed(future_to_test):
                        results.append(future.result())
            else:
                # Run tests sequentially
                for test_file in test_files:
                    results.append(self.run_test_file(test_file))
            
            # Calculate metrics
            execution_time = time.time() - start_time
            passed_tests = sum(1 for r in results if r["status"] == "pass")
            failed_tests = sum(1 for r in results if r["status"] == "fail")
            error_tests = sum(1 for r in results if r["status"] == "error")
            
            return {
                "status": "pass" if failed_tests == 0 and error_tests == 0 else "fail",
                "execution_time": execution_time,
                "metrics": {
                    "total_tests": len(results),
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "error_tests": error_tests,
                    "success_rate": (passed_tests / len(results)) * 100 if results else 0
                },
                "results": results
            }
        except Exception as e:
            logger.error(f"Error running test suite {suite_name}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time
            }

    def run_all_tests(self):
        """Run all test suites"""
        start_time = time.time()
        
        # Sort test suites by priority
        sorted_suites = sorted(
            self.test_suites.items(),
            key=lambda x: x[1]["priority"]
        )
        
        # Run test suites
        for suite_name, suite_config in sorted_suites:
            logger.info(f"Running test suite: {suite_name}")
            self.results["tests"][suite_name] = self.run_test_suite(suite_name, suite_config)
            
            # Stop if a required suite fails
            if (suite_config["required"] and 
                self.results["tests"][suite_name]["status"] != "pass"):
                logger.error(f"Required test suite {suite_name} failed. Stopping tests.")
                break
        
        self.results["execution_time"] = time.time() - start_time
        
        # Calculate overall status
        failed_suites = [suite for suite_name, suite in self.results["tests"].items()
                        if self.test_suites[suite_name]["required"] and
                        suite["status"] != "pass"]
        self.results["overall_status"] = "fail" if failed_suites else "pass"
        
        # Generate summary
        self.generate_summary()
        
        return self.results

    def generate_summary(self):
        """Generate test execution summary"""
        total_suites = len(self.results["tests"])
        passed_suites = sum(1 for suite in self.results["tests"].values() 
                          if suite["status"] == "pass")
        failed_suites = total_suites - passed_suites
        
        total_tests = sum(suite["metrics"]["total_tests"] 
                         for suite in self.results["tests"].values() 
                         if "metrics" in suite)
        passed_tests = sum(suite["metrics"]["passed_tests"] 
                          for suite in self.results["tests"].values() 
                          if "metrics" in suite)
        failed_tests = sum(suite["metrics"]["failed_tests"] 
                          for suite in self.results["tests"].values() 
                          if "metrics" in suite)
        error_tests = sum(suite["metrics"]["error_tests"] 
                         for suite in self.results["tests"].values() 
                         if "metrics" in suite)
        
        self.results["summary"] = {
            "total_suites": total_suites,
            "passed_suites": passed_suites,
            "failed_suites": failed_suites,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "execution_time": self.results["execution_time"]
        }

    def save_results(self):
        """Save test results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_results/parallel_tests_{timestamp}.json"
        
        os.makedirs("test_results", exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")

    def generate_report(self) -> str:
        """Generate a human-readable test report"""
        report = f"""
Parallel Test Report
==================
Generated at: {self.results['timestamp']}
Overall Status: {self.results['overall_status'].upper()}
Total Execution Time: {self.results['execution_time']:.2f} seconds

Summary:
--------
Test Suites: {self.results['summary']['total_suites']} total, {self.results['summary']['passed_suites']} passed, {self.results['summary']['failed_suites']} failed
Tests: {self.results['summary']['total_tests']} total, {self.results['summary']['passed_tests']} passed, {self.results['summary']['failed_tests']} failed, {self.results['summary']['error_tests']} errors
Success Rate: {self.results['summary']['success_rate']:.2f}%

Detailed Results:
---------------
"""
        
        for suite_name, suite in self.results["tests"].items():
            report += f"\n{suite_name.upper()}:"
            report += f"\n  Status: {suite['status'].upper()}"
            report += f"\n  Execution Time: {suite['execution_time']:.2f} seconds"
            
            if suite.get("metrics"):
                report += "\n  Metrics:"
                for metric, value in suite["metrics"].items():
                    if isinstance(value, float):
                        report += f"\n    - {metric}: {value:.2f}"
                    else:
                        report += f"\n    - {metric}: {value}"
            
            if suite.get("error"):
                report += f"\n  Error: {suite['error']}"
            
            if suite.get("results"):
                report += "\n  Test Files:"
                for test_result in suite["results"]:
                    report += f"\n    - {test_result['file']}: {test_result['status'].upper()}"
                    if test_result.get("error"):
                        report += f"\n      Error: {test_result['error']}"
            
            report += "\n"
        
        return report

def main():
    runner = ParallelTestRunner()
    results = runner.run_all_tests()
    runner.save_results()
    
    # Print report
    print(runner.generate_report())
    
    # Exit with appropriate status code
    sys.exit(0 if results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main() 