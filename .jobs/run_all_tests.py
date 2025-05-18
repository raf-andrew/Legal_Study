import subprocess
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestSuiteRunner:
    def __init__(self):
        self.test_suites = {
            "smoke": "run_smoke_tests.py",
            "ai": "test_ai_features.py",
            "notifications": "test_notifications.py",
            "platform": "verify_platform_health.py",
            "integration": "run_integration_tests.py",
            "parallel": "run_parallel_tests.py"
        }
        self.results = {}
        
    def run_test_suite(self, name: str, script: str) -> Dict:
        """Run a single test suite and return results."""
        try:
            logger.info(f"Running {name} test suite...")
            start_time = datetime.now()
            
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
                "timestamp": end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error running {name} test suite: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "duration": 0,
                "timestamp": datetime.now().isoformat()
            }

    def run_all_suites(self, parallel: bool = True) -> Dict:
        """Run all test suites and collect results."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "suites": {},
            "summary": {
                "total_suites": len(self.test_suites),
                "passed_suites": 0,
                "failed_suites": 0,
                "error_suites": 0,
                "total_duration": 0
            }
        }
        
        if parallel:
            with ThreadPoolExecutor() as executor:
                futures = {
                    name: executor.submit(self.run_test_suite, name, script)
                    for name, script in self.test_suites.items()
                }
                for name, future in futures.items():
                    results["suites"][name] = future.result()
        else:
            for name, script in self.test_suites.items():
                results["suites"][name] = self.run_test_suite(name, script)
        
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
        """Generate a test results report."""
        if not self.results:
            self.run_all_suites()
            
        if output_format == "json":
            return json.dumps(self.results, indent=2)
            
        elif output_format == "text":
            report = []
            report.append("Test Suite Results")
            report.append(f"Generated: {self.results['timestamp']}")
            report.append(f"\nSummary:")
            report.append(f"Total Suites: {self.results['summary']['total_suites']}")
            report.append(f"Passed: {self.results['summary']['passed_suites']}")
            report.append(f"Failed: {self.results['summary']['failed_suites']}")
            report.append(f"Errors: {self.results['summary']['error_suites']}")
            report.append(f"Total Duration: {self.results['summary']['total_duration']:.2f}s")
            
            for suite_name, suite_result in self.results["suites"].items():
                report.append(f"\n{suite_name.title()} Test Suite")
                report.append(f"Status: {suite_result['status'].upper()}")
                report.append(f"Duration: {suite_result['duration']:.2f}s")
                
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
                "<h1>Test Suite Results</h1>",
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
                
                if suite_result["error"]:
                    html.append(f"<p>Error: <span class='error'>{suite_result['error']}</span></p>")
                
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
        """Save test results in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON report
        with open(f"{output_dir}/test_results_{timestamp}.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Save text report
        with open(f"{output_dir}/test_results_{timestamp}.txt", "w") as f:
            f.write(self.generate_report("text"))
        
        # Save HTML report
        with open(f"{output_dir}/test_results_{timestamp}.html", "w") as f:
            f.write(self.generate_report("html"))

def main():
    runner = TestSuiteRunner()
    
    # Run all test suites
    runner.run_all_suites()
    
    # Generate and print text report
    print(runner.generate_report("text"))
    
    # Save reports in all formats
    runner.save_report()
    
    # Exit with appropriate status code
    if runner.results["summary"]["failed_suites"] > 0 or runner.results["summary"]["error_suites"] > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main() 