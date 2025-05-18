#!/usr/bin/env python3
"""
Script to generate test reports from template.
"""
import os
import sys
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class ReportGenerator:
    """Generate test reports from template."""

    def __init__(self, test_results: Dict[str, Any], template_file: str = "test_report_template.md"):
        """Initialize the report generator."""
        self.test_results = test_results
        self.template_file = Path(template_file)
        self.environment_info = self._get_environment_info()

    def _get_environment_info(self) -> Dict[str, str]:
        """Get environment information."""
        return {
            "python_version": platform.python_version(),
            "os_info": platform.platform(),
            "dependencies": self._get_dependencies()
        }

    def _get_dependencies(self) -> str:
        """Get installed dependencies."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "freeze"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return "Failed to get dependencies"

    def _calculate_test_stats(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate test statistics."""
        stats = {
            "total": len(test_results),
            "passed": sum(1 for t in test_results.values() if t["passed"]),
            "failed": sum(1 for t in test_results.values() if not t["passed"]),
            "issues": []
        }

        for test_name, result in test_results.items():
            if not result["passed"]:
                stats["issues"].extend(result.get("errors", []))
                if "missing_files" in result:
                    stats["issues"].extend(result["missing_files"])

        return stats

    def _format_issues(self, issues: list) -> str:
        """Format issues for markdown."""
        if not issues:
            return "No issues found."
        return "\n".join(f"- {issue}" for issue in issues)

    def _get_test_details(self, test_name: str) -> str:
        """Get detailed test results."""
        test_result = self.test_results["tests"].get(test_name, {})
        if not test_result:
            return "No test results available."

        details = []
        if not test_result["passed"]:
            details.append("Test failed with the following issues:")
            details.extend(f"- {error}" for error in test_result.get("errors", []))
            if "missing_files" in test_result:
                details.append("\nMissing files:")
                details.extend(f"- {file}" for file in test_result["missing_files"])
        else:
            details.append("All tests passed successfully.")

        return "\n".join(details)

    def generate_report(self, output_file: str) -> None:
        """Generate the test report."""
        # Calculate statistics
        doc_stats = self._calculate_test_stats({
            k: v for k, v in self.test_results["tests"].items()
            if k.startswith("test_documentation")
        })
        dir_stats = self._calculate_test_stats({
            k: v for k, v in self.test_results["tests"].items()
            if k.startswith("test_directory")
        })
        template_stats = self._calculate_test_stats({
            k: v for k, v in self.test_results["tests"].items()
            if k.startswith("test_template")
        })
        workflow_stats = self._calculate_test_stats({
            k: v for k, v in self.test_results["tests"].items()
            if k.startswith("test_workflow")
        })

        # Read template
        with open(self.template_file, "r") as f:
            template = f.read()

        # Prepare template variables
        template_vars = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "suite_name": "Process Documentation Test Suite",
            "environment": "Development",
            "status": self.test_results["overall_status"],
            "coverage": f"{self.test_results['coverage']:.2f}",

            # Documentation tests
            "doc_status": "PASSED" if doc_stats["passed"] == doc_stats["total"] else "FAILED",
            "doc_total": doc_stats["total"],
            "doc_passed": doc_stats["passed"],
            "doc_failed": doc_stats["failed"],
            "doc_issues": self._format_issues(doc_stats["issues"]),

            # Directory tests
            "dir_status": "PASSED" if dir_stats["passed"] == dir_stats["total"] else "FAILED",
            "dir_total": dir_stats["total"],
            "dir_passed": dir_stats["passed"],
            "dir_failed": dir_stats["failed"],
            "dir_issues": self._format_issues(dir_stats["issues"]),

            # Template tests
            "template_status": "PASSED" if template_stats["passed"] == template_stats["total"] else "FAILED",
            "template_total": template_stats["total"],
            "template_passed": template_stats["passed"],
            "template_failed": template_stats["failed"],
            "template_issues": self._format_issues(template_stats["issues"]),

            # Workflow tests
            "workflow_status": "PASSED" if workflow_stats["passed"] == workflow_stats["total"] else "FAILED",
            "workflow_total": workflow_stats["total"],
            "workflow_passed": workflow_stats["passed"],
            "workflow_failed": workflow_stats["failed"],
            "workflow_issues": self._format_issues(workflow_stats["issues"]),

            # Detailed results
            "doc_completeness_details": self._get_test_details("test_documentation_completeness"),
            "markdown_formatting_details": self._get_test_details("test_markdown_formatting"),
            "directory_structure_details": self._get_test_details("test_directory_structure"),
            "template_files_details": self._get_test_details("test_template_files"),
            "workflow_files_details": self._get_test_details("test_workflow_files"),

            # Environment details
            "python_version": self.environment_info["python_version"],
            "os_info": self.environment_info["os_info"],
            "dependencies": self.environment_info["dependencies"],

            # Recommendations and next steps
            "recommendations": self._generate_recommendations(),
            "next_steps": self._generate_next_steps(),

            # Execution log
            "execution_log": self._get_execution_log()
        }

        # Replace template variables
        for var, value in template_vars.items():
            template = template.replace(f"{{{{{var}}}}}", str(value))

        # Write report
        with open(output_file, "w") as f:
            f.write(template)

    def _generate_recommendations(self) -> str:
        """Generate recommendations based on test results."""
        recommendations = []

        if self.test_results["coverage"] < 100:
            recommendations.append("Increase test coverage to 100%")

        for test_name, result in self.test_results["tests"].items():
            if not result["passed"]:
                recommendations.append(f"Fix issues in {test_name}")

        if not recommendations:
            recommendations.append("No specific recommendations at this time.")

        return "\n".join(f"- {rec}" for rec in recommendations)

    def _generate_next_steps(self) -> str:
        """Generate next steps based on test results."""
        next_steps = []

        if self.test_results["overall_status"] == "FAILED":
            next_steps.append("Fix failing tests")
            next_steps.append("Run test suite again")
        else:
            next_steps.append("Review test coverage")
            next_steps.append("Consider additional test cases")

        return "\n".join(f"- {step}" for step in next_steps)

    def _get_execution_log(self) -> str:
        """Get test execution log."""
        return f"Test execution completed at {datetime.now().isoformat()}\n" + \
               f"Overall status: {self.test_results['overall_status']}\n" + \
               f"Coverage: {self.test_results['coverage']:.2f}%"

def main():
    """Main function to generate test report."""
    if len(sys.argv) != 3:
        print("Usage: generate_report.py <test_results.json> <output_report.md>")
        sys.exit(1)

    test_results_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(test_results_file, "r") as f:
            test_results = json.load(f)

        generator = ReportGenerator(test_results)
        generator.generate_report(output_file)
        print(f"Test report generated: {output_file}")

    except Exception as e:
        print(f"Error generating test report: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
