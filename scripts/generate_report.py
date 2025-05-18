"""
Script to generate reports from sniffing results.
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import jinja2
import yaml

logger = logging.getLogger("generate_report")

class ReportGenerator:
    """Class for generating reports from sniffing results."""

    def __init__(self):
        """Initialize generator."""
        self.root_dir = Path.cwd()
        self.results_dir = self.root_dir / "sniffing/results"
        self.templates_dir = self.root_dir / "sniffing/templates"
        self.reports_dir = self.root_dir / "sniffing/reports"

    def generate(
        self,
        format: str = "html",
        output: Optional[str] = None
    ) -> None:
        """Generate report.

        Args:
            format: Report format
            output: Output file path
        """
        try:
            # Load results
            results = self._load_results()
            if not results:
                logger.error("No results found")
                return

            # Generate report
            if format == "html":
                self._generate_html(results, output)
            elif format == "markdown":
                self._generate_markdown(results, output)
            elif format == "json":
                self._generate_json(results, output)
            else:
                raise ValueError(f"Unsupported format: {format}")

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

    def _load_results(self) -> Dict:
        """Load results.

        Returns:
            Dict: Results
        """
        try:
            # Get latest results
            results_files = list(self.results_dir.glob("*.json"))
            if not results_files:
                return {}

            latest_file = max(results_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"Loading results from {latest_file}")

            # Load results
            with open(latest_file) as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Error loading results: {e}")
            return {}

    def _generate_html(
        self,
        results: Dict,
        output: Optional[str] = None
    ) -> None:
        """Generate HTML report.

        Args:
            results: Results
            output: Output file path
        """
        try:
            # Load template
            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(self.templates_dir))
            )
            template = env.get_template("report.html")

            # Generate report
            report = template.render(
                results=results,
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # Save report
            if output:
                output_path = Path(output)
            else:
                output_path = self.reports_dir / f"report_{datetime.now():%Y%m%d_%H%M%S}.html"

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)

            logger.info(f"HTML report generated: {output_path}")

        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            raise

    def _generate_markdown(
        self,
        results: Dict,
        output: Optional[str] = None
    ) -> None:
        """Generate Markdown report.

        Args:
            results: Results
            output: Output file path
        """
        try:
            # Load template
            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(self.templates_dir))
            )
            template = env.get_template("report.md")

            # Generate report
            report = template.render(
                results=results,
                generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            # Save report
            if output:
                output_path = Path(output)
            else:
                output_path = self.reports_dir / f"report_{datetime.now():%Y%m%d_%H%M%S}.md"

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(report)

            logger.info(f"Markdown report generated: {output_path}")

        except Exception as e:
            logger.error(f"Error generating Markdown report: {e}")
            raise

    def _generate_json(
        self,
        results: Dict,
        output: Optional[str] = None
    ) -> None:
        """Generate JSON report.

        Args:
            results: Results
            output: Output file path
        """
        try:
            # Generate report
            report = {
                "results": results,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Save report
            if output:
                output_path = Path(output)
            else:
                output_path = self.reports_dir / f"report_{datetime.now():%Y%m%d_%H%M%S}.json"

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(report, f, indent=2)

            logger.info(f"JSON report generated: {output_path}")

        except Exception as e:
            logger.error(f"Error generating JSON report: {e}")
            raise

def main() -> None:
    """Main entry point."""
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("report.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Parse arguments
        parser = argparse.ArgumentParser(
            description="Generate reports from sniffing results"
        )
        parser.add_argument(
            "--format",
            type=str,
            choices=["html", "markdown", "json"],
            default="html",
            help="Report format"
        )
        parser.add_argument(
            "--output",
            type=str,
            help="Output file path"
        )
        args = parser.parse_args()

        # Generate report
        generator = ReportGenerator()
        generator.generate(
            format=args.format,
            output=args.output
        )

    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
