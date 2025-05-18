#!/usr/bin/env python3
"""
Platform Validation Script
This script orchestrates the complete platform validation process.
"""

import os
import sys
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
        logging.FileHandler('platform_validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class PlatformValidator:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "stages": {},
            "overall_status": "pending",
            "execution_time": 0,
            "summary": {}
        }
        
        # Define validation stages
        self.stages = [
            {
                "name": "environment_setup",
                "script": "setup_dev_environment.py",
                "required": True,
                "description": "Setting up development environment"
            },
            {
                "name": "smoke_tests",
                "script": "run_smoke_tests.py",
                "required": True,
                "description": "Running smoke tests"
            },
            {
                "name": "integration_tests",
                "script": "run_integration_tests.py",
                "required": True,
                "description": "Running integration tests"
            },
            {
                "name": "ai_tests",
                "script": "test_ai_features.py",
                "required": True,
                "description": "Testing AI features"
            },
            {
                "name": "notification_tests",
                "script": "test_notifications.py",
                "required": True,
                "description": "Testing notification system"
            },
            {
                "name": "error_handling",
                "script": "test_error_handling.py",
                "required": True,
                "description": "Testing error handling"
            },
            {
                "name": "performance_tests",
                "script": "run_performance_tests.py",
                "required": False,
                "description": "Running performance tests"
            },
            {
                "name": "security_tests",
                "script": "run_security_tests.py",
                "required": True,
                "description": "Running security tests"
            },
            {
                "name": "monitoring_setup",
                "script": "setup_monitoring.py",
                "required": True,
                "description": "Setting up monitoring"
            }
        ]

    def run_stage(self, stage: Dict) -> Dict:
        """Run a validation stage"""
        logger.info(f"Starting stage: {stage['description']}")
        start_time = time.time()
        
        try:
            # Run the script
            result = subprocess.run(
                [sys.executable, f"scripts/{stage['script']}"],
                capture_output=True,
                text=True
            )
            
            execution_time = time.time() - start_time
            
            # Check if the script has JSON output
            try:
                import json
                output = json.loads(result.stdout)
            except:
                output = {
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            
            return {
                "status": "pass" if result.returncode == 0 else "fail",
                "execution_time": execution_time,
                "output": output,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            logger.error(f"Error in stage {stage['name']}: {e}")
            return {
                "status": "error",
                "execution_time": time.time() - start_time,
                "error": str(e)
            }

    def run_validation(self):
        """Run all validation stages"""
        start_time = time.time()
        
        # Run stages
        for stage in self.stages:
            self.results["stages"][stage["name"]] = self.run_stage(stage)
            
            # Stop if a required stage fails
            if (stage["required"] and 
                self.results["stages"][stage["name"]]["status"] != "pass"):
                logger.error(f"Required stage {stage['name']} failed. Stopping validation.")
                # Mark remaining stages as skipped
                for remaining_stage in self.stages:
                    if remaining_stage["name"] not in self.results["stages"]:
                        self.results["stages"][remaining_stage["name"]] = {
                            "status": "skipped",
                            "execution_time": 0,
                            "error": "Previous required stage failed"
                        }
                break
        
        self.results["execution_time"] = time.time() - start_time
        
        # Calculate overall status
        failed_stages = [
            stage["name"] for stage in self.stages
            if stage["required"] and
            self.results["stages"][stage["name"]]["status"] not in ["pass", "skipped"]
        ]
        self.results["overall_status"] = "fail" if failed_stages else "pass"
        
        # Generate summary
        self.generate_summary()
        
        return self.results

    def generate_summary(self):
        """Generate validation summary"""
        total_stages = len(self.stages)
        passed_stages = sum(
            1 for stage in self.results["stages"].values()
            if stage["status"] == "pass"
        )
        failed_stages = sum(
            1 for stage in self.results["stages"].values()
            if stage["status"] == "fail"
        )
        error_stages = sum(
            1 for stage in self.results["stages"].values()
            if stage["status"] == "error"
        )
        skipped_stages = sum(
            1 for stage in self.results["stages"].values()
            if stage["status"] == "skipped"
        )
        
        self.results["summary"] = {
            "total_stages": total_stages,
            "passed_stages": passed_stages,
            "failed_stages": failed_stages,
            "error_stages": error_stages,
            "skipped_stages": skipped_stages,
            "success_rate": (passed_stages / (total_stages - skipped_stages)) * 100 if total_stages > skipped_stages else 0,
            "execution_time": self.results["execution_time"]
        }

    def save_results(self):
        """Save validation results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"validation_results/platform_validation_{timestamp}.json"
        
        os.makedirs("validation_results", exist_ok=True)
        with open(results_file, 'w') as f:
            import json
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")

    def generate_report(self) -> str:
        """Generate a human-readable validation report"""
        report = f"""
Platform Validation Report
========================
Generated at: {self.results['timestamp']}
Overall Status: {self.results['overall_status'].upper()}
Total Execution Time: {self.results['execution_time']:.2f} seconds

Summary:
--------
Total Stages: {self.results['summary']['total_stages']}
Passed Stages: {self.results['summary']['passed_stages']}
Failed Stages: {self.results['summary']['failed_stages']}
Error Stages: {self.results['summary']['error_stages']}
Skipped Stages: {self.results['summary']['skipped_stages']}
Success Rate: {self.results['summary']['success_rate']:.2f}%

Detailed Results:
---------------
"""
        
        for stage in self.stages:
            stage_result = self.results["stages"][stage["name"]]
            report += f"\n{stage['description'].upper()}:"
            report += f"\n  Status: {stage_result['status'].upper()}"
            if stage_result["status"] != "skipped":
                report += f"\n  Execution Time: {stage_result['execution_time']:.2f} seconds"
            
            if stage_result.get("error"):
                report += f"\n  Error: {stage_result['error']}"
            
            report += "\n"
        
        return report

def main():
    validator = PlatformValidator()
    results = validator.run_validation()
    validator.save_results()
    
    # Print report
    print(validator.generate_report())
    
    # Exit with appropriate status code
    sys.exit(0 if results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main() 