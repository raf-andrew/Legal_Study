import requests
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIFeatureTester:
    def __init__(self, config_path: str = "config/ai_tests.json"):
        self.config = self._load_config(config_path)
        self.results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "base_url": "http://localhost:8000",
                "tests": {
                    "model_health": {
                        "endpoint": "/ai/health",
                        "method": "GET",
                        "expected_status": 200
                    },
                    "basic_inference": {
                        "endpoint": "/ai/infer",
                        "method": "POST",
                        "payload": {
                            "text": "This is a test input for inference."
                        },
                        "expected_status": 200
                    },
                    "batch_inference": {
                        "endpoint": "/ai/batch-infer",
                        "method": "POST",
                        "payload": {
                            "texts": [
                                "First test input",
                                "Second test input",
                                "Third test input"
                            ]
                        },
                        "expected_status": 200
                    },
                    "model_metrics": {
                        "endpoint": "/ai/metrics",
                        "method": "GET",
                        "expected_status": 200
                    }
                },
                "performance_thresholds": {
                    "response_time": 1.0,
                    "batch_response_time": 2.0
                }
            }

    def run_test(self, name: str, test_config: Dict) -> Dict:
        url = f"{self.config['base_url']}{test_config['endpoint']}"
        method = test_config['method'].lower()
        
        try:
            start_time = time.time()
            
            if method == 'get':
                response = requests.get(url, timeout=10)
            elif method == 'post':
                response = requests.post(url, json=test_config['payload'], timeout=10)
            else:
                return {
                    "status": False,
                    "error": f"Unsupported method: {method}"
                }
            
            response_time = time.time() - start_time
            
            result = {
                "status": response.status_code == test_config['expected_status'],
                "response_time": response_time,
                "status_code": response.status_code
            }
            
            if response.headers.get('content-type') == 'application/json':
                result["response"] = response.json()
            
            # Check performance thresholds
            if name == "batch_inference":
                if response_time > self.config["performance_thresholds"]["batch_response_time"]:
                    result["performance_warning"] = f"Batch inference took {response_time:.2f}s (threshold: {self.config['performance_thresholds']['batch_response_time']}s)"
            else:
                if response_time > self.config["performance_thresholds"]["response_time"]:
                    result["performance_warning"] = f"Response took {response_time:.2f}s (threshold: {self.config['performance_thresholds']['response_time']}s)"
            
            return result
            
        except Exception as e:
            return {
                "status": False,
                "error": str(e)
            }

    def run_all_tests(self) -> Dict:
        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "pass",
            "warnings": []
        }

        with ThreadPoolExecutor() as executor:
            futures = {
                name: executor.submit(self.run_test, name, test_config)
                for name, test_config in self.config["tests"].items()
            }
            
            for name, future in futures.items():
                test_result = future.result()
                results["tests"][name] = test_result
                
                if not test_result["status"]:
                    results["overall_status"] = "fail"
                
                if "performance_warning" in test_result:
                    results["warnings"].append(f"{name}: {test_result['performance_warning']}")

        self.results = results
        return results

    def generate_report(self, output_format: str = "text") -> str:
        if not self.results:
            self.run_all_tests()

        if output_format == "json":
            return json.dumps(self.results, indent=2)
        elif output_format == "text":
            report = []
            report.append(f"AI Features Test Report - {self.results['timestamp']}")
            report.append(f"Overall Status: {self.results['overall_status'].upper()}")
            
            for name, result in self.results["tests"].items():
                status_symbol = "✓" if result["status"] else "✗"
                error_msg = f" - {result.get('error', '')}" if not result["status"] else ""
                report.append(f"\n{name}: {status_symbol}{error_msg}")
                
                if result["status"]:
                    report.append(f"  Response Time: {result['response_time']:.3f}s")
                    if "performance_warning" in result:
                        report.append(f"  ⚠ {result['performance_warning']}")
                    
                    if "response" in result:
                        report.append("  Response Data:")
                        for key, value in result["response"].items():
                            report.append(f"    {key}: {value}")
            
            if self.results["warnings"]:
                report.append("\nPerformance Warnings:")
                for warning in self.results["warnings"]:
                    report.append(f"  ⚠ {warning}")
            
            return "\n".join(report)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

def main():
    tester = AIFeatureTester()
    report = tester.generate_report("text")
    print(report)
    
    # Save detailed JSON report
    with open(f"reports/ai_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(tester.results, f, indent=2)
    
    # Exit with appropriate status code
    sys.exit(0 if tester.results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main() 