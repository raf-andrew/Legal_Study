"""
Base runner class for test execution.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from ...server.config import ServerConfig

logger = logging.getLogger("base_runner")

class BaseRunner(ABC):
    """Base class for test runners."""

    def __init__(self, domain: str, config: ServerConfig):
        """Initialize base runner.

        Args:
            domain: Domain name
            config: Server configuration
        """
        self.domain = domain
        self.config = config
        self.runner_config = config.get_runner_config(domain)
        self.analyzer = None
        self.active_jobs = set()
        self.metrics = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for runner."""
        try:
            # Get logging config
            log_config = self.config.logging_config
            log_level = log_config.get("level", "INFO")
            log_format = log_config.get("format")

            # Configure logger
            logger.setLevel(log_level)
            if log_format:
                formatter = logging.Formatter(log_format)
                for handler in logger.handlers:
                    handler.setFormatter(formatter)

        except Exception as e:
            logger.error(f"Error setting up logging: {e}")

    async def start(self) -> None:
        """Start the runner."""
        try:
            logger.info(f"Starting {self.domain} runner...")

            # Initialize analyzer
            await self._init_analyzer()

            # Start metrics collection
            asyncio.create_task(self._collect_metrics())

            logger.info(f"{self.domain} runner started successfully")

        except Exception as e:
            logger.error(f"Error starting {self.domain} runner: {e}")
            raise

    async def stop(self) -> None:
        """Stop the runner."""
        try:
            logger.info(f"Stopping {self.domain} runner...")

            # Stop analyzer
            if self.analyzer:
                await self.analyzer.stop()

            # Clear active jobs
            self.active_jobs.clear()

            # Clear metrics
            self.metrics.clear()

            logger.info(f"{self.domain} runner stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping {self.domain} runner: {e}")
            raise

    async def run_tests(self, files: List[str]) -> Dict[str, Any]:
        """Run tests on files.

        Args:
            files: Files to test

        Returns:
            Test results
        """
        try:
            logger.info(f"Running {self.domain} tests on {len(files)} files...")

            # Create job ID
            job_id = f"{self.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_jobs.add(job_id)

            try:
                # Run tests
                start_time = datetime.now()
                results = await self._run_tests(files)
                end_time = datetime.now()

                # Calculate metrics
                duration = (end_time - start_time).total_seconds()
                coverage = self._calculate_coverage(results)

                # Add metrics
                results["metrics"] = {
                    "duration": duration,
                    "coverage": coverage,
                    "files": len(files),
                    "issues": len(results.get("issues", []))
                }

                return results

            finally:
                self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error running {self.domain} tests: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    @abstractmethod
    async def _run_tests(self, files: List[str]) -> Dict[str, Any]:
        """Run domain-specific tests.

        Args:
            files: Files to test

        Returns:
            Test results
        """
        pass

    async def _init_analyzer(self) -> None:
        """Initialize analyzer."""
        try:
            # Import here to avoid circular imports
            from ..analyzers import get_analyzer
            self.analyzer = get_analyzer(self.domain, self.config)
            await self.analyzer.start()

        except Exception as e:
            logger.error(f"Error initializing analyzer: {e}")
            raise

    async def _collect_metrics(self) -> None:
        """Collect runner metrics."""
        try:
            while True:
                # Update metrics
                self.metrics = {
                    "active_jobs": len(self.active_jobs),
                    "total_jobs": len(self.active_jobs),
                    "success_rate": self._calculate_success_rate(),
                    "average_duration": self._calculate_average_duration(),
                    "average_coverage": self._calculate_average_coverage(),
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
                asyncio.create_task(self._collect_metrics())

    def _calculate_coverage(self, results: Dict[str, Any]) -> float:
        """Calculate test coverage.

        Args:
            results: Test results

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

    def _calculate_success_rate(self) -> float:
        """Calculate test success rate.

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

    def _calculate_average_duration(self) -> float:
        """Calculate average test duration.

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

    def _calculate_average_coverage(self) -> float:
        """Calculate average test coverage.

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

    async def get_health(self) -> Dict[str, Any]:
        """Get runner health.

        Returns:
            Health status dictionary
        """
        try:
            # Check analyzer health
            analyzer_health = (
                await self.analyzer.get_health()
                if self.analyzer else {"status": "not_initialized"}
            )

            # Check metrics
            metrics_health = "healthy" if self.metrics else "not_collecting"

            # Calculate overall health
            healthy = all([
                analyzer_health["status"] == "healthy",
                metrics_health == "healthy",
                not self.active_jobs  # No stuck jobs
            ])

            return {
                "status": "healthy" if healthy else "unhealthy",
                "timestamp": datetime.now(),
                "checks": {
                    "analyzer": analyzer_health,
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
        """Get runner metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "metrics": self.metrics,
                "labels": {
                    "domain": self.domain,
                    "runner": self.__class__.__name__
                },
                "help": {
                    "active_jobs": "Number of active test jobs",
                    "total_jobs": "Total number of test jobs",
                    "success_rate": "Test success rate percentage",
                    "average_duration": "Average test duration in seconds",
                    "average_coverage": "Average test coverage percentage"
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
