import subprocess
import sys
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlatformBuilder:
    def __init__(self, config_path: str = "config/build_config.json"):
        self.config = self._load_config(config_path)
        self.results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "build_steps": [
                    {
                        "name": "lint",
                        "commands": [
                            "black .",
                            "flake8 .",
                            "mypy ."
                        ]
                    },
                    {
                        "name": "test",
                        "commands": [
                            "pytest tests/ --cov=. --cov-report=html:reports/coverage"
                        ]
                    },
                    {
                        "name": "build",
                        "commands": [
                            "python setup.py build",
                            "python setup.py sdist bdist_wheel"
                        ]
                    }
                ],
                "parallel_execution": True,
                "stop_on_failure": True,
                "artifacts": {
                    "build": "dist/",
                    "coverage": "reports/coverage/",
                    "logs": "logs/"
                }
            }

    def run_command(self, command: str) -> Dict:
        """Run a shell command and return the result."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            return {
                "status": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "return_code": result.returncode
            }
        except Exception as e:
            logger.error(f"Error running command '{command}': {str(e)}")
            return {
                "status": False,
                "error": str(e),
                "return_code": -1
            }

    def run_build_step(self, step: Dict) -> Dict:
        """Run all commands in a build step."""
        results = []
        for command in step["commands"]:
            logger.info(f"Running command: {command}")
            result = self.run_command(command)
            results.append(result)
            
            if not result["status"] and self.config["stop_on_failure"]:
                logger.error(f"Build step '{step['name']}' failed. Stopping.")
                break
        
        return {
            "name": step["name"],
            "status": all(r["status"] for r in results),
            "commands": [{"command": cmd, "result": res} for cmd, res in zip(step["commands"], results)]
        }

    def create_artifact_directories(self) -> None:
        """Create directories for build artifacts."""
        for path in self.config["artifacts"].values():
            Path(path).mkdir(parents=True, exist_ok=True)

    def build_platform(self) -> Dict:
        """Run the complete build process."""
        self.create_artifact_directories()
        
        build_steps = self.config["build_steps"]
        results = []
        
        if self.config["parallel_execution"]:
            with ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(self.run_build_step, step): step["name"]
                    for step in build_steps
                }
                for future in futures:
                    results.append(future.result())
        else:
            for step in build_steps:
                result = self.run_build_step(step)
                results.append(result)
                if not result["status"] and self.config["stop_on_failure"]:
                    break
        
        # Check overall status
        overall_status = all(step["status"] for step in results)
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "status": "success" if overall_status else "failure",
            "steps": {step["name"]: step for step in results}
        }
        
        return self.results

    def generate_report(self, output_format: str = "text") -> str:
        """Generate a build report in the specified format."""
        if not self.results:
            self.build_platform()
            
        if output_format == "json":
            return json.dumps(self.results, indent=2)
        elif output_format == "text":
            report = []
            report.append(f"Platform Build Report - {self.results['timestamp']}")
            report.append(f"Overall Status: {self.results['status'].upper()}")
            
            for step_name, step in self.results["steps"].items():
                status_symbol = "✓" if step["status"] else "✗"
                report.append(f"\n{step_name}:")
                report.append(f"  Status: {status_symbol}")
                
                for cmd_result in step["commands"]:
                    cmd_status = "✓" if cmd_result["result"]["status"] else "✗"
                    report.append(f"  {cmd_result['command']}: {cmd_status}")
                    if not cmd_result["result"]["status"]:
                        if cmd_result["result"].get("error"):
                            report.append(f"    Error: {cmd_result['result']['error']}")
                        if cmd_result["result"].get("output"):
                            report.append(f"    Output: {cmd_result['result']['output']}")
            
            return "\n".join(report)
        elif output_format == "html":
            html = [
                "<html>",
                "<head>",
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                ".success { color: green; }",
                ".failure { color: red; }",
                ".step { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }",
                ".command { margin: 10px 0; padding: 5px; background-color: #f5f5f5; }",
                "</style>",
                "</head>",
                "<body>",
                f"<h1>Platform Build Report - {self.results['timestamp']}</h1>",
                f"<h2>Overall Status: <span class='{self.results['status']}'>{self.results['status'].upper()}</span></h2>"
            ]
            
            for step_name, step in self.results["steps"].items():
                status_class = "success" if step["status"] else "failure"
                html.append(f"<div class='step'>")
                html.append(f"<h3>{step_name}: <span class='{status_class}'>{'✓' if step['status'] else '✗'}</span></h3>")
                
                for cmd_result in step["commands"]:
                    cmd_status_class = "success" if cmd_result["result"]["status"] else "failure"
                    html.append(f"<div class='command'>")
                    html.append(f"<p>{cmd_result['command']}: <span class='{cmd_status_class}'>{'✓' if cmd_result['result']['status'] else '✗'}</span></p>")
                    
                    if not cmd_result["result"]["status"]:
                        if cmd_result["result"].get("error"):
                            html.append(f"<pre class='failure'>{cmd_result['result']['error']}</pre>")
                        if cmd_result["result"].get("output"):
                            html.append(f"<pre>{cmd_result['result']['output']}</pre>")
                    
                    html.append("</div>")
                
                html.append("</div>")
            
            html.extend(["</body>", "</html>"])
            return "\n".join(html)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

def main():
    # Create reports directory if it doesn't exist
    Path("reports").mkdir(exist_ok=True)
    
    # Run build process
    builder = PlatformBuilder()
    
    # Generate and print text report
    text_report = builder.generate_report("text")
    print(text_report)
    
    # Save JSON report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"reports/build_report_{timestamp}.json", "w") as f:
        json.dump(builder.results, f, indent=2)
    
    # Save HTML report
    html_report = builder.generate_report("html")
    with open(f"reports/build_report_{timestamp}.html", "w") as f:
        f.write(html_report)
    
    # Exit with appropriate status code
    sys.exit(0 if builder.results["status"] == "success" else 1)

if __name__ == "__main__":
    main() 