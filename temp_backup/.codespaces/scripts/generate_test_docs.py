#!/usr/bin/env python3

import os
import sys
import json
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET
from jinja2 import Template

class TestDocumentationGenerator:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.config_path = self.root_dir / "config" / "unit_test_config.yaml"
        self.docs_dir = self.root_dir / "docs" / "testing"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Setup logging
        self._setup_logging()

        # Load configuration
        self.config = self._load_config()

        # Create docs directory if it doesn't exist
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Configure logging for the documentation generator."""
        log_file = self.root_dir / "logs" / f"test_docs_{self.timestamp}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self) -> Dict:
        """Load the unit test configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def _parse_test_results(self, report_file: str) -> Dict:
        """Parse test results from HTML report."""
        try:
            with open(report_file, 'r') as f:
                content = f.read()
                # Extract test statistics using regex or HTML parsing
                # This is a simplified version - you might want to use BeautifulSoup for better parsing
                return {
                    "total_tests": content.count("test-case"),
                    "passed_tests": content.count("passed"),
                    "failed_tests": content.count("failed"),
                    "skipped_tests": content.count("skipped")
                }
        except Exception as e:
            self.logger.error(f"Failed to parse test results: {e}")
            return {}

    def _parse_coverage_results(self, coverage_file: str) -> Dict:
        """Parse coverage results from XML report."""
        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            return {
                "line_coverage": root.get("line-rate", "0"),
                "branch_coverage": root.get("branch-rate", "0"),
                "total_lines": root.get("lines-valid", "0"),
                "covered_lines": root.get("lines-covered", "0")
            }
        except Exception as e:
            self.logger.error(f"Failed to parse coverage results: {e}")
            return {}

    def _generate_test_suite_doc(self, test_suite: str, report_file: str,
                               coverage_file: str, verification_file: str) -> str:
        """Generate documentation for a specific test suite."""
        test_results = self._parse_test_results(report_file)
        coverage_results = self._parse_coverage_results(coverage_file)

        template = """
# {{ test_suite }} Test Suite Documentation

## Test Execution Summary
- **Execution Time**: {{ timestamp }}
- **Total Tests**: {{ test_results.total_tests }}
- **Passed Tests**: {{ test_results.passed_tests }}
- **Failed Tests**: {{ test_results.failed_tests }}
- **Skipped Tests**: {{ test_results.skipped_tests }}

## Coverage Report
- **Line Coverage**: {{ coverage_results.line_coverage }}%
- **Branch Coverage**: {{ coverage_results.branch_coverage }}%
- **Total Lines**: {{ coverage_results.total_lines }}
- **Covered Lines**: {{ coverage_results.covered_lines }}

## Test Categories
{% for category in config.test_categories %}
- {{ category }}
{% endfor %}

## Test Environment
- **Python Version**: {{ config.environment.python_version }}
- **Virtual Environment**: {{ config.environment.virtual_env }}
- **Dependencies**:
{% for dep in config.environment.dependencies %}
  - {{ dep }}
{% endfor %}

## Test Configuration
- **Parallel Execution**: {{ config.execution.parallel }}
- **Number of Workers**: {{ config.execution.workers }}
- **Timeout**: {{ config.execution.timeout }} seconds
- **Retry Failed**: {{ config.execution.retry_failed }}
- **Max Retries**: {{ config.execution.max_retries }}

## Coverage Requirements
- **Minimum Coverage**: {{ config.coverage.minimum_coverage }}%
- **Excluded Patterns**:
{% for pattern in config.coverage.exclude_patterns %}
  - {{ pattern }}
{% endfor %}

## Test Reports
- **HTML Report**: {{ report_file }}
- **Coverage Report**: {{ coverage_file }}
- **Verification Report**: {{ verification_file }}

## Issues and Resolutions
{% if issues %}
{% for issue in issues %}
### {{ issue.title }}
- **Status**: {{ issue.status }}
- **Description**: {{ issue.description }}
- **Resolution**: {{ issue.resolution }}
{% endfor %}
{% else %}
No issues reported.
{% endif %}
"""
        try:
            template = Template(template)
            return template.render(
                test_suite=test_suite,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                test_results=test_results,
                coverage_results=coverage_results,
                config=self.config,
                report_file=report_file,
                coverage_file=coverage_file,
                verification_file=verification_file,
                issues=self._load_issues(verification_file)
            )
        except Exception as e:
            self.logger.error(f"Failed to generate test suite documentation: {e}")
            return ""

    def _load_issues(self, verification_file: str) -> List[Dict]:
        """Load issues from verification file."""
        try:
            with open(verification_file, 'r') as f:
                data = json.load(f)
                return data.get("issues", [])
        except Exception as e:
            self.logger.error(f"Failed to load issues: {e}")
            return []

    def generate_documentation(self, test_suite: str, report_file: str,
                             coverage_file: str, verification_file: str,
                             output_file: str):
        """Generate comprehensive test documentation."""
        self.logger.info(f"Generating documentation for {test_suite}")

        # Generate test suite documentation
        doc_content = self._generate_test_suite_doc(
            test_suite, report_file, coverage_file, verification_file
        )

        # Write documentation to file
        try:
            with open(output_file, 'w') as f:
                f.write(doc_content)
            self.logger.info(f"Documentation generated successfully: {output_file}")
        except Exception as e:
            self.logger.error(f"Failed to write documentation: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate test documentation")
    parser.add_argument("--test-suite", required=True, help="Test suite name")
    parser.add_argument("--report-file", required=True, help="Test report file")
    parser.add_argument("--coverage-report", required=True, help="Coverage report file")
    parser.add_argument("--verification-file", required=True, help="Verification file")
    parser.add_argument("--output", required=True, help="Output documentation file")
    parser.add_argument("--log-file", help="Log file path")

    args = parser.parse_args()

    generator = TestDocumentationGenerator()
    generator.generate_documentation(
        args.test_suite,
        args.report_file,
        args.coverage_report,
        args.verification_file,
        args.output
    )

if __name__ == "__main__":
    main()
