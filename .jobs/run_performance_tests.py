import subprocess
import json
import logging
import os
import sys
import psutil
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceTester:
    def __init__(self, config_path: str = "config/performance_tests.json"):
        self.config = self._load_config(config_path)
        self.results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "endpoints": {
                    "api": "http://localhost:8000/api",
                    "ai": "http://localhost:8000/ai",
                    "notifications": "http://localhost:8000/notifications"
                },
                "load_test": {
                    "concurrent_users": [10, 50, 100],
                    "duration_seconds": 60,
                    "ramp_up_seconds": 10
                },
                "thresholds": {
                    "response_time": 1.0,
                    "error_rate": 0.01,
                    "cpu_percent": 80,
                    "memory_percent": 80
                }
            }

    def measure_system_resources(self) -> Dict:
        """Measure current system resource usage."""
        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count()
            },
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "available": psutil.virtual_memory().available
            },
            "disk": {
                "percent": psutil.disk_usage('/').percent,
                "free": psutil.disk_usage('/').free
            },
            "network": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv
            }
        }

    def test_endpoint(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Test a single endpoint and measure performance."""
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = requests.get(url, timeout=5)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=5)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            duration = time.time() - start_time
            
            return {
                "status_code": response.status_code,
                "response_time": duration,
                "success": response.status_code == 200,
                "error": None
            }
        except Exception as e:
            return {
                "status_code": None,
                "response_time": None,
                "success": False,
                "error": str(e)
            }

    def run_load_test(self, endpoint: str, users: int, duration: int) -> Dict:
        """Run a load test with specified number of concurrent users."""
        results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_duration": 0,
            "avg_response_time": 0,
            "min_response_time": float('inf'),
            "max_response_time": 0,
            "errors": []
        }
        
        def worker():
            while time.time() - start_time < duration:
                result = self.test_endpoint(endpoint)
                results["total_requests"] += 1
                
                if result["success"]:
                    results["successful_requests"] += 1
                    response_time = result["response_time"]
                    results["total_duration"] += response_time
                    results["min_response_time"] = min(results["min_response_time"], response_time)
                    results["max_response_time"] = max(results["max_response_time"], response_time)
                else:
                    results["failed_requests"] += 1
                    results["errors"].append(result["error"])
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=users) as executor:
            futures = [executor.submit(worker) for _ in range(users)]
            for future in futures:
                future.result()
        
        if results["successful_requests"] > 0:
            results["avg_response_time"] = results["total_duration"] / results["successful_requests"]
        if results["min_response_time"] == float('inf'):
            results["min_response_time"] = 0
            
        return results

    def run_performance_tests(self) -> Dict:
        """Run all performance tests."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "system_resources": {},
            "endpoints": {},
            "load_tests": {},
            "summary": {
                "total_endpoints": len(self.config["endpoints"]),
                "passed_endpoints": 0,
                "failed_endpoints": 0
            }
        }
        
        # Test each endpoint
        for name, url in self.config["endpoints"].items():
            logger.info(f"Testing endpoint: {name}")
            
            # Measure initial system resources
            initial_resources = self.measure_system_resources()
            
            # Run basic endpoint test
            endpoint_result = self.test_endpoint(url)
            
            # Run load tests
            load_test_results = {}
            for users in self.config["load_test"]["concurrent_users"]:
                logger.info(f"Running load test with {users} users")
                load_test_results[users] = self.run_load_test(
                    url,
                    users,
                    self.config["load_test"]["duration_seconds"]
                )
            
            # Measure final system resources
            final_resources = self.measure_system_resources()
            
            results["endpoints"][name] = {
                "basic_test": endpoint_result,
                "load_tests": load_test_results,
                "resource_impact": {
                    "cpu_increase": final_resources["cpu"]["percent"] - initial_resources["cpu"]["percent"],
                    "memory_increase": final_resources["memory"]["percent"] - initial_resources["memory"]["percent"]
                }
            }
            
            # Update summary
            if endpoint_result["success"]:
                results["summary"]["passed_endpoints"] += 1
            else:
                results["summary"]["failed_endpoints"] += 1
        
        self.results = results
        return results

    def generate_report(self, output_format: str = "text") -> str:
        """Generate a performance test report."""
        if not self.results:
            self.run_performance_tests()
            
        if output_format == "json":
            return json.dumps(self.results, indent=2)
            
        elif output_format == "text":
            report = []
            report.append("Performance Test Results")
            report.append(f"Generated: {self.results['timestamp']}")
            
            report.append("\nSummary:")
            report.append(f"Total Endpoints: {self.results['summary']['total_endpoints']}")
            report.append(f"Passed: {self.results['summary']['passed_endpoints']}")
            report.append(f"Failed: {self.results['summary']['failed_endpoints']}")
            
            for name, endpoint_results in self.results["endpoints"].items():
                report.append(f"\n{name} Endpoint:")
                basic_test = endpoint_results["basic_test"]
                report.append(f"Basic Test: {'PASS' if basic_test['success'] else 'FAIL'}")
                if basic_test["response_time"]:
                    report.append(f"Response Time: {basic_test['response_time']:.3f}s")
                if basic_test["error"]:
                    report.append(f"Error: {basic_test['error']}")
                
                report.append("\nLoad Tests:")
                for users, load_test in endpoint_results["load_tests"].items():
                    report.append(f"\n  {users} Concurrent Users:")
                    report.append(f"  Total Requests: {load_test['total_requests']}")
                    report.append(f"  Successful: {load_test['successful_requests']}")
                    report.append(f"  Failed: {load_test['failed_requests']}")
                    report.append(f"  Avg Response Time: {load_test['avg_response_time']:.3f}s")
                    report.append(f"  Min Response Time: {load_test['min_response_time']:.3f}s")
                    report.append(f"  Max Response Time: {load_test['max_response_time']:.3f}s")
                
                report.append("\nResource Impact:")
                report.append(f"  CPU Increase: {endpoint_results['resource_impact']['cpu_increase']:.1f}%")
                report.append(f"  Memory Increase: {endpoint_results['resource_impact']['memory_increase']:.1f}%")
            
            return "\n".join(report)
            
        elif output_format == "html":
            html = [
                "<html>",
                "<head>",
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                ".pass { color: green; }",
                ".fail { color: red; }",
                ".warning { color: orange; }",
                ".endpoint { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }",
                ".load-test { margin: 10px 0; }",
                "</style>",
                "</head>",
                "<body>",
                "<h1>Performance Test Results</h1>",
                f"<p>Generated: {self.results['timestamp']}</p>"
            ]
            
            # Summary
            html.append("<h2>Summary</h2>")
            html.append("<ul>")
            html.append(f"<li>Total Endpoints: {self.results['summary']['total_endpoints']}</li>")
            html.append(f"<li>Passed: <span class='pass'>{self.results['summary']['passed_endpoints']}</span></li>")
            html.append(f"<li>Failed: <span class='fail'>{self.results['summary']['failed_endpoints']}</span></li>")
            html.append("</ul>")
            
            # Endpoints
            for name, endpoint_results in self.results["endpoints"].items():
                html.append(f'<div class="endpoint">')
                html.append(f"<h3>{name} Endpoint</h3>")
                
                basic_test = endpoint_results["basic_test"]
                status_class = "pass" if basic_test["success"] else "fail"
                html.append(f"<p>Basic Test: <span class='{status_class}'>{'PASS' if basic_test['success'] else 'FAIL'}</span></p>")
                if basic_test["response_time"]:
                    html.append(f"<p>Response Time: {basic_test['response_time']:.3f}s</p>")
                if basic_test["error"]:
                    html.append(f"<p class='fail'>Error: {basic_test['error']}</p>")
                
                html.append("<h4>Load Tests</h4>")
                for users, load_test in endpoint_results["load_tests"].items():
                    html.append(f'<div class="load-test">')
                    html.append(f"<h5>{users} Concurrent Users</h5>")
                    html.append("<ul>")
                    html.append(f"<li>Total Requests: {load_test['total_requests']}</li>")
                    html.append(f"<li>Successful: <span class='pass'>{load_test['successful_requests']}</span></li>")
                    html.append(f"<li>Failed: <span class='fail'>{load_test['failed_requests']}</span></li>")
                    html.append(f"<li>Avg Response Time: {load_test['avg_response_time']:.3f}s</li>")
                    html.append(f"<li>Min Response Time: {load_test['min_response_time']:.3f}s</li>")
                    html.append(f"<li>Max Response Time: {load_test['max_response_time']:.3f}s</li>")
                    html.append("</ul>")
                    html.append("</div>")
                
                html.append("<h4>Resource Impact</h4>")
                html.append("<ul>")
                cpu_increase = endpoint_results['resource_impact']['cpu_increase']
                memory_increase = endpoint_results['resource_impact']['memory_increase']
                cpu_class = 'warning' if cpu_increase > 20 else 'pass'
                memory_class = 'warning' if memory_increase > 20 else 'pass'
                html.append(f"<li>CPU Increase: <span class='{cpu_class}'>{cpu_increase:.1f}%</span></li>")
                html.append(f"<li>Memory Increase: <span class='{memory_class}'>{memory_increase:.1f}%</span></li>")
                html.append("</ul>")
                
                html.append("</div>")
            
            html.extend(["</body>", "</html>"])
            return "\n".join(html)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def save_report(self, output_dir: str = "reports") -> None:
        """Save performance test results in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON report
        with open(f"{output_dir}/performance_test_{timestamp}.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Save text report
        with open(f"{output_dir}/performance_test_{timestamp}.txt", "w") as f:
            f.write(self.generate_report("text"))
        
        # Save HTML report
        with open(f"{output_dir}/performance_test_{timestamp}.html", "w") as f:
            f.write(self.generate_report("html"))

def main():
    tester = PerformanceTester()
    
    # Run performance tests
    tester.run_performance_tests()
    
    # Generate and print text report
    print(tester.generate_report("text"))
    
    # Save reports in all formats
    tester.save_report()
    
    # Exit with appropriate status code
    if tester.results["summary"]["failed_endpoints"] > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main() 