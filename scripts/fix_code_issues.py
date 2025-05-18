#!/usr/bin/env python3
"""
Code Issue Fixer Script
This script helps fix issues found by the code analysis
"""

import os
import sys
import logging
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('code_fixing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CodeFixer:
    def __init__(self):
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fixes": {},
            "overall_status": "pending"
        }
        self.report_dir = Path("analysis_reports")
        self.backup_dir = Path("code_backups")
        self.backup_dir.mkdir(exist_ok=True)

    def backup_code(self, directory: str):
        """Create a backup of the code before fixing"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        try:
            import shutil
            shutil.copytree(directory, backup_path, ignore=shutil.ignore_patterns(
                '*.pyc', '__pycache__', '.git', 'venv', 'code_backups', 'analysis_reports'
            ))
            logger.info(f"Code backup created at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create code backup: {e}")
            return False

    def fix_formatting(self, directory: str) -> Dict:
        """Fix code formatting using Black"""
        try:
            result = subprocess.run(
                ["black", directory],
                capture_output=True,
                text=True
            )
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "error": result.stderr if result.stderr else None
            }
        except Exception as e:
            logger.error(f"Failed to fix formatting: {e}")
            return {"status": "error", "error": str(e)}

    def fix_imports(self, directory: str) -> Dict:
        """Fix import ordering using isort"""
        try:
            result = subprocess.run(
                ["isort", directory],
                capture_output=True,
                text=True
            )
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "error": result.stderr if result.stderr else None
            }
        except Exception as e:
            logger.error(f"Failed to fix imports: {e}")
            return {"status": "error", "error": str(e)}

    def apply_autopep8(self, directory: str) -> Dict:
        """Apply autopep8 fixes"""
        try:
            result = subprocess.run(
                ["autopep8", "--in-place", "--recursive", "--aggressive", "--aggressive", directory],
                capture_output=True,
                text=True
            )
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "error": result.stderr if result.stderr else None
            }
        except Exception as e:
            logger.error(f"Failed to apply autopep8: {e}")
            return {"status": "error", "error": str(e)}

    def fix_security_issues(self, directory: str) -> Dict:
        """Fix security issues found by Bandit"""
        # Read Bandit report
        try:
            with open(self.report_dir / "bandit_report.json") as f:
                report = json.load(f)

            fixes = []
            for result in report.get("results", []):
                fixes.append({
                    "file": result["filename"],
                    "line": result["line_number"],
                    "issue": result["issue_text"],
                    "severity": result["issue_severity"],
                    "confidence": result["issue_confidence"]
                })

            return {
                "status": "report_generated",
                "fixes_needed": fixes
            }
        except Exception as e:
            logger.error(f"Failed to process security issues: {e}")
            return {"status": "error", "error": str(e)}

    def fix_type_issues(self, directory: str) -> Dict:
        """Fix type annotation issues found by MyPy"""
        try:
            # Read MyPy report
            with open(self.report_dir / "mypy_report.txt") as f:
                report = f.read()

            issues = []
            for line in report.splitlines():
                if ": error:" in line:
                    file_path, line_no, error = self._parse_mypy_error(line)
                    issues.append({
                        "file": file_path,
                        "line": line_no,
                        "error": error
                    })

            return {
                "status": "report_generated",
                "issues": issues
            }
        except Exception as e:
            logger.error(f"Failed to process type issues: {e}")
            return {"status": "error", "error": str(e)}

    def _parse_mypy_error(self, line: str) -> tuple:
        """Parse MyPy error line"""
        try:
            file_path, rest = line.split(":", 1)
            line_no, error = rest.split(": error:", 1)
            return file_path, int(line_no), error.strip()
        except Exception:
            return "unknown", 0, line

    def fix_code_issues(self, directory: str):
        """Fix all code issues"""
        logger.info("Starting code fixes")

        # Create backup first
        if not self.backup_code(directory):
            logger.error("Failed to create backup, aborting fixes")
            return False

        # Apply fixes
        self.results["fixes"] = {
            "formatting": self.fix_formatting(directory),
            "imports": self.fix_imports(directory),
            "style": self.apply_autopep8(directory),
            "security": self.fix_security_issues(directory),
            "types": self.fix_type_issues(directory)
        }

        # Update overall status
        self._update_overall_status()

        # Generate report
        self._generate_fix_report()

        logger.info("Code fixes completed")
        return self.results

    def _update_overall_status(self):
        """Update the overall status based on all fixes"""
        statuses = [fix["status"] for fix in self.results["fixes"].values()]

        if not statuses:
            self.results["overall_status"] = "unknown"
        elif all(status == "success" for status in statuses):
            self.results["overall_status"] = "success"
        elif any(status == "error" for status in statuses):
            self.results["overall_status"] = "error"
        else:
            self.results["overall_status"] = "partial"

    def _generate_fix_report(self):
        """Generate a report of all fixes applied"""
        report_file = self.report_dir / "fix_report.txt"

        report = [
            "Code Fix Report",
            "==============",
            f"Generated at: {self.results['timestamp']}",
            f"Overall Status: {self.results['overall_status'].upper()}",
            "",
            "Fix Results:",
            "-----------"
        ]

        for fix_type, result in self.results["fixes"].items():
            report.append(f"\n{fix_type.upper()}:")
            report.append(f"  Status: {result['status']}")

            if result.get("error"):
                report.append(f"  Error: {result['error']}")

            if fix_type == "security" and result.get("fixes_needed"):
                report.append("\n  Security Issues to Address:")
                for fix in result["fixes_needed"]:
                    report.append(f"    - {fix['file']}:{fix['line']} - {fix['issue']} "
                                f"(Severity: {fix['severity']}, Confidence: {fix['confidence']})")

            if fix_type == "types" and result.get("issues"):
                report.append("\n  Type Issues to Address:")
                for issue in result["issues"]:
                    report.append(f"    - {issue['file']}:{issue['line']} - {issue['error']}")

        with open(report_file, 'w') as f:
            f.write('\n'.join(report))

def main():
    """Main function"""
    try:
        fixer = CodeFixer()
        results = fixer.fix_code_issues(".")

        # Print report
        with open(fixer.report_dir / "fix_report.txt") as f:
            print(f.read())

        # Exit with appropriate status code
        sys.exit(0 if results["overall_status"] == "success" else 1)

    except Exception as e:
        logger.error(f"Code fixing failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
