"""
Main entry point for the sniffing infrastructure.
"""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from rich.console import Console
from rich.logging import RichHandler

from core.base_sniffer import SnifferType
from domains.browser.browser_sniffer import BrowserSniffer
from domains.functional.functional_sniffer import FunctionalSniffer
from domains.unit.unit_sniffer import UnitSniffer
from mcp.mcp_integration import MCPIntegration

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("sniffing")

class SniffingInfrastructure:
    """Main class for the sniffing infrastructure."""

    def __init__(self, config_path: str = "sniffing.yaml"):
        self.console = Console()
        self.config = self._load_config(config_path)
        self.mcp = MCPIntegration(self.config["mcp"]) if self.config["mcp"]["enabled"] else None
        self.sniffers = self._initialize_sniffers()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def _initialize_sniffers(self) -> Dict[SnifferType, Any]:
        """Initialize all enabled sniffers."""
        sniffers = {}

        if self.config["browser"]["enabled"]:
            sniffers[SnifferType.BROWSER] = BrowserSniffer(self.config["browser"])

        if self.config["functional"]["enabled"]:
            sniffers[SnifferType.FUNCTIONAL] = FunctionalSniffer(self.config["functional"])

        if self.config["unit"]["enabled"]:
            sniffers[SnifferType.UNIT] = UnitSniffer(self.config["unit"])

        return sniffers

    async def run(self) -> None:
        """Run the sniffing infrastructure."""
        try:
            self.console.print("[bold blue]Starting Sniffing Infrastructure[/bold blue]")

            # Run all sniffers
            results = []
            for sniffer_type, sniffer in self.sniffers.items():
                self.console.print(f"\n[bold green]Running {sniffer_type.name} Sniffer[/bold green]")
                result = await self._run_sniffer(sniffer)
                results.append(result)

            # Analyze results
            if self.mcp:
                await self.mcp.analyze_results(results)

            # Generate report
            self._generate_report(results)

            self.console.print("\n[bold green]Sniffing Infrastructure completed successfully[/bold green]")

        except Exception as e:
            logger.error(f"Error running sniffing infrastructure: {e}")
            sys.exit(1)

    async def _run_sniffer(self, sniffer: Any) -> Dict:
        """Run a single sniffer and handle its results."""
        try:
            # Run sniffing
            result = await sniffer.sniff()

            # Handle issues
            if result.issues:
                self.console.print(f"\n[bold yellow]Found {len(result.issues)} issues[/bold yellow]")

                # Try to fix issues
                if sniffer.fix_issues(result.issues):
                    self.console.print("[bold green]Successfully fixed issues[/bold green]")
                else:
                    self.console.print("[bold red]Failed to fix some issues[/bold red]")

            # Generate recommendations
            if result.recommendations:
                self.console.print("\n[bold blue]Recommendations:[/bold blue]")
                for rec in result.recommendations:
                    self.console.print(f"  • {rec}")

            return result

        except Exception as e:
            logger.error(f"Error running sniffer: {e}")
            return {
                "status": "error",
                "error": str(e),
                "issues": []
            }

    def _generate_report(self, results: List[Dict]) -> None:
        """Generate a comprehensive report of all sniffing results."""
        report_path = Path(self.config["report_path"])
        report_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_path / f"sniffing_report_{timestamp}.json"

        report = {
            "timestamp": timestamp,
            "results": results,
            "summary": self._generate_summary(results)
        }

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        self.console.print(f"\n[bold green]Report generated: {report_file}[/bold green]")

    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Generate a summary of all sniffing results."""
        total_issues = sum(len(r.get("issues", [])) for r in results)
        total_tests = sum(r.get("metrics", {}).get("total_tests", 0) for r in results)
        passed_tests = sum(r.get("metrics", {}).get("passed_tests", 0) for r in results)

        return {
            "total_issues": total_issues,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "test_success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }

async def main():
    """Main entry point."""
    infrastructure = SniffingInfrastructure()
    await infrastructure.run()

if __name__ == "__main__":
    asyncio.run(main())
