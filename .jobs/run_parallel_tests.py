import subprocess
import json
import logging
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

class ParallelTestRunner:
    def __init__(self):
        self.test_scripts = {
            "health": "verify_platform_health.py",
            "smoke": "run_smoke_tests.py",
            "ai": "test_ai_features.py",
            "notifications": "test_notifications.py",
            "integration": "run_integration_tests.py",
            "performance": "run_performance_tests.py"
        }
        self.results = {}
        
    def run_test_script(self, name: str, script: str) -> Dict:
        try:
            logger.info(f"Running {name} tests...")
            result = subprocess.run(
                [sys.executable, script],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            # Try to parse JSON output if available
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError:
                output = result.stdout.strip()
            
            return {
                "status": result.returncode == 0,
                "output": output,
                "error": result.stderr if result.stderr else None,
                "return_code": result.returncode
            }
        except Exception as e:
            logger.error(f"Error running {name} tests: {str(e)}")
            return {
                "status": False,
                "error": str(e),
                "return_code": -1
            }

    def run_all_tests(self, parallel: bool = True) -> Dict:
        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "pass"
        }
        
        if parallel:
            with ThreadPoolExecutor() as executor:
                futures = {
                    name: executor.submit(self.run_test_script, name, script)
                    for name, script in self.test_scripts.items()
                }
                for name, future in futures.items():
                    results["tests"][name] = future.result()
        else:
            for name, script in self.test_scripts.items():
                results["tests"][name] = self.run_test_script(name, script)
        
        # Evaluate overall status
        if any(not test["status"] for test in results["tests"].values()):
            results["overall_status"] = "fail"
        
        self.results = results
        return results

    def generate_report(self, output_format: str = "text") -> str:
        if not self.results:
            self.run_all_tests()

        if output_format == "json":
            return json.dumps(self.results, indent=2)
        elif output_format == "text":
            report = []
            report.append(f"Parallel Test Report - {self.results['timestamp']}")
            report.append(f"Overall Status: {self.results['overall_status'].upper()}")
            
            for name, result in self.results["tests"].items():
                status_symbol = "✓" if result["status"] else "✗"
                error_msg = f" - {result['error']}" if result.get("error") else ""
                report.append(f"\n{name.title()} Tests: {status_symbol}{error_msg}")
                
                if isinstance(result.get("output"), dict):
                    for key, value in result["output"].items():
                        report.append(f"  {key}: {value}")
                elif result.get("output"):
                    report.append(f"  {result['output']}")
            
            return "\n".join(report)
        elif output_format == "html":
            html = [
                "<html>",
                "<head>",
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                ".pass { color: green; }",
                ".fail { color: red; }",
                ".test-group { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }",
                "</style>",
                "</head>",
                "<body>",
                f"<h1>Parallel Test Report - {self.results['timestamp']}</h1>",
                f"<h2>Overall Status: <span class='{self.results['overall_status']}'>{self.results['overall_status'].upper()}</span></h2>"
            ]
            
            for name, result in self.results["tests"].items():
                status_class = "pass" if result["status"] else "fail"
                error_msg = f"<br><span class='fail'>{result['error']}</span>" if result.get("error") else ""
                html.append(f"<div class='test-group'>")
                html.append(f"<h3>{name.title()} Tests: <span class='{status_class}'>{'✓' if result['status'] else '✗'}</span>{error_msg}</h3>")
                
                if isinstance(result.get("output"), dict):
                    html.append("<ul>")
                    for key, value in result["output"].items():
                        html.append(f"<li><strong>{key}:</strong> {value}</li>")
                    html.append("</ul>")
                elif result.get("output"):
                    html.append(f"<pre>{result['output']}</pre>")
                
                html.append("</div>")
            
            html.extend(["</body>", "</html>"])
            return "\n".join(html)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

def main():
    # Create reports directory if it doesn't exist
    Path("reports").mkdir(exist_ok=True)
    
    # Run tests and generate reports
    runner = ParallelTestRunner()
    
    # Generate and print text report
    text_report = runner.generate_report("text")
    print(text_report)
    
    # Save JSON report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"reports/parallel_tests_{timestamp}.json", "w") as f:
        json.dump(runner.results, f, indent=2)
    
    # Save HTML report
    html_report = runner.generate_report("html")
    with open(f"reports/parallel_tests_{timestamp}.html", "w") as f:
        f.write(html_report)
    
    # Exit with appropriate status code
    sys.exit(0 if runner.results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main() 