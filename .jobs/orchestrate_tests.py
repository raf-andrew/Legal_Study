import subprocess
import json
import logging
import os
import sys
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

class TestOrchestrator:
    def __init__(self, config_path: str = "config/test_orchestration.json"):
        self.config = self._load_config(config_path)
        self.results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "test_suites": {
                    "smoke": {
                        "script": "run_smoke_tests.py",
                        "priority": 1,
                        "required": True
                    },
                    "security": {
                        "script": "run_security_tests.py",
                        "priority": 2,
                        "required": True
                    },
                    "ai": {
                        "script": "test_ai_features.py",
                        "priority": 2,
                        "required": True
                    },
                    "notifications": {
                        "script": "test_notifications.py",
                        "priority": 2,
                        "required": True
                    },
                    "performance": {
                        "script": "run_performance_tests.py",
                        "priority": 3,
                        "required": False
                    },
                    "integration": {
                        "script": "run_integration_tests.py",
                        "priority": 3,
                        "required": True
                    }
                },
                "parallel_execution": True,
                "max_retries": 3,
                "retry_delay": 5,
                "report_formats": ["text", "json", "html"],
                "notification_webhook": None
            }

    def run_test_suite(self, name: str, config: Dict) -> Dict:
        """Run a single test suite with retries."""
        script = config["script"]
        retries = 0
        start_time = datetime.now()
        
        while retries < self.config["max_retries"]:
            try:
                logger.info(f"Running {name} test suite (attempt {retries + 1})")
                
                result = subprocess.run(
                    [sys.executable, script],
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Try to parse JSON output
                try:
                    output = json.loads(result.stdout)
                except json.JSONDecodeError:
                    output = result.stdout.strip()
                
                return {
                    "status": "pass" if result.returncode == 0 else "fail",
                    "output": output,
                    "error": result.stderr if result.stderr else None,
                    "duration": duration,
                    "attempts": retries + 1,
                    "timestamp": end_time.isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error running {name} test suite: {str(e)}")
                retries += 1
                if retries < self.config["max_retries"]:
                    time.sleep(self.config["retry_delay"])
        
        end_time = datetime.now()
        return {
            "status": "error",
            "error": f"Failed after {retries} attempts",
            "duration": (end_time - start_time).total_seconds(),
            "attempts": retries,
            "timestamp": end_time.isoformat()
        }

    def orchestrate_tests(self) -> Dict:
        """Run all test suites in order of priority."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_suites": len(self.config["test_suites"]),
                "passed_suites": 0,
                "failed_suites": 0,
                "error_suites": 0,
                "total_duration": 0
            },
            "suites": {}
        }
        
        # Sort test suites by priority
        sorted_suites = sorted(
            self.config["test_suites"].items(),
            key=lambda x: x[1]["priority"]
        )
        
        if self.config["parallel_execution"]:
            # Group tests by priority
            priority_groups = {}
            for name, config in sorted_suites:
                priority = config["priority"]
                if priority not in priority_groups:
                    priority_groups[priority] = []
                priority_groups[priority].append((name, config))
            
            # Run each priority group in parallel
            for priority in sorted(priority_groups.keys()):
                with ThreadPoolExecutor() as executor:
                    futures = {
                        name: executor.submit(self.run_test_suite, name, config)
                        for name, config in priority_groups[priority]
                    }
                    for name, future in futures.items():
                        results["suites"][name] = future.result()
                        
                        # Check if a required test failed
                        if (self.config["test_suites"][name]["required"] and 
                            results["suites"][name]["status"] != "pass"):
                            logger.error(f"Required test suite {name} failed")
                            return results
        else:
            # Run tests sequentially
            for name, config in sorted_suites:
                results["suites"][name] = self.run_test_suite(name, config)
                
                # Check if a required test failed
                if (config["required"] and 
                    results["suites"][name]["status"] != "pass"):
                    logger.error(f"Required test suite {name} failed")
                    break
        
        # Update summary
        for suite_result in results["suites"].values():
            if suite_result["status"] == "pass":
                results["summary"]["passed_suites"] += 1
            elif suite_result["status"] == "fail":
                results["summary"]["failed_suites"] += 1
            else:
                results["summary"]["error_suites"] += 1
            results["summary"]["total_duration"] += suite_result["duration"]
        
        self.results = results
        return results

    def generate_report(self, output_format: str = "text") -> str:
        """Generate a test orchestration report."""
        if not self.results:
            self.orchestrate_tests()
            
        if output_format == "json":
            return json.dumps(self.results, indent=2)
            
        elif output_format == "text":
            report = []
            report.append("Test Orchestration Results")
            report.append(f"Generated: {self.results['timestamp']}")
            
            report.append("\nSummary:")
            report.append(f"Total Suites: {self.results['summary']['total_suites']}")
            report.append(f"Passed: {self.results['summary']['passed_suites']}")
            report.append(f"Failed: {self.results['summary']['failed_suites']}")
            report.append(f"Errors: {self.results['summary']['error_suites']}")
            report.append(f"Total Duration: {self.results['summary']['total_duration']:.2f}s")
            
            for suite_name, suite_result in self.results["suites"].items():
                report.append(f"\n{suite_name.title()} Test Suite:")
                report.append(f"Status: {suite_result['status'].upper()}")
                report.append(f"Duration: {suite_result['duration']:.2f}s")
                report.append(f"Attempts: {suite_result['attempts']}")
                
                if suite_result["error"]:
                    report.append(f"Error: {suite_result['error']}")
                
                if isinstance(suite_result["output"], dict):
                    report.append("Output:")
                    for key, value in suite_result["output"].items():
                        report.append(f"  {key}: {value}")
                elif suite_result["output"]:
                    report.append(f"Output: {suite_result['output']}")
            
            return "\n".join(report)
            
        elif output_format == "html":
            html = [
                "<html>",
                "<head>",
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                ".pass { color: green; }",
                ".fail { color: red; }",
                ".error { color: orange; }",
                ".suite { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }",
                "</style>",
                "</head>",
                "<body>",
                "<h1>Test Orchestration Results</h1>",
                f"<p>Generated: {self.results['timestamp']}</p>"
            ]
            
            # Summary
            html.append("<h2>Summary</h2>")
            html.append("<ul>")
            html.append(f"<li>Total Suites: {self.results['summary']['total_suites']}</li>")
            html.append(f"<li>Passed: <span class='pass'>{self.results['summary']['passed_suites']}</span></li>")
            html.append(f"<li>Failed: <span class='fail'>{self.results['summary']['failed_suites']}</span></li>")
            html.append(f"<li>Errors: <span class='error'>{self.results['summary']['error_suites']}</span></li>")
            html.append(f"<li>Total Duration: {self.results['summary']['total_duration']:.2f}s</li>")
            html.append("</ul>")
            
            # Individual suites
            for suite_name, suite_result in self.results["suites"].items():
                html.append(f'<div class="suite">')
                html.append(f"<h3>{suite_name.title()} Test Suite</h3>")
                html.append(f"<p>Status: <span class='{suite_result['status']}'>{suite_result['status'].upper()}</span></p>")
                html.append(f"<p>Duration: {suite_result['duration']:.2f}s</p>")
                html.append(f"<p>Attempts: {suite_result['attempts']}</p>")
                
                if suite_result["error"]:
                    html.append(f"<p class='error'>Error: {suite_result['error']}</p>")
                
                if isinstance(suite_result["output"], dict):
                    html.append("<h4>Output:</h4>")
                    html.append("<ul>")
                    for key, value in suite_result["output"].items():
                        html.append(f"<li><strong>{key}:</strong> {value}</li>")
                    html.append("</ul>")
                elif suite_result["output"]:
                    html.append(f"<p>Output: {suite_result['output']}</p>")
                
                html.append("</div>")
            
            html.extend(["</body>", "</html>"])
            return "\n".join(html)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def save_report(self, output_dir: str = "reports") -> None:
        """Save test orchestration results in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(output_dir, exist_ok=True)
        
        for format in self.config["report_formats"]:
            filename = f"{output_dir}/test_orchestration_{timestamp}.{format}"
            content = self.generate_report(format)
            
            with open(filename, "w") as f:
                f.write(content)
            
            logger.info(f"Saved {format} report to {filename}")

def main():
    orchestrator = TestOrchestrator()
    
    # Run all test suites
    orchestrator.orchestrate_tests()
    
    # Generate and print text report
    print(orchestrator.generate_report("text"))
    
    # Save reports in configured formats
    orchestrator.save_report()
    
    # Exit with appropriate status code
    if (orchestrator.results["summary"]["failed_suites"] > 0 or
        orchestrator.results["summary"]["error_suites"] > 0):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main() 