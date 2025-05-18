#!/usr/bin/env python3
"""
AI Feature Testing Script
This script tests AI-specific features and functionality
"""

import os
import sys
import logging
import json
import time
import requests
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_testing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class AITester:
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {},
            "overall_status": "pending"
        }
        self.ai_endpoint = "http://localhost:8001/ai"
        self.test_data = self._load_test_data()

    def _load_test_data(self) -> Dict:
        """Load test data from file"""
        test_data_path = Path("tests/data/ai_test_data.json")
        if test_data_path.exists():
            with open(test_data_path) as f:
                return json.load(f)
        return {
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
        }

    def test_model_loading(self) -> Dict:
        """Test model loading and initialization"""
        try:
            response = requests.get(f"{self.ai_endpoint}/model/status")
            return {
                "status": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "model_status": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def test_inference(self) -> Dict:
        """Test model inference with various inputs"""
        results = {}
        for prompt in self.test_data["prompts"]:
            try:
                response = requests.post(
                    f"{self.ai_endpoint}/generate",
                    json={"prompt": prompt}
                )
                results[prompt] = {
                    "status": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "output_length": len(response.json().get("output", ""))
                }
            except requests.exceptions.RequestException as e:
                results[prompt] = {"error": str(e)}
        return results

    def test_batch_processing(self) -> Dict:
        """Test batch processing capability"""
        try:
            response = requests.post(
                f"{self.ai_endpoint}/batch",
                json={"prompts": self.test_data["prompts"]}
            )
            return {
                "status": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "batch_size": len(self.test_data["prompts"]),
                "outputs_received": len(response.json().get("outputs", []))
            }
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def test_format_handling(self) -> Dict:
        """Test different output format handling"""
        results = {}
        for fmt in self.test_data["expected_formats"]:
            try:
                response = requests.post(
                    f"{self.ai_endpoint}/generate",
                    json={
                        "prompt": "Test prompt",
                        "output_format": fmt
                    }
                )
                results[fmt] = {
                    "status": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "format_matched": self._verify_format(
                        response.json().get("output", ""),
                        fmt
                    )
                }
            except requests.exceptions.RequestException as e:
                results[fmt] = {"error": str(e)}
        return results

    def _verify_format(self, output: str, expected_format: str) -> bool:
        """Verify output format matches expected format"""
        if expected_format == "json":
            try:
                json.loads(output)
                return True
            except json.JSONDecodeError:
                return False
        elif expected_format == "markdown":
            # Basic markdown check (presence of markdown syntax)
            return any(marker in output for marker in ["#", "*", "_", "`", "-"])
        return True  # Default for text format

    def test_error_handling(self) -> Dict:
        """Test error handling with invalid inputs"""
        test_cases = [
            {"case": "empty_prompt", "data": {"prompt": ""}},
            {"case": "long_prompt", "data": {"prompt": "x" * 10000}},
            {"case": "invalid_format", "data": {"prompt": "test", "format": "invalid"}},
            {"case": "missing_prompt", "data": {}}
        ]

        results = {}
        for test in test_cases:
            try:
                response = requests.post(
                    f"{self.ai_endpoint}/generate",
                    json=test["data"]
                )
                results[test["case"]] = {
                    "status": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "error_handled": response.status_code != 200
                }
            except requests.exceptions.RequestException as e:
                results[test["case"]] = {"error": str(e)}
        return results

    def test_performance(self) -> Dict:
        """Test model performance metrics"""
        try:
            response = requests.get(f"{self.ai_endpoint}/metrics")
            return {
                "status": response.status_code,
                "response_time": response.elapsed.total_seconds(),
                "metrics": response.json()
            }
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def run_tests(self):
        """Run all AI feature tests"""
        logger.info("Starting AI feature tests")

        # Test model loading
        self.results["tests"]["model_loading"] = self.test_model_loading()

        # Test inference
        self.results["tests"]["inference"] = self.test_inference()

        # Test batch processing
        self.results["tests"]["batch_processing"] = self.test_batch_processing()

        # Test format handling
        self.results["tests"]["format_handling"] = self.test_format_handling()

        # Test error handling
        self.results["tests"]["error_handling"] = self.test_error_handling()

        # Test performance
        self.results["tests"]["performance"] = self.test_performance()

        # Update overall status
        self._update_overall_status()

        # Save results
        self._save_results()

        logger.info("AI feature tests completed")
        return self.results

    def _update_overall_status(self):
        """Update the overall status based on test results"""
        statuses = []
        for test_suite in self.results["tests"].values():
            if isinstance(test_suite, dict):
                status = test_suite.get("status")
                if isinstance(status, int):
                    statuses.append(200 <= status < 300)
                elif isinstance(status, str):
                    statuses.append(status == "success")

        if not statuses:
            self.results["overall_status"] = "unknown"
        elif all(statuses):
            self.results["overall_status"] = "success"
        elif any(statuses):
            self.results["overall_status"] = "partial"
        else:
            self.results["overall_status"] = "failure"

    def _save_results(self):
        """Save test results to file"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"ai_test_results_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {output_file}")

def main():
    """Main function"""
    try:
        tester = AITester()
        results = tester.run_tests()

        # Print summary
        print("\nAI Feature Test Summary:")
        print(f"Overall Status: {results['overall_status']}")
        print("\nTest Results:")
        for test_name, test_results in results["tests"].items():
            print(f"\n{test_name.upper()}:")
            if isinstance(test_results, dict):
                for key, value in test_results.items():
                    if key != "metrics":  # Skip detailed metrics in summary
                        print(f"  {key}: {value}")

    except Exception as e:
        logger.error(f"AI feature tests failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
