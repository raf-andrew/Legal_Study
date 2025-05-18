"""
Result manager for sniffing results and reporting.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ...utils.config import MCPConfig
from ...utils.logging import setup_logger
from ...utils.metrics import record_job_start, record_job_end
from ..domains import get_analyzer

logger = logging.getLogger("result_manager")

class ResultManager:
    """Manages sniffing results and reporting."""

    def __init__(self, config: MCPConfig):
        """Initialize result manager.

        Args:
            config: MCP configuration
        """
        self.config = config
        self.results = {}
        self.reports = {}
        self.active_jobs = set()
        self.report_queue = asyncio.Queue()
        self.is_running = False
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for result manager."""
        setup_logger(logger, self.config.logging_config, "result_manager")

    async def start(self) -> None:
        """Start result manager."""
        try:
            logger.info("Starting result manager")
            self.is_running = True

            # Start report worker
            report_worker = asyncio.create_task(self._report_worker())
            await report_worker

        except Exception as e:
            logger.error(f"Error starting result manager: {e}")
            self.is_running = False

    async def stop(self) -> None:
        """Stop result manager."""
        try:
            logger.info("Stopping result manager")
            self.is_running = False

            # Wait for queue to empty
            await self.report_queue.join()

            # Wait for jobs to complete
            while self.active_jobs:
                await asyncio.sleep(0.1)

            logger.info("Result manager stopped")

        except Exception as e:
            logger.error(f"Error stopping result manager: {e}")

    async def store_result(
        self,
        result_id: str,
        result: Dict[str, Any]
    ) -> None:
        """Store sniffing result.

        Args:
            result_id: Result identifier
            result: Result data
        """
        try:
            # Store result
            self.results[result_id] = {
                "data": result,
                "timestamp": datetime.now()
            }

            # Add to report queue
            await self.report_queue.put({
                "id": result_id,
                "type": "result",
                "data": result,
                "timestamp": datetime.now()
            })

            logger.info(f"Stored result: {result_id}")

        except Exception as e:
            logger.error(f"Error storing result: {e}")

    async def store_report(
        self,
        report_id: str,
        report: Dict[str, Any]
    ) -> None:
        """Store generated report.

        Args:
            report_id: Report identifier
            report: Report data
        """
        try:
            # Store report
            self.reports[report_id] = {
                "data": report,
                "timestamp": datetime.now()
            }

            # Add to report queue
            await self.report_queue.put({
                "id": report_id,
                "type": "report",
                "data": report,
                "timestamp": datetime.now()
            })

            logger.info(f"Stored report: {report_id}")

        except Exception as e:
            logger.error(f"Error storing report: {e}")

    async def get_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get stored result.

        Args:
            result_id: Result identifier

        Returns:
            Result data or None
        """
        try:
            result = self.results.get(result_id)
            return result["data"] if result else None

        except Exception as e:
            logger.error(f"Error getting result: {e}")
            return None

    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get stored report.

        Args:
            report_id: Report identifier

        Returns:
            Report data or None
        """
        try:
            report = self.reports.get(report_id)
            return report["data"] if report else None

        except Exception as e:
            logger.error(f"Error getting report: {e}")
            return None

    async def _report_worker(self) -> None:
        """Process reports from queue."""
        try:
            while self.is_running:
                # Get item from queue
                item = await self.report_queue.get()
                item_id = item["id"]
                item_type = item["type"]
                data = item["data"]

                try:
                    # Record job start
                    record_job_start("result_manager", f"report_{item_type}")

                    # Process item
                    if item_type == "result":
                        await self._process_result(item_id, data)
                    elif item_type == "report":
                        await self._process_report(item_id, data)

                    # Record job end
                    record_job_end(
                        "result_manager",
                        f"report_{item_type}",
                        datetime.now().timestamp() - item["timestamp"].timestamp(),
                        True
                    )

                except Exception as e:
                    logger.error(f"Error processing {item_type} {item_id}: {e}")
                    record_job_end(
                        "result_manager",
                        f"report_{item_type}",
                        datetime.now().timestamp() - item["timestamp"].timestamp(),
                        False
                    )

                finally:
                    # Mark task as done
                    self.report_queue.task_done()

        except Exception as e:
            logger.error(f"Error in report worker: {e}")

    async def _process_result(
        self,
        result_id: str,
        result: Dict[str, Any]
    ) -> None:
        """Process sniffing result.

        Args:
            result_id: Result identifier
            result: Result data
        """
        try:
            # Create result directory
            result_dir = Path(self.config.report_path) / "results" / result_id
            result_dir.mkdir(parents=True, exist_ok=True)

            # Save result
            result_file = result_dir / "result.json"
            import json
            with open(result_file, "w") as f:
                json.dump(result, f, indent=2)

            # Analyze result
            analysis = await self._analyze_result(result)

            # Save analysis
            analysis_file = result_dir / "analysis.json"
            with open(analysis_file, "w") as f:
                json.dump(analysis, f, indent=2)

            logger.info(f"Processed result: {result_id}")

        except Exception as e:
            logger.error(f"Error processing result: {e}")

    async def _process_report(
        self,
        report_id: str,
        report: Dict[str, Any]
    ) -> None:
        """Process generated report.

        Args:
            report_id: Report identifier
            report: Report data
        """
        try:
            # Create report directory
            report_dir = Path(self.config.report_path) / "reports" / report_id
            report_dir.mkdir(parents=True, exist_ok=True)

            # Save report
            report_file = report_dir / "report.json"
            import json
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

            # Generate summary
            summary = await self._generate_summary(report)

            # Save summary
            summary_file = report_dir / "summary.json"
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)

            logger.info(f"Processed report: {report_id}")

        except Exception as e:
            logger.error(f"Error processing report: {e}")

    async def _analyze_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sniffing result.

        Args:
            result: Result data

        Returns:
            Analysis data
        """
        try:
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "domains": {}
            }

            # Analyze each domain
            for domain, domain_result in result.items():
                # Get domain analyzer
                analyzer = get_analyzer(domain, self.config)
                if not analyzer:
                    continue

                # Run analysis
                domain_analysis = await analyzer.analyze(domain_result)
                analysis["domains"][domain] = domain_analysis

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing result: {e}")
            return {}

    async def _generate_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate report summary.

        Args:
            report: Report data

        Returns:
            Summary data
        """
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "status": report.get("status"),
                "issues": self._count_issues(report),
                "coverage": self._calculate_coverage(report),
                "metrics": self._extract_metrics(report)
            }

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}

    def _count_issues(self, report: Dict[str, Any]) -> Dict[str, int]:
        """Count issues by severity.

        Args:
            report: Report data

        Returns:
            Issue counts
        """
        try:
            counts = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0
            }

            # Count issues
            for domain in report.get("domains", {}).values():
                for issue in domain.get("issues", []):
                    severity = issue.get("severity", "info").lower()
                    if severity in counts:
                        counts[severity] += 1

            return counts

        except Exception as e:
            logger.error(f"Error counting issues: {e}")
            return {}

    def _calculate_coverage(self, report: Dict[str, Any]) -> Dict[str, float]:
        """Calculate coverage metrics.

        Args:
            report: Report data

        Returns:
            Coverage metrics
        """
        try:
            coverage = {}

            # Calculate coverage
            for domain, domain_data in report.get("domains", {}).items():
                metrics = domain_data.get("metrics", {})
                if "coverage" in metrics:
                    coverage[domain] = metrics["coverage"]

            return coverage

        except Exception as e:
            logger.error(f"Error calculating coverage: {e}")
            return {}

    def _extract_metrics(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance metrics.

        Args:
            report: Report data

        Returns:
            Performance metrics
        """
        try:
            metrics = {}

            # Extract metrics
            for domain, domain_data in report.get("domains", {}).items():
                domain_metrics = domain_data.get("metrics", {})
                if domain_metrics:
                    metrics[domain] = {
                        k: v for k, v in domain_metrics.items()
                        if k not in ["coverage"]
                    }

            return metrics

        except Exception as e:
            logger.error(f"Error extracting metrics: {e}")
            return {}

    def get_metrics(self) -> Dict[str, Any]:
        """Get manager metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "stored_results": len(self.results),
                "stored_reports": len(self.reports),
                "queued_items": self.report_queue.qsize(),
                "active_jobs": len(self.active_jobs)
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
