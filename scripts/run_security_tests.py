#!/usr/bin/env python3
"""
Security Testing Script
This script runs security tests to identify potential vulnerabilities.
"""

import os
import sys
import json
import logging
import time
import requests
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('security_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SecurityTester:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "pending",
            "execution_time": 0,
            "summary": {}
        }
        
        # Define security test configurations
        self.test_configs = {
            "authentication": {
                "endpoints": [
                    "/api/auth/login",
                    "/api/auth/register",
                    "/api/auth/reset-password"
                ],
                "test_cases": [
                    {
                        "name": "invalid_credentials",
                        "data": {
                            "username": "invalid_user",
                            "password": "invalid_pass"
                        },
                        "expected_status": 401
                    },
                    {
                        "name": "sql_injection",
                        "data": {
                            "username": "' OR '1'='1",
                            "password": "' OR '1'='1"
                        },
                        "expected_status": 401
                    },
                    {
                        "name": "xss_attempt",
                        "data": {
                            "username": "<script>alert('xss')</script>",
                            "password": "password123"
                        },
                        "expected_status": 400
                    }
                ]
            },
            "authorization": {
                "endpoints": [
                    "/api/users/profile",
                    "/api/admin/users",
                    "/api/admin/settings"
                ],
                "test_cases": [
                    {
                        "name": "no_token",
                        "headers": {},
                        "expected_status": 401
                    },
                    {
                        "name": "invalid_token",
                        "headers": {
                            "Authorization": "Bearer invalid_token"
                        },
                        "expected_status": 401
                    },
                    {
                        "name": "expired_token",
                        "headers": {
                            "Authorization": "Bearer expired_token"
                        },
                        "expected_status": 401
                    }
                ]
            },
            "input_validation": {
                "endpoints": [
                    "/api/users/update",
                    "/api/content/create",
                    "/api/messages/send"
                ],
                "test_cases": [
                    {
                        "name": "xss_payload",
                        "data": {
                            "content": "<script>alert('xss')</script>"
                        },
                        "expected_status": 400
                    },
                    {
                        "name": "sql_injection",
                        "data": {
                            "id": "1; DROP TABLE users;"
                        },
                        "expected_status": 400
                    },
                    {
                        "name": "command_injection",
                        "data": {
                            "filename": "file.txt; rm -rf /"
                        },
                        "expected_status": 400
                    }
                ]
            },
            "rate_limiting": {
                "endpoints": [
                    "/api/auth/login",
                    "/api/content/create",
                    "/api/messages/send"
                ],
                "requests_per_minute": 60,
                "test_duration": 70  # seconds
            },
            "file_upload": {
                "endpoint": "/api/files/upload",
                "test_cases": [
                    {
                        "name": "executable_file",
                        "file": "test.exe",
                        "content_type": "application/x-msdownload",
                        "expected_status": 400
                    },
                    {
                        "name": "oversized_file",
                        "file": "large.txt",
                        "size": 11 * 1024 * 1024,  # 11MB
                        "expected_status": 400
                    },
                    {
                        "name": "malicious_extension",
                        "file": "script.php.jpg",
                        "content_type": "image/jpeg",
                        "expected_status": 400
                    }
                ]
            }
        }

    def test_authentication(self) -> Dict:
        """Test authentication security"""
        config = self.test_configs["authentication"]
        results = []
        
        for endpoint in config["endpoints"]:
            for test_case in config["test_cases"]:
                try:
                    response = requests.post(
                        f"http://localhost:8000{endpoint}",
                        json=test_case["data"]
                    )
                    
                    results.append({
                        "endpoint": endpoint,
                        "test_case": test_case["name"],
                        "status": "pass" if response.status_code == test_case["expected_status"] else "fail",
                        "actual_status": response.status_code,
                        "expected_status": test_case["expected_status"]
                    })
                except Exception as e:
                    logger.error(f"Error testing authentication for {endpoint}: {e}")
                    results.append({
                        "endpoint": endpoint,
                        "test_case": test_case["name"],
                        "status": "error",
                        "error": str(e)
                    })
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "results": results
        }

    def test_authorization(self) -> Dict:
        """Test authorization security"""
        config = self.test_configs["authorization"]
        results = []
        
        for endpoint in config["endpoints"]:
            for test_case in config["test_cases"]:
                try:
                    response = requests.get(
                        f"http://localhost:8000{endpoint}",
                        headers=test_case["headers"]
                    )
                    
                    results.append({
                        "endpoint": endpoint,
                        "test_case": test_case["name"],
                        "status": "pass" if response.status_code == test_case["expected_status"] else "fail",
                        "actual_status": response.status_code,
                        "expected_status": test_case["expected_status"]
                    })
                except Exception as e:
                    logger.error(f"Error testing authorization for {endpoint}: {e}")
                    results.append({
                        "endpoint": endpoint,
                        "test_case": test_case["name"],
                        "status": "error",
                        "error": str(e)
                    })
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "results": results
        }

    def test_input_validation(self) -> Dict:
        """Test input validation security"""
        config = self.test_configs["input_validation"]
        results = []
        
        for endpoint in config["endpoints"]:
            for test_case in config["test_cases"]:
                try:
                    response = requests.post(
                        f"http://localhost:8000{endpoint}",
                        json=test_case["data"]
                    )
                    
                    results.append({
                        "endpoint": endpoint,
                        "test_case": test_case["name"],
                        "status": "pass" if response.status_code == test_case["expected_status"] else "fail",
                        "actual_status": response.status_code,
                        "expected_status": test_case["expected_status"]
                    })
                except Exception as e:
                    logger.error(f"Error testing input validation for {endpoint}: {e}")
                    results.append({
                        "endpoint": endpoint,
                        "test_case": test_case["name"],
                        "status": "error",
                        "error": str(e)
                    })
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "results": results
        }

    def test_rate_limiting(self) -> Dict:
        """Test rate limiting security"""
        config = self.test_configs["rate_limiting"]
        results = []
        
        for endpoint in config["endpoints"]:
            try:
                start_time = time.time()
                requests_sent = 0
                blocked_requests = 0
                
                while time.time() - start_time < config["test_duration"]:
                    response = requests.get(f"http://localhost:8000{endpoint}")
                    requests_sent += 1
                    
                    if response.status_code == 429:  # Too Many Requests
                        blocked_requests += 1
                    
                    # Sleep briefly to not overwhelm the server
                    time.sleep(0.1)
                
                # Calculate actual requests per minute
                duration_minutes = config["test_duration"] / 60
                requests_per_minute = requests_sent / duration_minutes
                
                results.append({
                    "endpoint": endpoint,
                    "requests_sent": requests_sent,
                    "blocked_requests": blocked_requests,
                    "requests_per_minute": requests_per_minute,
                    "status": "pass" if blocked_requests > 0 else "fail"
                })
            except Exception as e:
                logger.error(f"Error testing rate limiting for {endpoint}: {e}")
                results.append({
                    "endpoint": endpoint,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "results": results
        }

    def test_file_upload(self) -> Dict:
        """Test file upload security"""
        config = self.test_configs["file_upload"]
        results = []
        
        for test_case in config["test_cases"]:
            try:
                # Create test file
                with open(test_case["file"], "wb") as f:
                    if "size" in test_case:
                        f.write(b"0" * test_case["size"])
                    else:
                        f.write(b"test content")
                
                # Upload file
                with open(test_case["file"], "rb") as f:
                    files = {"file": (test_case["file"], f, test_case["content_type"])}
                    response = requests.post(
                        f"http://localhost:8000{config['endpoint']}",
                        files=files
                    )
                
                results.append({
                    "test_case": test_case["name"],
                    "status": "pass" if response.status_code == test_case["expected_status"] else "fail",
                    "actual_status": response.status_code,
                    "expected_status": test_case["expected_status"]
                })
                
                # Clean up test file
                os.remove(test_case["file"])
            except Exception as e:
                logger.error(f"Error testing file upload for {test_case['name']}: {e}")
                results.append({
                    "test_case": test_case["name"],
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "results": results
        }

    def run_all_tests(self):
        """Run all security tests"""
        start_time = time.time()
        
        # Run tests
        self.results["tests"]["authentication"] = self.test_authentication()
        self.results["tests"]["authorization"] = self.test_authorization()
        self.results["tests"]["input_validation"] = self.test_input_validation()
        self.results["tests"]["rate_limiting"] = self.test_rate_limiting()
        self.results["tests"]["file_upload"] = self.test_file_upload()
        
        self.results["execution_time"] = time.time() - start_time
        
        # Calculate overall status
        failed_tests = [test for test in self.results["tests"].values() 
                       if test["status"] != "pass"]
        self.results["overall_status"] = "fail" if failed_tests else "pass"
        
        # Generate summary
        self.generate_summary()
        
        return self.results

    def generate_summary(self):
        """Generate security test summary"""
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
        results_file = f"test_results/security_tests_{timestamp}.json"
        
        os.makedirs("test_results", exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")

    def generate_report(self) -> str:
        """Generate a human-readable test report"""
        report = f"""
Security Test Report
==================
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
        
        for test_name, test in self.results["tests"].items():
            report += f"\n{test_name.upper()}:"
            report += f"\n  Status: {test['status'].upper()}"
            
            if test.get("results"):
                report += "\n  Test Cases:"
                for result in test["results"]:
                    report += f"\n    - {result.get('test_case', result.get('endpoint', 'Unknown'))}: {result['status'].upper()}"
                    if result.get("actual_status"):
                        report += f" (Expected: {result['expected_status']}, Got: {result['actual_status']})"
                    if result.get("error"):
                        report += f"\n      Error: {result['error']}"
            
            report += "\n"
        
        return report

def main():
    tester = SecurityTester()
    results = tester.run_all_tests()
    tester.save_results()
    
    # Print report
    print(tester.generate_report())
    
    # Exit with appropriate status code
    sys.exit(0 if results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main() 