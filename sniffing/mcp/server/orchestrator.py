"""
Test orchestrator for managing test execution and coordination.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .config import ServerConfig
from ..orchestration.runners import get_runner
from ..orchestration.results import ResultManager

logger = logging.getLogger("test_orchestrator")

class TestOrchestrator:
    """Orchestrator for managing test execution."""

    def __init__(self, config: ServerConfig):
        """Initialize test orchestrator.

        Args:
            config: Server configuration
        """
        self.config = config
        self.runners = self._init_runners()
        self.results = ResultManager(config)
        self.active_jobs = set()
        self._setup_logging()

    def _init_runners(self) -> Dict[str, Any]:
        """Initialize test runners.

        Returns:
            Dictionary of test runners
        """
        runners = {}
        for domain in self.config.domains:
            runners[domain] = get_runner(domain, self.config)
        return runners

    def _setup_logging(self) -> None:
        """Set up logging for test orchestrator."""
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

    async def run_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Run a test job.

        Args:
            job: Job to run

        Returns:
            Job result dictionary
        """
        try:
            logger.info(f"Running job {job['id']}")
            self.active_jobs.add(job["id"])

            # Get job details
            request = job["request"]
            domains = request.get("domains", self.config.domains)
            files = request.get("files", [])

            # Run tests
            results = {}
            for domain in domains:
                domain_results = await self._run_domain_tests(domain, files)
                results[domain] = domain_results

            # Aggregate results
            aggregated = await self._aggregate_results(results)

            # Store results
            await self.results.store(job["id"], aggregated)

            return aggregated

        except Exception as e:
            logger.error(f"Error running job {job['id']}: {e}")
            raise

        finally:
            self.active_jobs.remove(job["id"])

    async def _run_domain_tests(
        self,
        domain: str,
        files: List[str]
    ) -> Dict[str, Any]:
        """Run tests for a domain.

        Args:
            domain: Domain to run tests for
            files: Files to test

        Returns:
            Domain test results
        """
        try:
            logger.info(f"Running {domain} tests...")

            # Get runner
            runner = self.runners.get(domain)
            if not runner:
                raise ValueError(f"Runner not found for domain: {domain}")

            # Run tests
            results = await runner.run_tests(files)

            # Process results
            processed = await self._process_results(domain, results)

            return processed

        except Exception as e:
            logger.error(f"Error running {domain} tests: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _process_results(
        self,
        domain: str,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process test results.

        Args:
            domain: Domain results are for
            results: Results to process

        Returns:
            Processed results
        """
        try:
            # Get analyzer
            analyzer = self.runners[domain].analyzer
            if not analyzer:
                return results

            # Analyze results
            analysis = await analyzer.analyze(results)

            # Generate fixes
            fixes = await analyzer.generate_fixes(analysis)

            # Add to results
            results["analysis"] = analysis
            results["fixes"] = fixes

            return results

        except Exception as e:
            logger.error(f"Error processing {domain} results: {e}")
            return results

    async def _aggregate_results(
        self,
        results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate test results.

        Args:
            results: Results to aggregate

        Returns:
            Aggregated results
        """
        try:
            # Calculate overall status
            status = all(
                r.get("status") == "completed"
                for r in results.values()
            )

            # Count issues
            issues = {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }

            for domain_results in results.values():
                domain_issues = domain_results.get("issues", [])
                issues["total"] += len(domain_issues)
                for issue in domain_issues:
                    severity = issue.get("severity", "low")
                    issues[severity] += 1

            # Calculate metrics
            metrics = {
                "duration": sum(
                    r.get("metrics", {}).get("duration", 0)
                    for r in results.values()
                ),
                "coverage": sum(
                    r.get("metrics", {}).get("coverage", 0)
                    for r in results.values()
                ) / len(results) if results else 0
            }

            return {
                "status": "completed" if status else "failed",
                "timestamp": datetime.now(),
                "results": results,
                "issues": issues,
                "metrics": metrics
            }

        except Exception as e:
            logger.error(f"Error aggregating results: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    def get_active_jobs(self) -> Set[str]:
        """Get active jobs.

        Returns:
            Set of active job IDs
        """
        return self.active_jobs.copy()

    def get_runner_status(self, domain: str) -> Dict[str, Any]:
        """Get status of a runner.

        Args:
            domain: Domain to get runner status for

        Returns:
            Runner status dictionary
        """
        runner = self.runners.get(domain)
        if not runner:
            return {
                "status": "not_found",
                "error": f"Runner not found for domain: {domain}"
            }

        return runner.get_status()

    def get_all_runner_status(self) -> Dict[str, Any]:
        """Get status of all runners.

        Returns:
            Dictionary of runner status dictionaries
        """
        return {
            domain: runner.get_status()
            for domain, runner in self.runners.items()
        }

    async def cleanup(self) -> None:
        """Clean up orchestrator resources."""
        try:
            # Stop runners
            for runner in self.runners.values():
                await runner.stop()

            # Clear results
            await self.results.clear()

            # Clear active jobs
            self.active_jobs.clear()

        except Exception as e:
            logger.error(f"Error cleaning up orchestrator: {e}")
            raise
