"""
MCP orchestrator for test scheduling and management.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..utils.config import MCPConfig
from ..utils.logging import setup_logger

logger = logging.getLogger("mcp_orchestrator")

class MCPOrchestrator:
    """Orchestrator for test scheduling and management."""

    def __init__(self, config: MCPConfig):
        """Initialize orchestrator.

        Args:
            config: MCP configuration
        """
        self.config = config
        self.active_jobs: Set[str] = set()
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.metrics: Dict[str, Any] = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for orchestrator."""
        try:
            setup_logger(
                logger,
                self.config.logging_config,
                "mcp_orchestrator"
            )
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")

    async def start(self) -> None:
        """Start the orchestrator."""
        try:
            logger.info("Starting MCP orchestrator...")
            await self._initialize()
            await self._start_job_processor()
            await self._start_metrics_collection()
            logger.info("MCP orchestrator started successfully")

        except Exception as e:
            logger.error(f"Error starting orchestrator: {e}")
            raise

    async def stop(self) -> None:
        """Stop the orchestrator."""
        try:
            logger.info("Stopping MCP orchestrator...")
            await self._cleanup()
            self.active_jobs.clear()
            self.metrics.clear()
            logger.info("MCP orchestrator stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping orchestrator: {e}")
            raise

    async def schedule_job(
        self,
        job_type: str,
        files: List[str],
        domains: List[str],
        priority: int = 0
    ) -> str:
        """Schedule a test job.

        Args:
            job_type: Type of job (sniff, analyze, fix)
            files: Files to process
            domains: Domains to use
            priority: Job priority (0-9, higher is more important)

        Returns:
            Job identifier
        """
        try:
            # Create job
            job_id = f"{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            job = {
                "id": job_id,
                "type": job_type,
                "files": files,
                "domains": domains,
                "priority": priority,
                "status": "queued",
                "timestamp": datetime.now()
            }

            # Add to queue
            await self.job_queue.put((priority, job))
            logger.info(f"Scheduled job: {job_id}")

            return job_id

        except Exception as e:
            logger.error(f"Error scheduling job: {e}")
            raise

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status.

        Args:
            job_id: Job identifier

        Returns:
            Job status dictionary
        """
        try:
            # Check active jobs
            if job_id in self.active_jobs:
                return {
                    "id": job_id,
                    "status": "running",
                    "timestamp": datetime.now()
                }

            # Check completed jobs
            job_dir = Path(self.config.job_path) / job_id
            if job_dir.exists():
                status_file = job_dir / "status.json"
                if status_file.exists():
                    import json
                    with open(status_file) as f:
                        return json.load(f)

            return {
                "id": job_id,
                "status": "not_found",
                "timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return {
                "id": job_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job.

        Args:
            job_id: Job identifier

        Returns:
            Whether job was cancelled
        """
        try:
            # Check active jobs
            if job_id in self.active_jobs:
                # TODO: Implement job cancellation
                self.active_jobs.remove(job_id)
                logger.info(f"Cancelled job: {job_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error cancelling job: {e}")
            return False

    async def _initialize(self) -> None:
        """Initialize orchestrator resources."""
        try:
            # Create job directory
            job_dir = Path(self.config.job_path)
            job_dir.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.error(f"Error initializing orchestrator: {e}")
            raise

    async def _cleanup(self) -> None:
        """Clean up orchestrator resources."""
        try:
            # Clean up any temporary files
            pass

        except Exception as e:
            logger.error(f"Error cleaning up orchestrator: {e}")
            raise

    async def _start_job_processor(self) -> None:
        """Start job processing loop."""
        try:
            while True:
                # Get next job
                priority, job = await self.job_queue.get()
                job_id = job["id"]

                try:
                    # Process job
                    self.active_jobs.add(job_id)
                    await self._process_job(job)

                finally:
                    self.active_jobs.remove(job_id)
                    self.job_queue.task_done()

        except Exception as e:
            logger.error(f"Error processing jobs: {e}")
            if not self.active_jobs:
                # Restart job processor
                asyncio.create_task(self._start_job_processor())

    async def _process_job(self, job: Dict[str, Any]) -> None:
        """Process a job.

        Args:
            job: Job to process
        """
        try:
            job_id = job["id"]
            logger.info(f"Processing job: {job_id}")

            # Update status
            job["status"] = "running"
            job["start_time"] = datetime.now()

            # Run job
            if job["type"] == "sniff":
                results = await self._run_sniffing(job)
            elif job["type"] == "analyze":
                results = await self._run_analysis(job)
            elif job["type"] == "fix":
                results = await self._run_fixes(job)
            else:
                raise ValueError(f"Unknown job type: {job['type']}")

            # Update status
            job["status"] = "completed"
            job["end_time"] = datetime.now()
            job["results"] = results

            # Save results
            await self._save_job_results(job)

            logger.info(f"Completed job: {job_id}")

        except Exception as e:
            logger.error(f"Error processing job: {e}")
            job["status"] = "failed"
            job["error"] = str(e)
            job["end_time"] = datetime.now()
            await self._save_job_results(job)

    async def _run_sniffing(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Run sniffing job.

        Args:
            job: Job configuration

        Returns:
            Sniffing results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "domains": {}
            }

            # Run each domain
            for domain in job["domains"]:
                domain_results = await self._run_domain_sniffing(
                    domain,
                    job["files"]
                )
                results["domains"][domain] = domain_results

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error running sniffing: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_domain_sniffing(
        self,
        domain: str,
        files: List[str]
    ) -> Dict[str, Any]:
        """Run domain-specific sniffing.

        Args:
            domain: Domain name
            files: Files to sniff

        Returns:
            Domain sniffing results
        """
        try:
            # Import domain sniffer
            from sniffing.core.domains import get_sniffer
            sniffer = get_sniffer(domain, self.config)

            # Run sniffing
            return await sniffer.sniff(files)

        except Exception as e:
            logger.error(f"Error running domain sniffing: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_analysis(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Run analysis job.

        Args:
            job: Job configuration

        Returns:
            Analysis results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "domains": {}
            }

            # Run each domain
            for domain in job["domains"]:
                domain_results = await self._run_domain_analysis(
                    domain,
                    job["files"]
                )
                results["domains"][domain] = domain_results

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error running analysis: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_domain_analysis(
        self,
        domain: str,
        files: List[str]
    ) -> Dict[str, Any]:
        """Run domain-specific analysis.

        Args:
            domain: Domain name
            files: Files to analyze

        Returns:
            Domain analysis results
        """
        try:
            # Import domain analyzer
            from sniffing.core.domains import get_analyzer
            analyzer = get_analyzer(domain, self.config)

            # Run analysis
            return await analyzer.analyze(files)

        except Exception as e:
            logger.error(f"Error running domain analysis: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_fixes(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Run fix job.

        Args:
            job: Job configuration

        Returns:
            Fix results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "domains": {}
            }

            # Run each domain
            for domain in job["domains"]:
                domain_results = await self._run_domain_fixes(
                    domain,
                    job["files"]
                )
                results["domains"][domain] = domain_results

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error running fixes: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_domain_fixes(
        self,
        domain: str,
        files: List[str]
    ) -> Dict[str, Any]:
        """Run domain-specific fixes.

        Args:
            domain: Domain name
            files: Files to fix

        Returns:
            Domain fix results
        """
        try:
            # Import domain fixer
            from sniffing.core.domains import get_fixer
            fixer = get_fixer(domain, self.config)

            # Run fixes
            return await fixer.fix(files)

        except Exception as e:
            logger.error(f"Error running domain fixes: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _save_job_results(self, job: Dict[str, Any]) -> None:
        """Save job results.

        Args:
            job: Job results to save
        """
        try:
            # Create job directory
            job_dir = Path(self.config.job_path) / job["id"]
            job_dir.mkdir(parents=True, exist_ok=True)

            # Save status
            status_file = job_dir / "status.json"
            import json
            with open(status_file, "w") as f:
                json.dump(job, f, indent=2, default=str)

            logger.info(f"Saved results for job: {job['id']}")

        except Exception as e:
            logger.error(f"Error saving job results: {e}")
            raise

    async def _start_metrics_collection(self) -> None:
        """Start collecting metrics."""
        try:
            while True:
                # Update metrics
                self.metrics = {
                    "active_jobs": len(self.active_jobs),
                    "queued_jobs": self.job_queue.qsize(),
                    "total_jobs": len(self.active_jobs) + self.job_queue.qsize(),
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

    async def get_health(self) -> Dict[str, Any]:
        """Get orchestrator health.

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
                    "active_jobs": len(self.active_jobs),
                    "queued_jobs": self.job_queue.qsize()
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
        """Get orchestrator metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "metrics": self.metrics,
                "labels": {
                    "component": "orchestrator",
                    "version": "1.0.0"
                },
                "help": {
                    "active_jobs": "Number of active jobs",
                    "queued_jobs": "Number of queued jobs",
                    "total_jobs": "Total number of jobs"
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
