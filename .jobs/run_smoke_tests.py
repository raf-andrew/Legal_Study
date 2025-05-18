import requests
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmokeTestRunner:
    def __init__(self, config_path: str = "config/smoke_tests.json"):
        self.config = self._load_config(config_path)
        self.results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "api_tests": [
                    {
                        "name": "Health Check",
                        "endpoint": "/health",
                        "method": "GET",
                        "expected_status": 200
                    },
                    {
                        "name": "API Version",
                        "endpoint": "/version",
                        "method": "GET",
                        "expected_status": 200
                    }
                ],
                "ai_tests": [
                    {
                        "name": "Model Health",
                        "endpoint": "/ai/health",
                        "method": "GET",
                        "expected_status": 200
                    },
                    {
                        "name": "Basic Inference",
                        "endpoint": "/ai/infer",
                        "method": "POST",
                        "payload": {"text": "test"},
                        "expected_status": 200
                    }
                ],
                "notification_tests": [
                    {
                        "name": "Notification Service Health",
                        "endpoint": "/notifications/health",
                        "method": "GET",
                        "expected_status": 200
                    }
                ],
                "base_url": "http://localhost:8000"
            }

    def run_api_test(self, test: Dict) -> Dict:
        url = f"{self.config['base_url']}{test['endpoint']}"
        method = test['method'].lower()
        try:
            if method == 'get':
                response = requests.get(url, timeout=5)
            elif method == 'post':
                response = requests.post(url, json=test.get('payload', {}), timeout=5)
            else:
                return {
                    "status": False,
                    "error": f"Unsupported method: {method}"
                }

            return {
                "status": response.status_code == test['expected_status'],
                "response_time": response.elapsed.total_seconds(),
                "status_code": response.status_code,
                "response": response.json() if response.headers.get('content-type') == 'application/json' else None
            }
        except Exception as e:
            return {
                "status": False,
                "error": str(e)
            }

    def run_smoke_tests(self) -> Dict:
        results = {
            "timestamp": datetime.now().isoformat(),
            "api_tests": {},
            "ai_tests": {},
            "notification_tests": {},
            "overall_status": "pass"
        }

        with ThreadPoolExecutor() as executor:
            # Run API tests
            api_futures = {
                test["name"]: executor.submit(self.run_api_test, test)
                for test in self.config["api_tests"]
            }
            for name, future in api_futures.items():
                results["api_tests"][name] = future.result()

            # Run AI tests
            ai_futures = {
                test["name"]: executor.submit(self.run_api_test, test)
                for test in self.config["ai_tests"]
            }
            for name, future in ai_futures.items():
                results["ai_tests"][name] = future.result()

            # Run notification tests
            notification_futures = {
                test["name"]: executor.submit(self.run_api_test, test)
                for test in self.config["notification_tests"]
            }
            for name, future in notification_futures.items():
                results["notification_tests"][name] = future.result()

        # Evaluate overall status
        for category in ["api_tests", "ai_tests", "notification_tests"]:
            if any(not test["status"] for test in results[category].values()):
                results["overall_status"] = "fail"
                break

        self.results = results
        return results

    def generate_report(self, output_format: str = "text") -> str:
        if not self.results:
            self.run_smoke_tests()

        if output_format == "json":
            return json.dumps(self.results, indent=2)
        elif output_format == "text":
            report = []
            report.append(f"Smoke Test Report - {self.results['timestamp']}")
            report.append(f"Overall Status: {self.results['overall_status'].upper()}")

            for category in ["api_tests", "ai_tests", "notification_tests"]:
                report.append(f"\n{category.replace('_', ' ').title()}:")
                for name, result in self.results[category].items():
                    status_symbol = "✓" if result["status"] else "✗"
                    error_msg = f" - {result.get('error', '')}" if not result["status"] else ""
                    report.append(f"  {name}: {status_symbol}{error_msg}")
                    if result["status"]:
                        report.append(f"    Response Time: {result['response_time']:.3f}s")

            return "\n".join(report)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

def main():
    runner = SmokeTestRunner()
    report = runner.generate_report("text")
    print(report)
    
    # Save detailed JSON report
    with open(f"reports/smoke_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(runner.results, f, indent=2)
    
    # Exit with appropriate status code
    sys.exit(0 if runner.results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main() 