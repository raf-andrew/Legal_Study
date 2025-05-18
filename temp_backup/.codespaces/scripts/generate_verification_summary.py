#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class VerificationSummaryGenerator:
    def __init__(self):
        """Initialize the VerificationSummaryGenerator."""
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            ]
        )

    def collect_verification_reports(self, reports_dir: Path) -> List[Dict]:
        """Collect all verification reports from the specified directory."""
        reports = []
        try:
            for report_file in reports_dir.glob("**/verification_*.json"):
                with open(report_file) as f:
                    report = json.load(f)
                    reports.append({
                        "file": str(report_file),
                        "data": report
                    })
            return reports
        except Exception as e:
            self.logger.error(f"Failed to collect verification reports: {e}")
            raise

    def generate_summary(self, reports: List[Dict]) -> Dict:
        """Generate a summary from all verification reports."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_reports": len(reports),
            "overall_status": "passed",
            "test_summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            },
            "coverage_summary": {
                "total": 0,
                "covered": 0,
                "percentage": 0
            },
            "issues": [],
            "component_status": {}
        }

        try:
            for report in reports:
                data = report["data"]
                component = Path(report["file"]).parent.name

                # Update test summary
                test_results = data["test_results"]
                summary["test_summary"]["total"] += test_results["total"]
                summary["test_summary"]["passed"] += test_results["passed"]
                summary["test_summary"]["failed"] += test_results["failed"]
                summary["test_summary"]["skipped"] += test_results["skipped"]

                # Update coverage summary
                coverage_results = data["coverage_results"]
                summary["coverage_summary"]["total"] += coverage_results["total"]
                summary["coverage_summary"]["covered"] += coverage_results["covered"]

                # Update component status
                summary["component_status"][component] = {
                    "status": data["verification_status"],
                    "test_results": test_results,
                    "coverage_results": coverage_results
                }

                # Collect issues
                if data["issues"]:
                    summary["issues"].extend([
                        {
                            "component": component,
                            **issue
                        }
                        for issue in data["issues"]
                    ])

            # Calculate overall coverage percentage
            if summary["coverage_summary"]["total"] > 0:
                summary["coverage_summary"]["percentage"] = (
                    summary["coverage_summary"]["covered"] /
                    summary["coverage_summary"]["total"] * 100
                )

            # Determine overall status
            if summary["test_summary"]["failed"] > 0 or summary["issues"]:
                summary["overall_status"] = "failed"

            return summary

        except Exception as e:
            self.logger.error(f"Failed to generate summary: {e}")
            raise

    def save_summary(self, summary: Dict, output_file: Path) -> bool:
        """Save the summary to a JSON file."""
        try:
            with open(output_file, "w") as f:
                json.dump(summary, f, indent=2)
            self.logger.info(f"Summary saved to: {output_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save summary: {e}")
            return False

def main():
    """Main function to run the verification summary generator."""
    parser = argparse.ArgumentParser(description="Generate verification summary from test reports")
    parser.add_argument("--reports-dir", required=True, help="Directory containing verification reports")
    parser.add_argument("--output", required=True, help="Path to output summary JSON file")

    args = parser.parse_args()

    generator = VerificationSummaryGenerator()

    try:
        reports = generator.collect_verification_reports(Path(args.reports_dir))
        summary = generator.generate_summary(reports)
        success = generator.save_summary(summary, Path(args.output))

        sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Failed to generate summary: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
