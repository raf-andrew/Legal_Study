"""
Test scheduler for managing and scheduling test jobs.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .config import ServerConfig
from ..orchestration.queues import PriorityQueue, DomainQueue, FileQueue, AnalysisQueue

logger = logging.getLogger("test_scheduler")

class TestScheduler:
    """Scheduler for managing and executing test jobs."""

    def __init__(self, config: ServerConfig):
        """Initialize test scheduler.

        Args:
            config: Server configuration
        """
        self.config = config
        self.queues = self._init_queues()
        self.active_jobs = set()
        self.running = False
        self._setup_logging()

    def _init_queues(self) -> Dict[str, Any]:
        """Initialize job queues.

        Returns:
            Dictionary of job queues
        """
        return {
            "priority": PriorityQueue(self.config.get_queue_config("priority")),
            "domain": DomainQueue(self.config.get_queue_config("domain")),
            "file": FileQueue(self.config.get_queue_config("file")),
            "analysis": AnalysisQueue(self.config.get_queue_config("analysis"))
        }

    def _setup_logging(self) -> None:
        """Set up logging for test scheduler."""
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
        """Start the test scheduler."""
        try:
            logger.info("Starting test scheduler...")
            self.running = True

            # Start queue processors
            for queue_type, queue in self.queues.items():
                asyncio.create_task(self._process_queue(queue_type, queue))

            logger.info("Test scheduler started successfully")

        except Exception as e:
            logger.error(f"Error starting test scheduler: {e}")
            self.running = False
            raise

    async def stop(self) -> None:
        """Stop the test scheduler."""
        try:
            logger.info("Stopping test scheduler...")
            self.running = False

            # Wait for active jobs to complete
            while self.active_jobs:
                await asyncio.sleep(1)

            # Clear queues
            for queue in self.queues.values():
                await queue.clear()

            logger.info("Test scheduler stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping test scheduler: {e}")
            raise

    async def schedule(self, job: Dict[str, Any]) -> None:
        """Schedule a test job.

        Args:
            job: Job to schedule
        """
        try:
            # Determine queue
            queue_type = self._get_queue_type(job)
            queue = self.queues[queue_type]

            # Add to queue
            await queue.put(job)

            logger.info(f"Scheduled job {job['id']} in {queue_type} queue")

        except Exception as e:
            logger.error(f"Error scheduling job: {e}")
            raise

    def _get_queue_type(self, job: Dict[str, Any]) -> str:
        """Get queue type for job.

        Args:
            job: Job to get queue type for

        Returns:
            Queue type string
        """
        request = job["request"]

        # Check priority
        if job["priority"] >= 8:
            return "priority"

        # Check domains
        if request.get("domains"):
            return "domain"

        # Check files
        if request.get("files"):
            return "file"

        # Default to analysis
        return "analysis"

    async def _process_queue(self, queue_type: str, queue: Any) -> None:
        """Process jobs in queue.

        Args:
            queue_type: Type of queue
            queue: Queue to process
        """
        try:
            while self.running:
                # Get next job
                job = await queue.get()
                if not job:
                    continue

                # Process job
                try:
                    self.active_jobs.add(job["id"])
                    await self._process_job(job)
                finally:
                    self.active_jobs.remove(job["id"])
                    queue.task_done()

        except Exception as e:
            logger.error(f"Error processing {queue_type} queue: {e}")
            if self.running:
                # Restart queue processor
                asyncio.create_task(self._process_queue(queue_type, queue))

    async def _process_job(self, job: Dict[str, Any]) -> None:
        """Process a test job.

        Args:
            job: Job to process
        """
        try:
            logger.info(f"Processing job {job['id']}")

            # Update job status
            job["status"] = "running"
            job["started_at"] = datetime.now()

            # Run job
            result = await self._run_job(job)

            # Update job status
            job["status"] = "completed"
            job["completed_at"] = datetime.now()
            job["result"] = result

            logger.info(f"Completed job {job['id']}")

        except Exception as e:
            logger.error(f"Error processing job {job['id']}: {e}")
            job["status"] = "failed"
            job["error"] = str(e)
            job["completed_at"] = datetime.now()

    async def _run_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Run a test job.

        Args:
            job: Job to run

        Returns:
            Job result dictionary
        """
        try:
            # Import here to avoid circular imports
            from .orchestrator import TestOrchestrator
            orchestrator = TestOrchestrator(self.config)

            # Run job
            return await orchestrator.run_job(job)

        except Exception as e:
            logger.error(f"Error running job {job['id']}: {e}")
            raise

    def get_queue_status(self) -> Dict[str, Any]:
        """Get status of all queues.

        Returns:
            Queue status dictionary
        """
        return {
            queue_type: {
                "size": queue.qsize(),
                "active": len([j for j in self.active_jobs if self._get_queue_type(j) == queue_type])
            }
            for queue_type, queue in self.queues.items()
        }

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a job.

        Args:
            job_id: ID of job to get status for

        Returns:
            Job status dictionary or None if not found
        """
        # Check active jobs
        for job in self.active_jobs:
            if job["id"] == job_id:
                return job

        # Check queues
        for queue in self.queues.values():
            for job in queue._queue:
                if job["id"] == job_id:
                    return job

        return None
