"""
Sniffing loop mechanism for continuous and file-specific testing.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ...core.base_sniffer import BaseSniffer, SnifferType, SniffingResult
from ..ai.ai_analyzer import AIAnalyzer

logger = logging.getLogger("sniffing_loop")

class SniffingLoop:
    """Handles continuous sniffing and file-specific testing."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active_sniffers: Dict[str, BaseSniffer] = {}
        self.file_queue: asyncio.Queue = asyncio.Queue()
        self.domain_queues: Dict[str, asyncio.Queue] = {}
        self.file_locks: Dict[str, asyncio.Lock] = {}
        self.results_cache: Dict[str, Dict[str, Any]] = {}
        self.ai_analyzer = AIAnalyzer(config.get("ai", {}))
        self.is_running = False
        self.report_path = Path(config.get("report_path", "reports"))
        self._setup_queues()

    def _setup_queues(self) -> None:
        """Set up queues for each domain."""
        domains = [
            "security",
            "browser",
            "functional",
            "unit",
            "documentation",
            "api",
            "performance"
        ]
        for domain in domains:
            self.domain_queues[domain] = asyncio.Queue()

    async def start(self) -> None:
        """Start the sniffing loop."""
        try:
            self.is_running = True
            logger.info("Starting sniffing loop")

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
            logger.error(f"Error in sniffing loop: {e}")
            self.is_running = False

    async def stop(self) -> None:
        """Stop the sniffing loop."""
        self.is_running = False
        logger.info("Stopping sniffing loop")

    async def add_file(self, file: str, domains: Optional[List[str]] = None) -> None:
        """Add a file to the sniffing queue."""
        try:
            await self.file_queue.put({
                "file": file,
                "domains": domains,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"Added file to queue: {file}")

        except Exception as e:
            logger.error(f"Error adding file to queue: {e}")

    async def _file_worker(self) -> None:
        """Process files from the queue."""
        try:
            while self.is_running:
                # Get file from queue
                file_data = await self.file_queue.get()
                file = file_data["file"]
                domains = file_data["domains"]

                # Get or create file lock
                if file not in self.file_locks:
                    self.file_locks[file] = asyncio.Lock()

                async with self.file_locks[file]:
                    # Run sniffing on file
                    result = await self._sniff_file(file, domains)

                    # Cache result
                    self.results_cache[file] = {
                        "result": result,
                        "timestamp": datetime.now().isoformat()
                    }

                    # Generate report
                    await self._generate_report(file, result)

                # Mark task as done
                self.file_queue.task_done()

        except Exception as e:
            logger.error(f"Error in file worker: {e}")

    async def _domain_worker(self, domain: str) -> None:
        """Process files for a specific domain."""
        try:
            queue = self.domain_queues[domain]
            while self.is_running:
                # Get file from queue
                file = await queue.get()

                # Run domain-specific sniffing
                result = await self._sniff_domain(domain, file)

                # Generate domain report
                await self._generate_domain_report(domain, file, result)

                # Mark task as done
                queue.task_done()

        except Exception as e:
            logger.error(f"Error in domain worker: {e}")

    async def _sniff_file(self, file: str, domains: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run sniffing on a single file."""
        try:
            results = []
            issues = []
            metrics = {}

            # Get domains to test
            if not domains:
                domains = list(self.domain_queues.keys())

            # Run sniffing for each domain
            for domain in domains:
                sniffer = self.active_sniffers.get(domain)
                if sniffer:
                    result = await sniffer.sniff_file(file)
                    results.append(result)
                    issues.extend(result.issues)
                    self._update_metrics(metrics, result.metrics)

            # Analyze results
            analysis = await self.ai_analyzer.analyze_results(results)

            return {
                "status": "success",
                "file": file,
                "domains": domains,
                "results": results,
                "issues": issues,
                "metrics": metrics,
                "analysis": analysis
            }

        except Exception as e:
            logger.error(f"Error sniffing file: {e}")
            return {
                "status": "error",
                "file": file,
                "error": str(e)
            }

    async def _sniff_domain(self, domain: str, file: str) -> Dict[str, Any]:
        """Run domain-specific sniffing on a file."""
        try:
            sniffer = self.active_sniffers.get(domain)
            if not sniffer:
                return {
                    "status": "error",
                    "error": f"No sniffer found for domain: {domain}"
                }

            # Run sniffing
            result = await sniffer.sniff_file(file)

            return {
                "status": "success",
                "domain": domain,
                "file": file,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error in domain sniffing: {e}")
            return {
                "status": "error",
                "domain": domain,
                "file": file,
                "error": str(e)
            }

    async def _generate_report(self, file: str, result: Dict[str, Any]) -> None:
        """Generate report for file sniffing results."""
        try:
            # Create report directory
            report_dir = self.report_path / Path(file).stem
            report_dir.mkdir(parents=True, exist_ok=True)

            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "file": file,
                "result": result
            }

            # Save report
            report_file = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import json
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

        except Exception as e:
            logger.error(f"Error generating report: {e}")

    async def _generate_domain_report(self, domain: str, file: str, result: Dict[str, Any]) -> None:
        """Generate domain-specific report."""
        try:
            # Create report directory
            report_dir = self.report_path / domain
            report_dir.mkdir(parents=True, exist_ok=True)

            # Generate report
            report = {
                "timestamp": datetime.now().isoformat(),
                "domain": domain,
                "file": file,
                "result": result
            }

            # Save report
            report_file = report_dir / f"report_{Path(file).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import json
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

        except Exception as e:
            logger.error(f"Error generating domain report: {e}")

    def _update_metrics(self, metrics: Dict[str, Any], new_metrics: Dict[str, Any]) -> None:
        """Update metrics dictionary with new values."""
        for key, value in new_metrics.items():
            if isinstance(value, (int, float)):
                metrics[key] = metrics.get(key, 0) + value
            else:
                metrics[key] = value
