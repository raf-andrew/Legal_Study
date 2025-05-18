"""
Script to run full sniffing system and generate comprehensive report.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from sniffing.mcp.server.mcp_server import MCPServer
from sniffing.mcp.orchestration.sniffing_loop import SniffingLoop

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("full_sniffing.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("full_sniffing")

class FullSniffingRunner:
    """Runner for full sniffing system."""

    def __init__(self):
        self.console = Console()
        self.config = self._load_config()
        self.mcp_server = MCPServer(self.config)
        self.sniffing_loop = SniffingLoop(self.config.get("sniffing", {}))
        self.report_path = Path(self.config["mcp"]["report_path"])
        self.results: Dict[str, Any] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            config_file = Path("sniffing/config/sniffing_config.yaml")
            if not config_file.exists():
                raise FileNotFoundError("Configuration file not found")

            with open(config_file, "r") as f:
                return yaml.safe_load(f)

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)

    async def run(self) -> None:
        """Run full sniffing system."""
        try:
            self.console.print("[bold green]Starting full sniffing system...[/bold green]")

            # Create progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                # Start services
                task = progress.add_task("Starting services...", total=None)
                await self._start_services()
                progress.update(task, completed=True)

                # Get files to sniff
                task = progress.add_task("Finding files to sniff...", total=None)
                files = await self._get_files()
                progress.update(task, completed=True)

                # Run sniffing
                task = progress.add_task(f"Running sniffing on {len(files)} files...", total=None)
                await self._run_sniffing(files)
                progress.update(task, completed=True)

                # Generate reports
                task = progress.add_task("Generating reports...", total=None)
                await self._generate_reports()
                progress.update(task, completed=True)

            # Print summary
            self._print_summary()

        except Exception as e:
            logger.error(f"Error running full sniffing: {e}")
            await self.cleanup()
            sys.exit(1)

    async def _start_services(self) -> None:
        """Start required services."""
        try:
            # Start MCP server
            await self.mcp_server.start()

            # Start sniffing loop
            await self.sniffing_loop.start()

        except Exception as e:
            logger.error(f"Error starting services: {e}")
            raise

    async def _get_files(self) -> Set[Path]:
        """Get files to sniff."""
        try:
            files = set()
            workspace = Path(".")

            # Get file patterns from config
            patterns = self.config.get("sniffing", {}).get("file_patterns", ["*.py", "*.js", "*.ts"])
            ignore_patterns = self.config.get("sniffing", {}).get("ignore_patterns", ["**/tests/**", "**/vendor/**"])

            # Find files
            for pattern in patterns:
                files.update(workspace.glob(f"**/{pattern}"))

            # Filter ignored files
            for pattern in ignore_patterns:
                files = {f for f in files if not any(part.match(pattern) for part in f.parents)}

            return files

        except Exception as e:
            logger.error(f"Error getting files: {e}")
            raise

    async def _run_sniffing(self, files: Set[Path]) -> None:
        """Run sniffing on files."""
        try:
            # Add files to sniffing loop
            for file in files:
                await self.sniffing_loop.add_file(str(file))

            # Wait for completion
            while any(not r.get("completed", False) for r in self.sniffing_loop.results_cache.values()):
                await asyncio.sleep(1)

            # Store results
            self.results = {
                str(file): self.sniffing_loop.results_cache[str(file)]
                for file in files
            }

        except Exception as e:
            logger.error(f"Error running sniffing: {e}")
            raise

    async def _generate_reports(self) -> None:
        """Generate comprehensive reports."""
        try:
            # Create report directories
            for domain in ["security", "browser", "functional", "unit", "documentation"]:
                (self.report_path / domain).mkdir(parents=True, exist_ok=True)

            # Generate summary report
            summary = self._generate_summary_report()
            with open(self.report_path / "summary.json", "w") as f:
                json.dump(summary, f, indent=2)

            # Generate domain reports
            for domain in ["security", "browser", "functional", "unit", "documentation"]:
                report = self._generate_domain_report(domain)
                with open(self.report_path / domain / "report.json", "w") as f:
                    json.dump(report, f, indent=2)

            # Generate compliance report
            compliance = self._generate_compliance_report()
            with open(self.report_path / "compliance.json", "w") as f:
                json.dump(compliance, f, indent=2)

            # Generate markdown report
            markdown = self._generate_markdown_report()
            with open(self.report_path / "report.md", "w") as f:
                f.write(markdown)

        except Exception as e:
            logger.error(f"Error generating reports: {e}")
            raise

    def _generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report."""
        try:
            total_files = len(self.results)
            total_issues = sum(
                len(r["result"].get("issues", []))
                for r in self.results.values()
            )
            total_fixes = sum(
                len(r["result"].get("fixes", []))
                for r in self.results.values()
            )

            return {
                "timestamp": datetime.now().isoformat(),
                "total_files": total_files,
                "total_issues": total_issues,
                "total_fixes": total_fixes,
                "success_rate": (total_fixes / total_issues * 100) if total_issues > 0 else 100,
                "domains": {
                    domain: {
                        "files": len([
                            f for f in self.results
                            if domain in self.results[f]["result"].get("domains", [])
                        ]),
                        "issues": len([
                            i for r in self.results.values()
                            for i in r["result"].get("issues", [])
                            if i.get("domain") == domain
                        ])
                    }
                    for domain in ["security", "browser", "functional", "unit", "documentation"]
                }
            }

        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            return {}

    def _generate_domain_report(self, domain: str) -> Dict[str, Any]:
        """Generate domain-specific report."""
        try:
            domain_files = [
                f for f in self.results
                if domain in self.results[f]["result"].get("domains", [])
            ]
            domain_issues = [
                i for r in self.results.values()
                for i in r["result"].get("issues", [])
                if i.get("domain") == domain
            ]

            return {
                "timestamp": datetime.now().isoformat(),
                "domain": domain,
                "total_files": len(domain_files),
                "total_issues": len(domain_issues),
                "files": {
                    f: self.results[f]["result"]
                    for f in domain_files
                },
                "issues": domain_issues
            }

        except Exception as e:
            logger.error(f"Error generating domain report: {e}")
            return {}

    def _generate_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report."""
        try:
            compliance_issues = [
                i for r in self.results.values()
                for i in r["result"].get("issues", [])
                if i.get("type") == "compliance"
            ]

            return {
                "timestamp": datetime.now().isoformat(),
                "total_issues": len(compliance_issues),
                "issues": compliance_issues,
                "soc2": {
                    category: {
                        "status": "compliant" if not any(
                            i for i in compliance_issues
                            if i.get("category") == category
                        ) else "non_compliant",
                        "issues": [
                            i for i in compliance_issues
                            if i.get("category") == category
                        ]
                    }
                    for category in ["security", "availability", "processing", "confidentiality", "privacy"]
                }
            }

        except Exception as e:
            logger.error(f"Error generating compliance report: {e}")
            return {}

    def _generate_markdown_report(self) -> str:
        """Generate markdown report."""
        try:
            summary = self._generate_summary_report()
            compliance = self._generate_compliance_report()

            return f"""# Sniffing System Report

## Summary
- **Total Files**: {summary["total_files"]}
- **Total Issues**: {summary["total_issues"]}
- **Total Fixes**: {summary["total_fixes"]}
- **Success Rate**: {summary["success_rate"]:.1f}%

## Domain Results
{self._format_domain_results(summary["domains"])}

## Compliance Status
{self._format_compliance_status(compliance["soc2"])}

## Issues by Severity
{self._format_issues_by_severity()}

## Recommendations
{self._format_recommendations()}

## Report Locations
- Summary Report: {self.report_path / "summary.json"}
- Domain Reports: {self.report_path / "<domain>" / "report.json"}
- Compliance Report: {self.report_path / "compliance.json"}
- Full Log: full_sniffing.log
"""

        except Exception as e:
            logger.error(f"Error generating markdown report: {e}")
            return ""

    def _format_domain_results(self, domains: Dict[str, Any]) -> str:
        """Format domain results for markdown."""
        lines = []
        for domain, stats in domains.items():
            lines.append(f"### {domain.capitalize()}")
            lines.append(f"- Files: {stats['files']}")
            lines.append(f"- Issues: {stats['issues']}")
            lines.append("")
        return "\n".join(lines)

    def _format_compliance_status(self, soc2: Dict[str, Any]) -> str:
        """Format compliance status for markdown."""
        lines = []
        for category, status in soc2.items():
            lines.append(f"### {category.capitalize()}")
            lines.append(f"- Status: {status['status']}")
            if status['issues']:
                lines.append("- Issues:")
                for issue in status['issues']:
                    lines.append(f"  - {issue['description']}")
            lines.append("")
        return "\n".join(lines)

    def _format_issues_by_severity(self) -> str:
        """Format issues by severity for markdown."""
        issues = [
            i for r in self.results.values()
            for i in r["result"].get("issues", [])
        ]
        severities = {}
        for issue in issues:
            severity = issue.get("severity", "unknown")
            if severity not in severities:
                severities[severity] = []
            severities[severity].append(issue)

        lines = []
        for severity, severity_issues in severities.items():
            lines.append(f"### {severity.capitalize()}")
            lines.append(f"Total: {len(severity_issues)}")
            lines.append("Issues:")
            for issue in severity_issues:
                lines.append(f"- {issue.get('description', 'No description')}")
            lines.append("")
        return "\n".join(lines)

    def _format_recommendations(self) -> str:
        """Format recommendations for markdown."""
        recommendations = set()
        for result in self.results.values():
            recommendations.update(result["result"].get("recommendations", []))

        if not recommendations:
            return "No recommendations available."

        lines = []
        for recommendation in sorted(recommendations):
            lines.append(f"- {recommendation}")
        return "\n".join(lines)

    def _print_summary(self) -> None:
        """Print summary to console."""
        try:
            summary = self._generate_summary_report()

            # Create summary table
            table = Table(title="Sniffing System Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")

            # Add overall stats
            table.add_row("Total Files", str(summary["total_files"]))
            table.add_row("Total Issues", str(summary["total_issues"]))
            table.add_row("Total Fixes", str(summary["total_fixes"]))
            table.add_row("Success Rate", f"{summary['success_rate']:.1f}%")

            # Add domain stats
            table.add_section()
            for domain, stats in summary["domains"].items():
                table.add_row(
                    f"{domain.capitalize()} Files",
                    str(stats["files"])
                )
                table.add_row(
                    f"{domain.capitalize()} Issues",
                    str(stats["issues"])
                )

            # Print table
            self.console.print(table)

            # Print report locations
            self.console.print("\n[bold]Report Locations:[/bold]")
            self.console.print(f"Summary Report: {self.report_path / 'summary.json'}")
            self.console.print(f"Domain Reports: {self.report_path / '<domain>' / 'report.json'}")
            self.console.print(f"Compliance Report: {self.report_path / 'compliance.json'}")
            self.console.print(f"Markdown Report: {self.report_path / 'report.md'}")
            self.console.print("Full Log: full_sniffing.log")

        except Exception as e:
            logger.error(f"Error printing summary: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Stop sniffing loop
            await self.sniffing_loop.stop()

            # Stop MCP server
            await self.mcp_server.stop()

        except Exception as e:
            logger.error(f"Error cleaning up: {e}")

async def main() -> None:
    """Main entry point."""
    runner = FullSniffingRunner()
    await runner.run()
    await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
