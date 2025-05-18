"""
Base sniffer class providing core sniffing functionality.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..utils.config import SnifferConfig
from ..utils.logging import setup_logger

logger = logging.getLogger("base_sniffer")

class BaseSniffer(ABC):
    """Base class for all sniffers."""

    def __init__(self, domain: str, config: SnifferConfig):
        """Initialize base sniffer.

        Args:
            domain: Domain name
            config: Sniffer configuration
        """
        self.domain = domain
        self.config = config
        self.active_jobs: Set[str] = set()
        self.metrics: Dict[str, Any] = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for sniffer."""
        try:
            setup_logger(
                logger,
                self.config.logging_config,
                f"{self.domain}_sniffer"
            )
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")

    async def start(self) -> None:
        """Start the sniffer."""
        try:
            logger.info(f"Starting {self.domain} sniffer...")
            await self._initialize()
            await self._start_metrics_collection()
            logger.info(f"{self.domain} sniffer started successfully")

        except Exception as e:
            logger.error(f"Error starting {self.domain} sniffer: {e}")
            raise

    async def stop(self) -> None:
        """Stop the sniffer."""
        try:
            logger.info(f"Stopping {self.domain} sniffer...")
            await self._cleanup()
            self.active_jobs.clear()
            self.metrics.clear()
            logger.info(f"{self.domain} sniffer stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping {self.domain} sniffer: {e}")
            raise

    async def sniff(self, files: List[str]) -> Dict[str, Any]:
        """Run sniffing on files.

        Args:
            files: Files to sniff

        Returns:
            Sniffing results
        """
        try:
            logger.info(f"Sniffing {len(files)} files...")
            job_id = f"{self.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_jobs.add(job_id)

            try:
                # Run sniffing
                start_time = datetime.now()
                results = await self._sniff_files(files)
                end_time = datetime.now()

                # Calculate metrics
                duration = (end_time - start_time).total_seconds()
                coverage = await self._calculate_coverage(results)

                # Add metrics
                results["metrics"] = {
                    "duration": duration,
                    "coverage": coverage,
                    "files": len(files),
                    "issues": len(results.get("issues", []))
                }

                # Generate report
                await self._generate_report(job_id, results)

                return results

            finally:
                self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error sniffing files: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    @abstractmethod
    async def _sniff_files(self, files: List[str]) -> Dict[str, Any]:
        """Run domain-specific sniffing.

        Args:
            files: Files to sniff

        Returns:
            Sniffing results
        """
        pass

    async def _initialize(self) -> None:
        """Initialize sniffer resources."""
        try:
            # Create report directory
            report_dir = Path(self.config.report_path) / self.domain
            report_dir.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.error(f"Error initializing sniffer: {e}")
            raise

    async def _cleanup(self) -> None:
        """Clean up sniffer resources."""
        try:
            # Clean up any temporary files
            pass

        except Exception as e:
            logger.error(f"Error cleaning up sniffer: {e}")
            raise

    async def _start_metrics_collection(self) -> None:
        """Start collecting metrics."""
        try:
            while True:
                # Update metrics
                self.metrics = {
                    "active_jobs": len(self.active_jobs),
                    "total_jobs": len(self.active_jobs),
                    "success_rate": await self._calculate_success_rate(),
                    "average_duration": await self._calculate_average_duration(),
                    "average_coverage": await self._calculate_average_coverage(),
                    "timestamp": datetime.now()
                }

                # Wait for next collection
                await asyncio.sleep(
                    self.config.monitoring_config["collection_interval"]
                )

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            if not self.active_jobs:
                # Restart metrics collection
                asyncio.create_task(self._start_metrics_collection())

    async def _calculate_coverage(self, results: Dict[str, Any]) -> float:
        """Calculate sniffing coverage.

        Args:
            results: Sniffing results

        Returns:
            Coverage percentage
        """
        try:
            # Get coverage data
            coverage_data = results.get("coverage", {})
            if not coverage_data:
                return 0.0

            # Calculate coverage
            total_lines = coverage_data.get("total_lines", 0)
            covered_lines = coverage_data.get("covered_lines", 0)

            return (covered_lines / total_lines * 100) if total_lines > 0 else 0.0

        except Exception as e:
            logger.error(f"Error calculating coverage: {e}")
            return 0.0

    async def _calculate_success_rate(self) -> float:
        """Calculate sniffing success rate.

        Returns:
            Success rate percentage
        """
        try:
            # Get job history
            history = self.metrics.get("job_history", [])
            if not history:
                return 0.0

            # Calculate success rate
            successful = sum(1 for job in history if job["status"] == "completed")
            return (successful / len(history) * 100)

        except Exception as e:
            logger.error(f"Error calculating success rate: {e}")
            return 0.0

    async def _calculate_average_duration(self) -> float:
        """Calculate average sniffing duration.

        Returns:
            Average duration in seconds
        """
        try:
            # Get job history
            history = self.metrics.get("job_history", [])
            if not history:
                return 0.0

            # Calculate average duration
            durations = [
                job["metrics"]["duration"]
                for job in history
                if job.get("metrics", {}).get("duration")
            ]
            return sum(durations) / len(durations) if durations else 0.0

        except Exception as e:
            logger.error(f"Error calculating average duration: {e}")
            return 0.0

    async def _calculate_average_coverage(self) -> float:
        """Calculate average sniffing coverage.

        Returns:
            Average coverage percentage
        """
        try:
            # Get job history
            history = self.metrics.get("job_history", [])
            if not history:
                return 0.0

            # Calculate average coverage
            coverages = [
                job["metrics"]["coverage"]
                for job in history
                if job.get("metrics", {}).get("coverage")
            ]
            return sum(coverages) / len(coverages) if coverages else 0.0

        except Exception as e:
            logger.error(f"Error calculating average coverage: {e}")
            return 0.0

    async def _generate_report(
        self,
        job_id: str,
        results: Dict[str, Any]
    ) -> None:
        """Generate sniffing report.

        Args:
            job_id: Job identifier
            results: Sniffing results
        """
        try:
            # Get report path
            report_dir = Path(self.config.report_path) / self.domain
            report_path = report_dir / f"{job_id}.json"

            # Write report
            import json
            with open(report_path, "w") as f:
                json.dump(results, f, indent=2, default=str)

            logger.info(f"Generated report: {report_path}")

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise

    async def get_health(self) -> Dict[str, Any]:
        """Get sniffer health.

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
        """Get sniffer metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "metrics": self.metrics,
                "labels": {
                    "domain": self.domain,
                    "sniffer": self.__class__.__name__
                },
                "help": {
                    "active_jobs": "Number of active sniffing jobs",
                    "total_jobs": "Total number of sniffing jobs",
                    "success_rate": "Sniffing success rate percentage",
                    "average_duration": "Average sniffing duration in seconds",
                    "average_coverage": "Average sniffing coverage percentage"
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
