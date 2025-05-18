"""
Base reporter class providing core reporting functionality.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..utils.config import SnifferConfig
from ..utils.logging import setup_logger

logger = logging.getLogger("base_reporter")

class BaseReporter(ABC):
    """Base class for all reporters."""

    def __init__(self, domain: str, config: SnifferConfig):
        """Initialize base reporter.

        Args:
            domain: Domain name
            config: Reporter configuration
        """
        self.domain = domain
        self.config = config
        self.active_jobs: Set[str] = set()
        self.metrics: Dict[str, Any] = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for reporter."""
        try:
            setup_logger(
                logger,
                self.config.logging_config,
                f"{self.domain}_reporter"
            )
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")

    async def start(self) -> None:
        """Start the reporter."""
        try:
            logger.info(f"Starting {self.domain} reporter...")
            await self._initialize()
            await self._start_metrics_collection()
            logger.info(f"{self.domain} reporter started successfully")

        except Exception as e:
            logger.error(f"Error starting {self.domain} reporter: {e}")
            raise

    async def stop(self) -> None:
        """Stop the reporter."""
        try:
            logger.info(f"Stopping {self.domain} reporter...")
            await self._cleanup()
            self.active_jobs.clear()
            self.metrics.clear()
            logger.info(f"{self.domain} reporter stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping {self.domain} reporter: {e}")
            raise

    async def generate_report(
        self,
        results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate report from results and analysis.

        Args:
            results: Sniffing results
            analysis: Analysis results

        Returns:
            Generated report
        """
        try:
            logger.info(f"Generating {self.domain} report...")
            job_id = f"{self.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_jobs.add(job_id)

            try:
                # Generate report
                start_time = datetime.now()
                report = await self._generate_report(results, analysis)
                end_time = datetime.now()

                # Calculate metrics
                duration = (end_time - start_time).total_seconds()
                quality = await self._calculate_quality(report)

                # Add metrics
                report["metrics"] = {
                    "duration": duration,
                    "quality": quality,
                    "results": len(results),
                    "findings": len(analysis.get("findings", []))
                }

                # Save report
                await self._save_report(job_id, report)

                return report

            finally:
                self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    @abstractmethod
    async def _generate_report(
        self,
        results: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate domain-specific report.

        Args:
            results: Sniffing results
            analysis: Analysis results

        Returns:
            Generated report
        """
        pass

    async def _initialize(self) -> None:
        """Initialize reporter resources."""
        try:
            # Create report directories
            report_dir = Path(self.config.report_path) / self.domain
            for subdir in ["html", "json", "pdf", "csv"]:
                (report_dir / subdir).mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.error(f"Error initializing reporter: {e}")
            raise

    async def _cleanup(self) -> None:
        """Clean up reporter resources."""
        try:
            # Clean up any temporary files
            pass

        except Exception as e:
            logger.error(f"Error cleaning up reporter: {e}")
            raise

    async def _calculate_quality(self, report: Dict[str, Any]) -> float:
        """Calculate report quality.

        Args:
            report: Generated report

        Returns:
            Quality score between 0 and 1
        """
        try:
            # Get sections
            sections = report.get("sections", [])
            if not sections:
                return 0.0

            # Calculate average quality
            qualities = [
                section.get("quality", 0.0)
                for section in sections
            ]
            return sum(qualities) / len(qualities)

        except Exception as e:
            logger.error(f"Error calculating quality: {e}")
            return 0.0

    async def _save_report(
        self,
        job_id: str,
        report: Dict[str, Any]
    ) -> None:
        """Save report in multiple formats.

        Args:
            job_id: Job identifier
            report: Report to save
        """
        try:
            # Get report directory
            report_dir = Path(self.config.report_path) / self.domain

            # Save JSON
            json_path = report_dir / "json" / f"{job_id}.json"
            import json
            with open(json_path, "w") as f:
                json.dump(report, f, indent=2, default=str)

            # Save HTML
            html_path = report_dir / "html" / f"{job_id}.html"
            await self._save_html(html_path, report)

            # Save PDF
            pdf_path = report_dir / "pdf" / f"{job_id}.pdf"
            await self._save_pdf(pdf_path, report)

            # Save CSV
            csv_path = report_dir / "csv" / f"{job_id}.csv"
            await self._save_csv(csv_path, report)

            logger.info(f"Saved report: {job_id}")

        except Exception as e:
            logger.error(f"Error saving report: {e}")
            raise

    async def _save_html(
        self,
        path: Path,
        report: Dict[str, Any]
    ) -> None:
        """Save report as HTML.

        Args:
            path: Path to save to
            report: Report to save
        """
        try:
            # Convert report to HTML
            html = await self._convert_to_html(report)

            # Write HTML
            with open(path, "w") as f:
                f.write(html)

        except Exception as e:
            logger.error(f"Error saving HTML: {e}")
            raise

    async def _save_pdf(
        self,
        path: Path,
        report: Dict[str, Any]
    ) -> None:
        """Save report as PDF.

        Args:
            path: Path to save to
            report: Report to save
        """
        try:
            # Convert report to PDF
            pdf = await self._convert_to_pdf(report)

            # Write PDF
            with open(path, "wb") as f:
                f.write(pdf)

        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            raise

    async def _save_csv(
        self,
        path: Path,
        report: Dict[str, Any]
    ) -> None:
        """Save report as CSV.

        Args:
            path: Path to save to
            report: Report to save
        """
        try:
            # Convert report to CSV
            csv = await self._convert_to_csv(report)

            # Write CSV
            with open(path, "w") as f:
                f.write(csv)

        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            raise

    async def _convert_to_html(self, report: Dict[str, Any]) -> str:
        """Convert report to HTML.

        Args:
            report: Report to convert

        Returns:
            HTML string
        """
        try:
            # Import here to avoid circular imports
            from jinja2 import Environment, PackageLoader

            # Load template
            env = Environment(
                loader=PackageLoader("sniffing.core.templates", "reports")
            )
            template = env.get_template(f"{self.domain}.html")

            # Render template
            return template.render(report=report)

        except Exception as e:
            logger.error(f"Error converting to HTML: {e}")
            raise

    async def _convert_to_pdf(self, report: Dict[str, Any]) -> bytes:
        """Convert report to PDF.

        Args:
            report: Report to convert

        Returns:
            PDF bytes
        """
        try:
            # Import here to avoid circular imports
            from weasyprint import HTML

            # Convert to HTML first
            html = await self._convert_to_html(report)

            # Convert HTML to PDF
            return HTML(string=html).write_pdf()

        except Exception as e:
            logger.error(f"Error converting to PDF: {e}")
            raise

    async def _convert_to_csv(self, report: Dict[str, Any]) -> str:
        """Convert report to CSV.

        Args:
            report: Report to convert

        Returns:
            CSV string
        """
        try:
            # Import here to avoid circular imports
            import csv
            import io

            # Create CSV buffer
            output = io.StringIO()
            writer = csv.writer(output)

            # Write headers
            headers = ["Section", "Finding", "Severity", "Description"]
            writer.writerow(headers)

            # Write findings
            for section in report.get("sections", []):
                for finding in section.get("findings", []):
                    writer.writerow([
                        section.get("name", ""),
                        finding.get("name", ""),
                        finding.get("severity", ""),
                        finding.get("description", "")
                    ])

            return output.getvalue()

        except Exception as e:
            logger.error(f"Error converting to CSV: {e}")
            raise

    async def get_health(self) -> Dict[str, Any]:
        """Get reporter health.

        Returns:
            Health status dictionary
        """
        try:
            # Check metrics
            metrics_health = "healthy" if self.metrics else "not_collecting"

            # Calculate overall health
            healthy = all([
                metrics_health == "healthy",
                not self.active_jobs  # No stuck jobs
            ])

            return {
                "status": "healthy" if healthy else "unhealthy",
                "timestamp": datetime.now(),
                "checks": {
                    "metrics": metrics_health,
                    "active_jobs": len(self.active_jobs)
                },
                "metrics": self.metrics
            }

        except Exception as e:
            logger.error(f"Error getting health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get reporter metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "metrics": self.metrics,
                "labels": {
                    "domain": self.domain,
                    "reporter": self.__class__.__name__
                },
                "help": {
                    "active_jobs": "Number of active report jobs",
                    "total_jobs": "Total number of report jobs",
                    "success_rate": "Report generation success rate percentage",
                    "average_duration": "Average report generation duration in seconds",
                    "average_quality": "Average report quality score"
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
