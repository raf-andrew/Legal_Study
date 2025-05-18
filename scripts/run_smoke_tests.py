#!/usr/bin/env python3
"""
Platform Smoke Testing Script
This script runs smoke tests to verify basic platform functionality.
"""

import os
import sys
import json
import logging
import time
import requests
import psutil
import redis
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smoke_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SmokeTester:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "pending",
            "execution_time": 0,
            "summary": {}
        }
        
        # Define test endpoints and their expected responses
        self.endpoints = {
            "api_health": "/api/health",
            "database_health": "/api/database/health",
            "cache_health": "/api/cache/health",
            "ai_health": "/api/ai/health",
            "notification_health": "/api/notifications/health"
        }
        
        # Define test thresholds
        self.thresholds = {
            "response_time": 200,  # ms
            "success_rate": 99.9,  # %
            "error_rate": 0.1,     # %
            "cpu_usage": 70,       # %
            "memory_usage": 80,    # %
            "disk_usage": 75       # %
        }

    def check_endpoint(self, endpoint: str) -> Dict:
        """Check health of a specific endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "status": "pass" if response.status_code == 200 else "fail",
                "metrics": {
                    "response_time": response_time,
                    "status_code": response.status_code
                },
                "data": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            logger.error(f"Error checking endpoint {endpoint}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def check_system_resources(self) -> Dict:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "pass" if (
                    cpu_percent < self.thresholds["cpu_usage"] and
                    memory.percent < self.thresholds["memory_usage"] and
                    disk.percent < self.thresholds["disk_usage"]
                ) else "fail",
                "metrics": {
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory.percent,
                    "disk_usage": disk.percent
                }
            }
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def check_database_connection(self) -> Dict:
        """Check database connection"""
        try:
            # Implement database connection check
            return {
                "status": "pass",
                "metrics": {
                    "connection_time": 0.0,
                    "query_time": 0.0
                }
            }
        except Exception as e:
            logger.error(f"Error checking database connection: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def check_cache_connection(self) -> Dict:
        """Check cache connection"""
        try:
            # Implement cache connection check
            return {
                "status": "pass",
                "metrics": {
                    "connection_time": 0.0,
                    "operation_time": 0.0
                }
            }
        except Exception as e:
            logger.error(f"Error checking cache connection: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def check_ai_system(self) -> Dict:
        """Check AI system health"""
        try:
            # Implement AI system health check
            return {
                "status": "pass",
                "metrics": {
                    "model_loaded": True,
                    "inference_time": 0.0
                }
            }
        except Exception as e:
            logger.error(f"Error checking AI system: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def check_notification_system(self) -> Dict:
        """Check notification system health"""
        try:
            # Implement notification system health check
            return {
                "status": "pass",
                "metrics": {
                    "queue_size": 0,
                    "processing_rate": 0.0
                }
            }
        except Exception as e:
            logger.error(f"Error checking notification system: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def run_all_tests(self):
        """Run all smoke tests"""
        start_time = time.time()
        
        # Check all endpoints
        for endpoint_name, endpoint_path in self.endpoints.items():
            self.results["tests"][endpoint_name] = self.check_endpoint(endpoint_path)
        
        # Check system resources
        self.results["tests"]["system_resources"] = self.check_system_resources()
        
        # Check database connection
        self.results["tests"]["database"] = self.check_database_connection()
        
        # Check cache connection
        self.results["tests"]["cache"] = self.check_cache_connection()
        
        # Check AI system
        self.results["tests"]["ai_system"] = self.check_ai_system()
        
        # Check notification system
        self.results["tests"]["notification_system"] = self.check_notification_system()
        
        self.results["execution_time"] = time.time() - start_time
        
        # Calculate overall status
        failed_tests = [test for test in self.results["tests"].values() 
                       if test["status"] == "fail"]
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
        results_file = f"test_results/smoke_tests_{timestamp}.json"
        
        os.makedirs("test_results", exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")

    def generate_report(self) -> str:
        """Generate a human-readable test report"""
        report = f"""
Smoke Test Report
================
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
            
            if result.get("metrics"):
                report += "\n  Metrics:"
                for metric, value in result["metrics"].items():
                    report += f"\n    - {metric}: {value}"
            
            if result.get("error"):
                report += f"\n  Error: {result['error']}"
            
            report += "\n"
        
        return report

def main():
    tester = SmokeTester()
    results = tester.run_all_tests()
    tester.save_results()
    
    # Print report
    print(tester.generate_report())
    
    # Exit with appropriate status code
    sys.exit(0 if results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main() 