#!/usr/bin/env python3
"""
Code Analysis Script
This script performs comprehensive code analysis and sniffing across the codebase
"""

import os
import sys
import logging
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('code_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "analyses": {},
            "overall_status": "pending"
        }
        self.report_dir = Path("analysis_reports")
        self.report_dir.mkdir(exist_ok=True)

    def setup_environment(self):
        """Set up analysis environment"""
        logger.info("Setting up analysis environment")
        try:
            # Install analysis tools if not present
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade",
                          "flake8", "pylint", "mypy", "bandit", "safety",
                          "black", "isort"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install analysis tools: {e}")
            return False

    def run_flake8(self, directory: str) -> Dict:
        """Run Flake8 for code style and syntax errors"""
        output_file = self.report_dir / "flake8_report.txt"
        try:
            result = subprocess.run(
                ["flake8", "--max-line-length=100", "--statistics",
                 "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s",
                 directory],
                capture_output=True,
                text=True
            )
            with open(output_file, 'w') as f:
                f.write(result.stdout)
            return {
                "status": "success" if result.returncode == 0 else "issues_found",
                "output_file": str(output_file),
                "error_count": len(result.stdout.splitlines())
            }
        except Exception as e:
            logger.error(f"Flake8 analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def run_pylint(self, directory: str) -> Dict:
        """Run Pylint for code quality analysis"""
        output_file = self.report_dir / "pylint_report.txt"
        try:
            result = subprocess.run(
                ["pylint", "--output-format=text", directory],
                capture_output=True,
                text=True
            )
            with open(output_file, 'w') as f:
                f.write(result.stdout)
            return {
                "status": "success" if result.returncode == 0 else "issues_found",
                "output_file": str(output_file),
                "score": self._extract_pylint_score(result.stdout)
            }
        except Exception as e:
            logger.error(f"Pylint analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def _extract_pylint_score(self, output: str) -> float:
        """Extract Pylint score from output"""
        try:
            for line in output.splitlines():
                if "Your code has been rated at" in line:
                    return float(line.split()[6].split('/')[0])
        except Exception:
            pass
        return 0.0

    def run_mypy(self, directory: str) -> Dict:
        """Run MyPy for type checking"""
        output_file = self.report_dir / "mypy_report.txt"
        try:
            result = subprocess.run(
                ["mypy", "--ignore-missing-imports", directory],
                capture_output=True,
                text=True
            )
            with open(output_file, 'w') as f:
                f.write(result.stdout)
            return {
                "status": "success" if result.returncode == 0 else "issues_found",
                "output_file": str(output_file),
                "error_count": len(result.stdout.splitlines())
            }
        except Exception as e:
            logger.error(f"MyPy analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def run_bandit(self, directory: str) -> Dict:
        """Run Bandit for security analysis"""
        output_file = self.report_dir / "bandit_report.json"
        try:
            result = subprocess.run(
                ["bandit", "-r", "-f", "json", directory],
                capture_output=True,
                text=True
            )
            with open(output_file, 'w') as f:
                f.write(result.stdout)
            report = json.loads(result.stdout)
            return {
                "status": "success" if result.returncode == 0 else "issues_found",
                "output_file": str(output_file),
                "metrics": report.get("metrics", {}),
                "issue_count": len(report.get("results", []))
            }
        except Exception as e:
            logger.error(f"Bandit analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def run_safety_check(self) -> Dict:
        """Run Safety check for dependency vulnerabilities"""
        output_file = self.report_dir / "safety_report.txt"
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True
            )
            with open(output_file, 'w') as f:
                f.write(result.stdout)
            vulnerabilities = json.loads(result.stdout)
            return {
                "status": "success" if result.returncode == 0 else "issues_found",
                "output_file": str(output_file),
                "vulnerability_count": len(vulnerabilities)
            }
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return {"status": "error", "error": str(e)}

    def check_code_formatting(self, directory: str) -> Dict:
        """Check code formatting with Black"""
        output_file = self.report_dir / "formatting_report.txt"
        try:
            result = subprocess.run(
                ["black", "--check", "--diff", directory],
                capture_output=True,
                text=True
            )
            with open(output_file, 'w') as f:
                f.write(result.stdout)
            return {
                "status": "success" if result.returncode == 0 else "issues_found",
                "output_file": str(output_file),
                "needs_formatting": result.returncode != 0
            }
        except Exception as e:
            logger.error(f"Code formatting check failed: {e}")
            return {"status": "error", "error": str(e)}

    def check_import_ordering(self, directory: str) -> Dict:
        """Check import ordering with isort"""
        output_file = self.report_dir / "import_order_report.txt"
        try:
            result = subprocess.run(
                ["isort", "--check-only", "--diff", directory],
                capture_output=True,
                text=True
            )
            with open(output_file, 'w') as f:
                f.write(result.stdout)
            return {
                "status": "success" if result.returncode == 0 else "issues_found",
                "output_file": str(output_file),
                "needs_reordering": result.returncode != 0
            }
        except Exception as e:
            logger.error(f"Import order check failed: {e}")
            return {"status": "error", "error": str(e)}

    def analyze_directory(self, directory: str):
        """Run all analyses on a directory"""
        logger.info(f"Analyzing directory: {directory}")

        self.results["analyses"] = {
            "flake8": self.run_flake8(directory),
            "pylint": self.run_pylint(directory),
            "mypy": self.run_mypy(directory),
            "bandit": self.run_bandit(directory),
            "safety": self.run_safety_check(),
            "formatting": self.check_code_formatting(directory),
            "imports": self.check_import_ordering(directory)
        }

        # Update overall status
        self._update_overall_status()

        # Generate summary report
        self._generate_summary_report()

        logger.info("Code analysis completed")
        return self.results

    def _update_overall_status(self):
        """Update the overall status based on all analyses"""
        statuses = [analysis["status"] for analysis in self.results["analyses"].values()]

        if not statuses:
            self.results["overall_status"] = "unknown"
        elif all(status == "success" for status in statuses):
            self.results["overall_status"] = "success"
        elif any(status == "error" for status in statuses):
            self.results["overall_status"] = "error"
        else:
            self.results["overall_status"] = "issues_found"

    def _generate_summary_report(self):
        """Generate a summary report of all analyses"""
        summary_file = self.report_dir / "analysis_summary.txt"

        summary = [
            "Code Analysis Summary Report",
            "==========================",
            f"Generated at: {self.results['timestamp']}",
            f"Overall Status: {self.results['overall_status'].upper()}",
            "",
            "Analysis Results:",
            "----------------"
        ]

        for tool, result in self.results["analyses"].items():
            summary.append(f"\n{tool.upper()}:")
            summary.append(f"  Status: {result['status']}")

            if tool == "pylint":
                summary.append(f"  Score: {result.get('score', 0.0)}/10.0")
            elif tool in ["flake8", "mypy"]:
                summary.append(f"  Error Count: {result.get('error_count', 0)}")
            elif tool == "bandit":
                summary.append(f"  Issue Count: {result.get('issue_count', 0)}")
            elif tool == "safety":
                summary.append(f"  Vulnerability Count: {result.get('vulnerability_count', 0)}")

            if result.get("error"):
                summary.append(f"  Error: {result['error']}")

        with open(summary_file, 'w') as f:
            f.write('\n'.join(summary))

def main():
    """Main function"""
    try:
        analyzer = CodeAnalyzer()

        # Setup environment
        if not analyzer.setup_environment():
            logger.error("Failed to set up analysis environment")
            sys.exit(1)

        # Run analysis on the project directory
        results = analyzer.analyze_directory(".")

        # Print summary
        with open(analyzer.report_dir / "analysis_summary.txt") as f:
            print(f.read())

        # Exit with appropriate status code
        sys.exit(0 if results["overall_status"] == "success" else 1)

    except Exception as e:
        logger.error(f"Code analysis failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
