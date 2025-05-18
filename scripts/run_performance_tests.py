#!/usr/bin/env python3
"""
Performance Testing Script
This script runs performance tests to measure system performance and scalability.
"""

import os
import sys
import json
import logging
import time
import asyncio
import aiohttp
import psutil
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class PerformanceTester:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "pending",
            "execution_time": 0,
            "summary": {}
        }
        
        # Define performance test configurations
        self.test_configs = {
            "load_test": {
                "endpoint": "http://localhost:8000/api/test",
                "method": "GET",
                "concurrent_users": [10, 50, 100],
                "duration": 60,  # seconds
                "thresholds": {
                    "avg_response_time": 200,  # ms
                    "error_rate": 1,  # %
                    "requests_per_second": 100
                }
            },
            "stress_test": {
                "endpoint": "http://localhost:8000/api/test",
                "method": "POST",
                "concurrent_users": [200, 500, 1000],
                "duration": 300,  # seconds
                "thresholds": {
                    "avg_response_time": 500,  # ms
                    "error_rate": 5,  # %
                    "requests_per_second": 500
                }
            },
            "spike_test": {
                "endpoint": "http://localhost:8000/api/test",
                "method": "GET",
                "base_users": 50,
                "spike_users": 500,
                "duration": 180,  # seconds
                "thresholds": {
                    "recovery_time": 10,  # seconds
                    "error_rate": 10,  # %
                }
            },
            "endurance_test": {
                "endpoint": "http://localhost:8000/api/test",
                "method": "GET",
                "concurrent_users": 100,
                "duration": 3600,  # 1 hour
                "thresholds": {
                    "avg_response_time": 300,  # ms
                    "error_rate": 1,  # %
                    "memory_growth": 10  # %
                }
            }
        }

    async def make_request(self, session: aiohttp.ClientSession, 
                         endpoint: str, method: str) -> Dict:
        """Make a single HTTP request"""
        start_time = time.time()
        try:
            if method == "GET":
                async with session.get(endpoint) as response:
                    await response.text()
            else:  # POST
                async with session.post(endpoint, json={}) as response:
                    await response.text()
            
            return {
                "status": "success",
                "response_time": (time.time() - start_time) * 1000,  # Convert to ms
                "status_code": response.status
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time": (time.time() - start_time) * 1000
            }

    async def run_concurrent_requests(self, num_users: int, duration: int,
                                    endpoint: str, method: str) -> Dict:
        """Run concurrent requests for a specified duration"""
        start_time = time.time()
        results = []
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < duration:
                tasks = [
                    self.make_request(session, endpoint, method)
                    for _ in range(num_users)
                ]
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)
        
        # Calculate metrics
        successful_requests = [r for r in results if r["status"] == "success"]
        failed_requests = [r for r in results if r["status"] == "error"]
        response_times = [r["response_time"] for r in successful_requests]
        
        return {
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "error_rate": (len(failed_requests) / len(results)) * 100 if results else 0,
            "avg_response_time": statistics.mean(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else None,
            "requests_per_second": len(results) / duration
        }

    async def run_load_test(self) -> Dict:
        """Run load test with increasing concurrent users"""
        config = self.test_configs["load_test"]
        results = []
        
        for num_users in config["concurrent_users"]:
            logger.info(f"Running load test with {num_users} concurrent users")
            metrics = await self.run_concurrent_requests(
                num_users,
                config["duration"],
                config["endpoint"],
                config["method"]
            )
            results.append({
                "concurrent_users": num_users,
                "metrics": metrics
            })
        
        # Check if thresholds are met
        thresholds_met = all(
            result["metrics"]["avg_response_time"] < config["thresholds"]["avg_response_time"] and
            result["metrics"]["error_rate"] < config["thresholds"]["error_rate"] and
            result["metrics"]["requests_per_second"] > config["thresholds"]["requests_per_second"]
            for result in results
        )
        
        return {
            "status": "pass" if thresholds_met else "fail",
            "results": results
        }

    async def run_stress_test(self) -> Dict:
        """Run stress test with high concurrent users"""
        config = self.test_configs["stress_test"]
        results = []
        
        for num_users in config["concurrent_users"]:
            logger.info(f"Running stress test with {num_users} concurrent users")
            metrics = await self.run_concurrent_requests(
                num_users,
                config["duration"],
                config["endpoint"],
                config["method"]
            )
            results.append({
                "concurrent_users": num_users,
                "metrics": metrics
            })
        
        # Check if thresholds are met
        thresholds_met = all(
            result["metrics"]["avg_response_time"] < config["thresholds"]["avg_response_time"] and
            result["metrics"]["error_rate"] < config["thresholds"]["error_rate"] and
            result["metrics"]["requests_per_second"] > config["thresholds"]["requests_per_second"]
            for result in results
        )
        
        return {
            "status": "pass" if thresholds_met else "fail",
            "results": results
        }

    async def run_spike_test(self) -> Dict:
        """Run spike test with sudden increase in users"""
        config = self.test_configs["spike_test"]
        
        # Run baseline load
        logger.info(f"Running baseline load with {config['base_users']} users")
        baseline_metrics = await self.run_concurrent_requests(
            config["base_users"],
            30,  # 30 seconds baseline
            config["endpoint"],
            config["method"]
        )
        
        # Run spike load
        logger.info(f"Running spike load with {config['spike_users']} users")
        spike_metrics = await self.run_concurrent_requests(
            config["spike_users"],
            30,  # 30 seconds spike
            config["endpoint"],
            config["method"]
        )
        
        # Run recovery period
        logger.info("Measuring recovery period")
        recovery_start = time.time()
        recovery_metrics = await self.run_concurrent_requests(
            config["base_users"],
            30,  # 30 seconds recovery
            config["endpoint"],
            config["method"]
        )
        recovery_time = time.time() - recovery_start
        
        # Check if thresholds are met
        thresholds_met = (
            recovery_time < config["thresholds"]["recovery_time"] and
            spike_metrics["error_rate"] < config["thresholds"]["error_rate"]
        )
        
        return {
            "status": "pass" if thresholds_met else "fail",
            "results": {
                "baseline": baseline_metrics,
                "spike": spike_metrics,
                "recovery": {
                    "metrics": recovery_metrics,
                    "recovery_time": recovery_time
                }
            }
        }

    async def run_endurance_test(self) -> Dict:
        """Run endurance test over an extended period"""
        config = self.test_configs["endurance_test"]
        
        # Record initial memory usage
        initial_memory = psutil.Process().memory_info().rss
        
        # Run test
        logger.info(f"Running endurance test with {config['concurrent_users']} users")
        metrics = await self.run_concurrent_requests(
            config["concurrent_users"],
            config["duration"],
            config["endpoint"],
            config["method"]
        )
        
        # Record final memory usage
        final_memory = psutil.Process().memory_info().rss
        memory_growth = ((final_memory - initial_memory) / initial_memory) * 100
        
        # Check if thresholds are met
        thresholds_met = (
            metrics["avg_response_time"] < config["thresholds"]["avg_response_time"] and
            metrics["error_rate"] < config["thresholds"]["error_rate"] and
            memory_growth < config["thresholds"]["memory_growth"]
        )
        
        return {
            "status": "pass" if thresholds_met else "fail",
            "results": {
                "metrics": metrics,
                "memory": {
                    "initial": initial_memory,
                    "final": final_memory,
                    "growth_percentage": memory_growth
                }
            }
        }

    async def run_all_tests(self):
        """Run all performance tests"""
        start_time = time.time()
        
        # Run tests
        self.results["tests"]["load"] = await self.run_load_test()
        self.results["tests"]["stress"] = await self.run_stress_test()
        self.results["tests"]["spike"] = await self.run_spike_test()
        self.results["tests"]["endurance"] = await self.run_endurance_test()
        
        self.results["execution_time"] = time.time() - start_time
        
        # Calculate overall status
        failed_tests = [test for test in self.results["tests"].values() 
                       if test["status"] != "pass"]
        self.results["overall_status"] = "fail" if failed_tests else "pass"
        
        # Generate summary
        self.generate_summary()
        
        return self.results

    def generate_summary(self):
        """Generate performance test summary"""
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
        results_file = f"test_results/performance_tests_{timestamp}.json"
        
        os.makedirs("test_results", exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")

    def generate_report(self) -> str:
        """Generate a human-readable test report"""
        report = f"""
Performance Test Report
=====================
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
            
            if test_name == "load" or test_name == "stress":
                for result in test["results"]:
                    report += f"\n  Concurrent Users: {result['concurrent_users']}"
                    report += f"\n    Requests/second: {result['metrics']['requests_per_second']:.2f}"
                    report += f"\n    Avg Response Time: {result['metrics']['avg_response_time']:.2f} ms"
                    report += f"\n    Error Rate: {result['metrics']['error_rate']:.2f}%"
            elif test_name == "spike":
                report += "\n  Baseline:"
                report += f"\n    Requests/second: {test['results']['baseline']['requests_per_second']:.2f}"
                report += f"\n    Avg Response Time: {test['results']['baseline']['avg_response_time']:.2f} ms"
                report += "\n  Spike:"
                report += f"\n    Requests/second: {test['results']['spike']['requests_per_second']:.2f}"
                report += f"\n    Avg Response Time: {test['results']['spike']['avg_response_time']:.2f} ms"
                report += "\n  Recovery:"
                report += f"\n    Time: {test['results']['recovery']['recovery_time']:.2f} seconds"
            elif test_name == "endurance":
                report += f"\n  Requests/second: {test['results']['metrics']['requests_per_second']:.2f}"
                report += f"\n  Avg Response Time: {test['results']['metrics']['avg_response_time']:.2f} ms"
                report += f"\n  Memory Growth: {test['results']['memory']['growth_percentage']:.2f}%"
            
            report += "\n"
        
        return report

async def main():
    tester = PerformanceTester()
    results = await tester.run_all_tests()
    tester.save_results()
    
    # Print report
    print(tester.generate_report())
    
    # Exit with appropriate status code
    sys.exit(0 if results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    asyncio.run(main()) 