"""
Script to run sniffing tests and generate reports.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest
from rich.console import Console
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("sniffing_tests")

class SniffingTestRunner:
    """Runner for sniffing tests."""

    def __init__(self):
        self.console = Console()
        self.test_results: Dict[str, Any] = {}
        self.report_path = Path("test_reports")
        self.setup_directories()

    def setup_directories(self) -> None:
        """Set up test directories."""
        directories = [
            self.report_path,
            self.report_path / "security",
            self.report_path / "browser",
            self.report_path / "functional",
            self.report_path / "unit",
            self.report_path / "documentation",
            self.report_path / "api",
            self.report_path / "performance",
            self.report_path / "compliance",
            self.report_path / "audit"
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    async def run_tests(self) -> None:
        """Run all sniffing tests."""
        try:
            self.console.print("[bold green]Starting sniffing tests...[/bold green]")

            # Run pytest
            result = pytest.main([
                "tests/test_sniffing.py",
                "-v",
                "--capture=no",
                "--asyncio-mode=auto",
                f"--html={self.report_path}/report.html",
                f"--json-report-file={self.report_path}/report.json"
            ])

            # Store results
            self.test_results = self._load_test_results()

            # Generate reports
            await self._generate_reports()

            # Print summary
            self._print_summary()

        except Exception as e:
            logger.error(f"Error running tests: {e}")
            sys.exit(1)

    def _load_test_results(self) -> Dict[str, Any]:
        """Load test results from JSON report."""
        try:
            report_file = self.report_path / "report.json"
            if report_file.exists():
                with open(report_file, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading test results: {e}")
            return {}

    async def _generate_reports(self) -> None:
        """Generate detailed test reports."""
        try:
            # Generate summary report
            summary = {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results.get("tests", [])),
                "passed_tests": len([t for t in self.test_results.get("tests", []) if t["outcome"] == "passed"]),
                "failed_tests": len([t for t in self.test_results.get("tests", []) if t["outcome"] == "failed"]),
                "skipped_tests": len([t for t in self.test_results.get("tests", []) if t["outcome"] == "skipped"]),
                "duration": self.test_results.get("duration", 0)
            }

            # Save summary
            with open(self.report_path / "summary.json", "w") as f:
                json.dump(summary, f, indent=2)

            # Generate domain-specific reports
            for domain in ["security", "browser", "functional", "unit", "documentation"]:
                domain_tests = [
                    t for t in self.test_results.get("tests", [])
                    if domain in t["nodeid"].lower()
                ]
                if domain_tests:
                    domain_report = {
                        "timestamp": datetime.now().isoformat(),
                        "domain": domain,
                        "total_tests": len(domain_tests),
                        "passed_tests": len([t for t in domain_tests if t["outcome"] == "passed"]),
                        "failed_tests": len([t for t in domain_tests if t["outcome"] == "failed"]),
                        "skipped_tests": len([t for t in domain_tests if t["outcome"] == "skipped"]),
                        "tests": domain_tests
                    }
                    with open(self.report_path / domain / "report.json", "w") as f:
                        json.dump(domain_report, f, indent=2)

            # Generate compliance report
            compliance_tests = [
                t for t in self.test_results.get("tests", [])
                if "compliance" in t["nodeid"].lower()
            ]
            if compliance_tests:
                compliance_report = {
                    "timestamp": datetime.now().isoformat(),
                    "total_tests": len(compliance_tests),
                    "passed_tests": len([t for t in compliance_tests if t["outcome"] == "passed"]),
                    "failed_tests": len([t for t in compliance_tests if t["outcome"] == "failed"]),
                    "tests": compliance_tests
                }
                with open(self.report_path / "compliance" / "report.json", "w") as f:
                    json.dump(compliance_report, f, indent=2)

        except Exception as e:
            logger.error(f"Error generating reports: {e}")

    def _print_summary(self) -> None:
        """Print test summary to console."""
        try:
            # Create summary table
            table = Table(title="Sniffing Test Results")
            table.add_column("Category", style="cyan")
            table.add_column("Total", style="magenta")
            table.add_column("Passed", style="green")
            table.add_column("Failed", style="red")
            table.add_column("Skipped", style="yellow")

            # Add overall results
            total = len(self.test_results.get("tests", []))
            passed = len([t for t in self.test_results.get("tests", []) if t["outcome"] == "passed"])
            failed = len([t for t in self.test_results.get("tests", []) if t["outcome"] == "failed"])
            skipped = len([t for t in self.test_results.get("tests", []) if t["outcome"] == "skipped"])
            table.add_row(
                "Overall",
                str(total),
                str(passed),
                str(failed),
                str(skipped)
            )

            # Add domain-specific results
            for domain in ["security", "browser", "functional", "unit", "documentation"]:
                domain_tests = [t for t in self.test_results.get("tests", []) if domain in t["nodeid"].lower()]
                if domain_tests:
                    table.add_row(
                        domain.capitalize(),
                        str(len(domain_tests)),
                        str(len([t for t in domain_tests if t["outcome"] == "passed"])),
                        str(len([t for t in domain_tests if t["outcome"] == "failed"])),
                        str(len([t for t in domain_tests if t["outcome"] == "skipped"]))
                    )

            # Print table
            self.console.print(table)

            # Print status
            if failed == 0:
                self.console.print("\n[bold green]All tests passed![/bold green]")
            else:
                self.console.print(f"\n[bold red]{failed} tests failed![/bold red]")

            # Print report location
            self.console.print(f"\nDetailed reports available in: {self.report_path}")

        except Exception as e:
            logger.error(f"Error printing summary: {e}")

async def main() -> None:
    """Main entry point."""
    runner = SniffingTestRunner()
    await runner.run_tests()

if __name__ == "__main__":
    asyncio.run(main())
