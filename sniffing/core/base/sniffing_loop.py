"""
Enhanced sniffing loop with file isolation and domain-specific processing.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
import yaml

from ..config.config_loader import load_config
from ..utils.metrics import MetricsCollector
from ..utils.logging import setup_logger
from ..utils.file_lock import FileLock

logger = logging.getLogger(__name__)

class SniffingLoop:
    """Main sniffing orchestrator with file isolation."""

    def __init__(self, config_path: str):
        """Initialize sniffing loop.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = load_config(config_path)

        # Set up logging
        setup_logger(
            logger,
            self.config["monitoring"]["logging"],
            "sniffing_loop"
        )

        # Initialize queues
        self.file_queue = asyncio.Queue(
            maxsize=self.config["core"]["max_queue_size"]
        )
        self.domain_queues = {
            domain: asyncio.Queue()
            for domain, settings in self.config["domains"].items()
            if settings["enabled"]
        }

        # Initialize state
        self.active_jobs: Set[str] = set()
        self.file_locks: Dict[str, FileLock] = {}
        self.results_cache: Dict[str, Dict] = {}
        self.metrics = MetricsCollector("sniffing_loop")
        self.is_running = False

    async def start(self) -> None:
        """Start sniffing workers."""
        try:
            logger.info("Starting sniffing loop")
            self.is_running = True

            # Start workers
            workers = []

            # File worker
            workers.append(
                asyncio.create_task(self._file_worker())
            )

            # Domain workers
            for domain in self.domain_queues:
                workers.append(
                    asyncio.create_task(
                        self._domain_worker(domain)
                    )
                )

            # Wait for workers
            await asyncio.gather(*workers)

        except Exception as e:
            logger.error(f"Error starting sniffing loop: {e}")
            self.is_running = False
            raise

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
            raise

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
                    # Record metrics
                    self.metrics.record_start("file_processing")

                    # Get or create file lock
                    if file not in self.file_locks:
                        self.file_locks[file] = FileLock(
                            file,
                            timeout=self.config["core"]["file_lock_timeout"]
                        )

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

                    # Record metrics
                    self.metrics.record_end(
                        "file_processing",
                        success=True
                    )

                except Exception as e:
                    logger.error(f"Error processing file {file}: {e}")
                    self.metrics.record_end(
                        "file_processing",
                        success=False
                    )

                finally:
                    # Mark task as done
                    self.file_queue.task_done()
                    self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error in file worker: {e}")
            raise

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
                    # Record metrics
                    self.metrics.record_start(f"domain_{domain}")

                    # Run domain-specific sniffing
                    domain_result = await self._sniff_domain(
                        domain,
                        file,
                        result
                    )

                    # Generate report
                    await self._generate_report(
                        domain,
                        file,
                        domain_result
                    )

                    # Record metrics
                    self.metrics.record_end(
                        f"domain_{domain}",
                        success=True
                    )

                except Exception as e:
                    logger.error(
                        f"Error processing domain {domain} for {file}: {e}"
                    )
                    self.metrics.record_end(
                        f"domain_{domain}",
                        success=False
                    )

                finally:
                    # Mark task as done
                    queue.task_done()

        except Exception as e:
            logger.error(f"Error in domain worker {domain}: {e}")
            raise

    async def _sniff_file(self, job: Dict) -> Dict:
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
                sniffer = self._get_sniffer(domain)
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
        result: Dict
    ) -> Dict:
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
            sniffer = self._get_sniffer(domain)
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
        result: Dict
    ) -> None:
        """Generate domain-specific report.

        Args:
            domain: Domain name
            file: File name
            result: Sniffing result
        """
        try:
            # Create report directory
            report_dir = Path(self.config["reporting"]["base_path"]) / domain / Path(file).stem
            report_dir.mkdir(parents=True, exist_ok=True)

            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "file": file,
                "domain": domain,
                "result": result
            }

            # Save report in all formats
            for fmt in self.config["reporting"]["formats"]:
                report_file = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}"

                if fmt == "json":
                    import json
                    with open(report_file, "w") as f:
                        json.dump(report, f, indent=2)
                elif fmt == "yaml":
                    with open(report_file, "w") as f:
                        yaml.safe_dump(report, f)
                # Add other format handlers as needed

        except Exception as e:
            logger.error(f"Error generating report: {e}")

    def _get_sniffer(self, domain: str):
        """Get domain sniffer instance.

        Args:
            domain: Domain name

        Returns:
            Sniffer instance or None
        """
        try:
            # Import domain sniffer
            module = __import__(
                f"domains.{domain}",
                fromlist=[f"{domain.capitalize()}Sniffer"]
            )
            sniffer_class = getattr(
                module,
                f"{domain.capitalize()}Sniffer"
            )

            # Create instance
            return sniffer_class(self.config)

        except Exception as e:
            logger.error(f"Error getting sniffer for domain {domain}: {e}")
            return None

    def get_metrics(self) -> Dict:
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
                "file_locks": len(self.file_locks),
                "metrics": self.metrics.get_metrics()
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}
