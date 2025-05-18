#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class MarkdownReportGenerator:
    def __init__(self):
        """Initialize the MarkdownReportGenerator."""
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'markdown_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            ]
        )

    def load_summary(self, summary_file: Path) -> Dict:
        """Load the verification summary from JSON file."""
        try:
            with open(summary_file) as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load summary: {e}")
            raise

    def generate_markdown(self, summary: Dict) -> str:
        """Generate markdown content from the verification summary."""
        try:
            # Format timestamp
            timestamp = datetime.fromisoformat(summary["timestamp"])
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            # Generate markdown content
            content = [
                "# Unit Test Verification Report",
                f"\nGenerated on: {formatted_time}",
                f"\nOverall Status: {'✅ PASSED' if summary['overall_status'] == 'passed' else '❌ FAILED'}",

                "\n## Test Summary",
                f"- Total Tests: {summary['test_summary']['total']}",
                f"- Passed: {summary['test_summary']['passed']}",
                f"- Failed: {summary['test_summary']['failed']}",
                f"- Skipped: {summary['test_summary']['skipped']}",

                "\n## Coverage Summary",
                f"- Total Lines: {summary['coverage_summary']['total']}",
                f"- Covered Lines: {summary['coverage_summary']['covered']}",
                f"- Coverage Percentage: {summary['coverage_summary']['percentage']:.2f}%",

                "\n## Component Status"
            ]

            # Add component status
            for component, status in summary["component_status"].items():
                content.extend([
                    f"\n### {component}",
                    f"- Status: {'✅ PASSED' if status['status'] == 'passed' else '❌ FAILED'}",
                    f"- Tests: {status['test_results']['passed']}/{status['test_results']['total']} passed",
                    f"- Coverage: {status['coverage_results']['percentage']:.2f}%"
                ])

            # Add issues if any
            if summary["issues"]:
                content.extend([
                    "\n## Issues Found",
                    "\n| Component | Type | Details |",
                    "|-----------|------|---------|"
                ])

                for issue in summary["issues"]:
                    content.append(
                        f"| {issue['component']} | {issue['type']} | {issue.get('details', 'N/A')} |"
                    )

            # Add recommendations
            content.extend([
                "\n## Recommendations",
                "\n### Test Coverage",
                "- Ensure all critical paths are covered by tests",
                "- Add more test cases for edge cases",
                "- Consider adding integration tests for complex workflows",

                "\n### Code Quality",
                "- Review and refactor code with low coverage",
                "- Add more assertions to existing tests",
                "- Consider using property-based testing for complex logic",

                "\n### Performance",
                "- Monitor test execution time",
                "- Optimize slow-running tests",
                "- Consider parallel test execution for large test suites"
            ])

            return "\n".join(content)

        except Exception as e:
            self.logger.error(f"Failed to generate markdown: {e}")
            raise

    def save_markdown(self, content: str, output_file: Path) -> bool:
        """Save the markdown content to a file."""
        try:
            with open(output_file, "w") as f:
                f.write(content)
            self.logger.info(f"Markdown report saved to: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save markdown report: {e}")
            return False

def main():
    """Main function to run the markdown report generator."""
    parser = argparse.ArgumentParser(description="Generate markdown report from verification summary")
    parser.add_argument("--summary", required=True, help="Path to verification summary JSON file")
    parser.add_argument("--output", required=True, help="Path to output markdown file")

    args = parser.parse_args()

    generator = MarkdownReportGenerator()

    try:
        summary = generator.load_summary(Path(args.summary))
        content = generator.generate_markdown(summary)
        success = generator.save_markdown(content, Path(args.output))

        sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Failed to generate markdown report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
