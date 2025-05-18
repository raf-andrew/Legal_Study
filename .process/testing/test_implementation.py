"""
Test implementation for process documentation verification.
"""
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class ProcessDocumentationTester:
    """Test implementation for process documentation."""

    def __init__(self, process_dir: str = ".process"):
        """Initialize the tester with the process directory."""
        self.process_dir = Path(process_dir)
        self.required_files = [
            "README.md",
            "testing/README.md",
            "resolution/README.md",
            "validation/README.md",
            "automation/README.md",
            "documentation/README.md"
        ]

    def test_documentation_completeness(self) -> Dict[str, Any]:
        """Test that all required documentation exists."""
        results = {
            "passed": True,
            "missing_files": [],
            "errors": []
        }

        for file in self.required_files:
            file_path = self.process_dir / file
            if not file_path.exists():
                results["passed"] = False
                results["missing_files"].append(str(file_path))
                results["errors"].append(f"Missing required file: {file_path}")

        return results

    def test_markdown_formatting(self) -> Dict[str, Any]:
        """Test markdown formatting in all documentation files."""
        results = {
            "passed": True,
            "errors": []
        }

        for file in self.process_dir.rglob("*.md"):
            try:
                # Check for common markdown issues
                content = file.read_text()

                # Check for headers
                if not re.search(r"^#\s", content, re.MULTILINE):
                    results["errors"].append(f"Missing main header in {file}")

                # Check for code blocks
                if "```" in content and not re.search(r"```\w*\n.*\n```", content, re.DOTALL):
                    results["errors"].append(f"Malformed code block in {file}")

                # Check for links
                if "[" in content and not re.search(r"\[.*\]\(.*\)", content):
                    results["errors"].append(f"Malformed link in {file}")

            except Exception as e:
                results["errors"].append(f"Error processing {file}: {str(e)}")

        if results["errors"]:
            results["passed"] = False

        return results

    def test_directory_structure(self) -> Dict[str, Any]:
        """Test the directory structure and permissions."""
        results = {
            "passed": True,
            "errors": []
        }

        required_dirs = [
            "testing",
            "resolution",
            "validation",
            "automation",
            "documentation"
        ]

        for dir_name in required_dirs:
            dir_path = self.process_dir / dir_name
            if not dir_path.exists():
                results["passed"] = False
                results["errors"].append(f"Missing required directory: {dir_path}")
            elif not os.access(dir_path, os.R_OK):
                results["passed"] = False
                results["errors"].append(f"Cannot read directory: {dir_path}")

        return results

    def test_template_files(self) -> Dict[str, Any]:
        """Test all template files in the process directory."""
        results = {
            "passed": True,
            "errors": []
        }

        template_patterns = [
            "*.template",
            "*.md.template",
            "*.yaml.template"
        ]

        for pattern in template_patterns:
            for template_file in self.process_dir.rglob(pattern):
                try:
                    content = template_file.read_text()

                    # Check for template variables
                    if not re.search(r"\{\{.*\}\}", content):
                        results["errors"].append(f"No template variables found in {template_file}")

                    # Check for required sections
                    required_sections = ["##", "###", "-"]
                    for section in required_sections:
                        if section not in content:
                            results["errors"].append(f"Missing {section} section in {template_file}")

                except Exception as e:
                    results["errors"].append(f"Error processing {template_file}: {str(e)}")

        if results["errors"]:
            results["passed"] = False

        return results

    def test_workflow_files(self) -> Dict[str, Any]:
        """Test all workflow files in the process directory."""
        results = {
            "passed": True,
            "errors": []
        }

        workflow_files = list(self.process_dir.rglob("workflow*.yaml")) + \
                        list(self.process_dir.rglob("workflow*.yml"))

        for workflow_file in workflow_files:
            try:
                content = workflow_file.read_text()

                # Check for required workflow sections
                required_sections = ["name:", "on:", "jobs:"]
                for section in required_sections:
                    if section not in content:
                        results["errors"].append(f"Missing {section} in {workflow_file}")

                # Check for valid YAML
                if not self._is_valid_yaml(content):
                    results["errors"].append(f"Invalid YAML in {workflow_file}")

            except Exception as e:
                results["errors"].append(f"Error processing {workflow_file}: {str(e)}")

        if results["errors"]:
            results["passed"] = False

        return results

    def _is_valid_yaml(self, content: str) -> bool:
        """Check if the content is valid YAML."""
        try:
            import yaml
            yaml.safe_load(content)
            return True
        except Exception:
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        results = {
            "passed": True,
            "test_results": {}
        }

        # Run all test methods
        test_methods = [
            self.test_documentation_completeness,
            self.test_markdown_formatting,
            self.test_directory_structure,
            self.test_template_files,
            self.test_workflow_files
        ]

        for test_method in test_methods:
            test_name = test_method.__name__
            test_result = test_method()
            results["test_results"][test_name] = test_result
            if not test_result["passed"]:
                results["passed"] = False

        return results

def main():
    """Main function to run all tests."""
    tester = ProcessDocumentationTester()
    results = tester.run_all_tests()

    # Print results
    print("\nTest Results:")
    print("=" * 50)

    for test_name, test_result in results["test_results"].items():
        print(f"\n{test_name}:")
        print("-" * 30)
        print(f"Status: {'PASSED' if test_result['passed'] else 'FAILED'}")

        if not test_result["passed"]:
            print("\nErrors:")
            for error in test_result.get("errors", []):
                print(f"- {error}")

            if "missing_files" in test_result:
                print("\nMissing Files:")
                for file in test_result["missing_files"]:
                    print(f"- {file}")

    print("\n" + "=" * 50)
    print(f"Overall Status: {'PASSED' if results['passed'] else 'FAILED'}")

if __name__ == "__main__":
    main()
