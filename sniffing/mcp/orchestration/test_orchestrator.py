"""
Enhanced test orchestrator for managing and scheduling sniffing operations.
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ...core.utils.result import SniffingResult
from ...domains.security.security_sniffer import SecuritySniffer
from ...domains.browser.browser_sniffer import BrowserSniffer
from ...domains.functional.functional_sniffer import FunctionalSniffer
from ...domains.unit.unit_sniffer import UnitSniffer
from ...domains.documentation.documentation_sniffer import DocumentationSniffer

logger = logging.getLogger("test_orchestrator")

@dataclass
class TestJob:
    """Test job data class."""
    id: str
    files: List[str]
    domains: List[str]
    priority: int
    fix: bool
    created_at: datetime
    status: str = "pending"
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class TestOrchestrator:
    """Enhanced test orchestrator for managing sniffing operations."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize test orchestrator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.job_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_jobs: Dict[str, TestJob] = {}
        self.completed_jobs: Dict[str, TestJob] = {}
        self.domain_locks: Dict[str, asyncio.Lock] = {}
        self.file_locks: Dict[str, asyncio.Lock] = {}
        self.sniffers = self._initialize_sniffers()
        self.max_concurrent_jobs = config.get("orchestration", {}).get("max_concurrent_jobs", 4)
        self.job_semaphore = asyncio.Semaphore(self.max_concurrent_jobs)
        self._setup_domain_locks()

    def _initialize_sniffers(self) -> Dict[str, Any]:
        """Initialize domain-specific sniffers.

        Returns:
            Dictionary of initialized sniffers
        """
        try:
            return {
                "security": SecuritySniffer(self.config["domains"]["security"]),
                "browser": BrowserSniffer(self.config["domains"]["browser"]),
                "functional": FunctionalSniffer(self.config["domains"]["functional"]),
                "unit": UnitSniffer(self.config["domains"]["unit"]),
                "documentation": DocumentationSniffer(self.config["domains"]["documentation"])
            }
        except Exception as e:
            logger.error(f"Error initializing sniffers: {e}")
            raise

    def _setup_domain_locks(self) -> None:
        """Set up locks for each domain."""
        for domain in self.sniffers:
            self.domain_locks[domain] = asyncio.Lock()

    async def run_tests(
        self,
        files: List[str],
        domains: Optional[List[str]] = None,
        priority: int = 1,
        fix: bool = True
    ) -> Dict[str, Any]:
        """Run tests on specified files.

        Args:
            files: List of files to test
            domains: Optional list of domains to test
            priority: Job priority (lower is higher priority)
            fix: Whether to fix issues

        Returns:
            Test results
        """
        try:
            # Create job
            job = TestJob(
                id=f"job_{len(self.active_jobs)}",
                files=files,
                domains=domains or list(self.sniffers.keys()),
                priority=priority,
                fix=fix,
                created_at=datetime.now()
            )

            # Queue job
            await self.job_queue.put((priority, job))
            self.active_jobs[job.id] = job

            # Process job
            results = await self._process_job(job)

            # Update job status
            job.status = "completed"
            job.results = results
            self.completed_jobs[job.id] = job
            del self.active_jobs[job.id]

            return {
                "job_id": job.id,
                "status": "completed",
                "results": results
            }

        except Exception as e:
            logger.error(f"Error running tests: {e}")
            if job.id in self.active_jobs:
                job.status = "failed"
                job.error = str(e)
                self.completed_jobs[job.id] = job
                del self.active_jobs[job.id]
            return {
                "status": "failed",
                "error": str(e)
            }

    async def _process_job(self, job: TestJob) -> Dict[str, Any]:
        """Process a test job.

        Args:
            job: Test job to process

        Returns:
            Test results
        """
        try:
            async with self.job_semaphore:
                results = {}

                # Process each file
                for file in job.files:
                    # Get or create file lock
                    if file not in self.file_locks:
                        self.file_locks[file] = asyncio.Lock()

                    async with self.file_locks[file]:
                        file_results = {}

                        # Process each domain
                        for domain in job.domains:
                            if domain not in self.sniffers:
                                continue

                            sniffer = self.sniffers[domain]
                            if not sniffer.config.get("enabled", True):
                                continue

                            async with self.domain_locks[domain]:
                                # Run sniffing
                                result = await sniffer.sniff_file(file)
                                file_results[domain] = result.to_dict()

                                # Fix issues if requested
                                if job.fix and result.has_issues():
                                    await sniffer.fix_issues(result.issues)

                        results[file] = file_results

                return results

        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}")
            raise

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of a job.

        Args:
            job_id: Job ID to check

        Returns:
            Job status information
        """
        try:
            # Check active jobs
            if job_id in self.active_jobs:
                job = self.active_jobs[job_id]
                return {
                    "job_id": job.id,
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "files": len(job.files),
                    "domains": job.domains
                }

            # Check completed jobs
            if job_id in self.completed_jobs:
                job = self.completed_jobs[job_id]
                return {
                    "job_id": job.id,
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "completed_at": datetime.now().isoformat(),
                    "files": len(job.files),
                    "domains": job.domains,
                    "results": job.results,
                    "error": job.error
                }

            return {
                "status": "not_found",
                "job_id": job_id
            }

        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return {
                "status": "error",
                "job_id": job_id,
                "error": str(e)
            }

    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a job.

        Args:
            job_id: Job ID to cancel

        Returns:
            Cancellation status
        """
        try:
            if job_id not in self.active_jobs:
                return {
                    "status": "not_found",
                    "job_id": job_id
                }

            job = self.active_jobs[job_id]
            job.status = "cancelled"
            self.completed_jobs[job_id] = job
            del self.active_jobs[job_id]

            return {
                "status": "cancelled",
                "job_id": job_id
            }

        except Exception as e:
            logger.error(f"Error cancelling job: {e}")
            return {
                "status": "error",
                "job_id": job_id,
                "error": str(e)
            }

    def get_queue_status(self) -> Dict[str, Any]:
        """Get status of the job queue.

        Returns:
            Queue status information
        """
        return {
            "active_jobs": len(self.active_jobs),
            "completed_jobs": len(self.completed_jobs),
            "queue_size": self.job_queue.qsize(),
            "max_concurrent_jobs": self.max_concurrent_jobs
        }

    def get_domain_status(self) -> Dict[str, Any]:
        """Get status of each domain.

        Returns:
            Domain status information
        """
        return {
            domain: {
                "enabled": sniffer.config.get("enabled", True),
                "locked": self.domain_locks[domain].locked()
            }
            for domain, sniffer in self.sniffers.items()
        }

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Cancel all active jobs
            for job_id in list(self.active_jobs.keys()):
                await self.cancel_job(job_id)

            # Clear queues and locks
            while not self.job_queue.empty():
                await self.job_queue.get()

            self.active_jobs.clear()
            self.completed_jobs.clear()
            self.domain_locks.clear()
            self.file_locks.clear()

            # Clean up sniffers
            for sniffer in self.sniffers.values():
                await sniffer.cleanup()

        except Exception as e:
            logger.error(f"Error cleaning up test orchestrator: {e}")
            raise
