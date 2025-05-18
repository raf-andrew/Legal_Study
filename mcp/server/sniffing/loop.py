"""
Core sniffing loop for continuous and file-specific testing.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ...utils.config import MCPConfig
from ...utils.logging import setup_logger
from ...utils.metrics import record_job_start, record_job_end
from ..domains import get_sniffer

logger = logging.getLogger("sniffing_loop")

class SniffingLoop:
    """Manages continuous and file-specific sniffing."""

    def __init__(self, config: MCPConfig):
        """Initialize sniffing loop.

        Args:
            config: MCP configuration
        """
        self.config = config
        self.file_queue = asyncio.Queue()
        self.domain_queues = {}
        self.results_cache = {}
        self.file_locks = {}
        self.active_jobs = set()
        self.is_running = False
        self._setup_queues()
        self._setup_logging()

    def _setup_queues(self) -> None:
        """Set up queues for each domain."""
        for domain in self.config.domains:
            self.domain_queues[domain] = asyncio.Queue()

    def _setup_logging(self) -> None:
        """Set up logging for sniffing loop."""
        setup_logger(logger, self.config.logging_config, "sniffing_loop")

    async def start(self) -> None:
        """Start sniffing workers."""
        try:
            logger.info("Starting sniffing loop")
            self.is_running = True

            # Start domain workers
            workers = []
            for domain in self.domain_queues:
                worker = asyncio.create_task(self._domain_worker(domain))
                workers.append(worker)

            # Start file worker
            file_worker = asyncio.create_task(self._file_worker())
            workers.append(file_worker)

            # Wait for workers
            await asyncio.gather(*workers)

        except Exception as e:
            logger.error(f"Error starting sniffing loop: {e}")
            self.is_running = False

    async def stop(self) -> None:
        """Stop sniffing workers."""
        try:
            logger.info("Stopping sniffing loop")
            self.is_running = False

            # Wait for queues to empty
            await self.file_queue.join()
            for queue in self.domain_queues.values():
                await queue.join()

            # Wait for jobs to complete
            while self.active_jobs:
                await asyncio.sleep(0.1)

            logger.info("Sniffing loop stopped")

        except Exception as e:
            logger.error(f"Error stopping sniffing loop: {e}")

    async def add_file(
        self,
        file: str,
        domains: Optional[List[str]] = None,
        priority: int = 1
    ) -> str:
        """Add file to sniffing queue.

        Args:
            file: File to sniff
            domains: Optional list of domains to sniff
            priority: Job priority (1-10)

        Returns:
            Job ID
        """
        try:
            # Create job ID
            job_id = f"sniff_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_jobs.add(job_id)

            # Add to queue
            await self.file_queue.put({
                "id": job_id,
                "file": file,
                "domains": domains or list(self.domain_queues.keys()),
                "priority": priority,
                "timestamp": datetime.now()
            })

            logger.info(f"Added file to queue: {file} (job: {job_id})")
            return job_id

        except Exception as e:
            logger.error(f"Error adding file to queue: {e}")
            raise

    async def _file_worker(self) -> None:
        """Process files from queue."""
        try:
            while self.is_running:
                # Get file from queue
                job = await self.file_queue.get()
                job_id = job["id"]
                file = job["file"]
                domains = job["domains"]

                try:
                    # Record job start
                    record_job_start("sniffing_loop", "file")

                    # Get or create file lock
                    if file not in self.file_locks:
                        self.file_locks[file] = asyncio.Lock()

                    async with self.file_locks[file]:
                        # Run sniffing
                        result = await self._sniff_file(job)

                        # Cache result
                        self.results_cache[file] = {
                            "result": result,
                            "timestamp": datetime.now()
                        }

                        # Add to domain queues
                        for domain in domains:
                            if domain in self.domain_queues:
                                await self.domain_queues[domain].put({
                                    "id": job_id,
                                    "file": file,
                                    "result": result.get(domain)
                                })

                    # Record job end
                    record_job_end(
                        "sniffing_loop",
                        "file",
                        datetime.now().timestamp() - job["timestamp"].timestamp(),
                        True
                    )

                except Exception as e:
                    logger.error(f"Error processing file {file}: {e}")
                    record_job_end(
                        "sniffing_loop",
                        "file",
                        datetime.now().timestamp() - job["timestamp"].timestamp(),
                        False
                    )

                finally:
                    # Mark task as done
                    self.file_queue.task_done()
                    self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error in file worker: {e}")

    async def _domain_worker(self, domain: str) -> None:
        """Process domain-specific tests.

        Args:
            domain: Domain to process
        """
        try:
            queue = self.domain_queues[domain]
            while self.is_running:
                # Get job from queue
                job = await queue.get()
                job_id = job["id"]
                file = job["file"]
                result = job["result"]

                try:
                    # Record job start
                    record_job_start("sniffing_loop", f"domain_{domain}")

                    # Run domain-specific sniffing
                    domain_result = await self._sniff_domain(domain, file, result)

                    # Generate report
                    await self._generate_report(domain, file, domain_result)

                    # Record job end
                    record_job_end(
                        "sniffing_loop",
                        f"domain_{domain}",
                        datetime.now().timestamp() - job["timestamp"].timestamp(),
                        True
                    )

                except Exception as e:
                    logger.error(f"Error processing domain {domain} for {file}: {e}")
                    record_job_end(
                        "sniffing_loop",
                        f"domain_{domain}",
                        datetime.now().timestamp() - job["timestamp"].timestamp(),
                        False
                    )

                finally:
                    # Mark task as done
                    queue.task_done()

        except Exception as e:
            logger.error(f"Error in domain worker {domain}: {e}")

    async def _sniff_file(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Run sniffing on a single file.

        Args:
            job: Job configuration

        Returns:
            Sniffing results
        """
        try:
            results = {}
            file = job["file"]
            domains = job["domains"]

            # Run sniffing for each domain
            for domain in domains:
                if domain not in self.domain_queues:
                    continue

                # Get domain sniffer
                sniffer = get_sniffer(domain, self.config)
                if not sniffer:
                    continue

                # Run sniffing
                result = await sniffer.sniff_file(file)
                results[domain] = result

            return results

        except Exception as e:
            logger.error(f"Error sniffing file: {e}")
            return {}

    async def _sniff_domain(
        self,
        domain: str,
        file: str,
        result: Any
    ) -> Dict[str, Any]:
        """Run domain-specific sniffing.

        Args:
            domain: Domain to sniff
            file: File to sniff
            result: Previous sniffing result

        Returns:
            Domain sniffing results
        """
        try:
            # Get domain sniffer
            sniffer = get_sniffer(domain, self.config)
            if not sniffer:
                return {}

            # Run domain-specific sniffing
            return await sniffer.analyze_result(file, result)

        except Exception as e:
            logger.error(f"Error in domain sniffing: {e}")
            return {}

    async def _generate_report(
        self,
        domain: str,
        file: str,
        result: Dict[str, Any]
    ) -> None:
        """Generate domain-specific report.

        Args:
            domain: Domain name
            file: File name
            result: Sniffing result
        """
        try:
            # Create report directory
            report_dir = Path(self.config.report_path) / domain / Path(file).stem
            report_dir.mkdir(parents=True, exist_ok=True)

            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "file": file,
                "domain": domain,
                "result": result
            }

            # Save report
            report_file = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import json
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

        except Exception as e:
            logger.error(f"Error generating report: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get sniffing metrics.

        Returns:
            Metrics dictionary
        """
        try:
            return {
                "active_jobs": len(self.active_jobs),
                "queued_files": self.file_queue.qsize(),
                "domain_queues": {
                    domain: queue.qsize()
                    for domain, queue in self.domain_queues.items()
                },
                "cached_results": len(self.results_cache),
                "file_locks": len(self.file_locks)
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
