"""
Base sniffer class for domain-specific sniffing.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ...utils.config import MCPConfig
from ...utils.logging import setup_logger
from ...utils.metrics import record_job_start, record_job_end

logger = logging.getLogger("base_sniffer")

class BaseSniffer(ABC):
    """Base class for all sniffers."""

    def __init__(self, config: MCPConfig, domain: str):
        """Initialize base sniffer.

        Args:
            config: MCP configuration
            domain: Sniffer domain
        """
        self.config = config
        self.domain = domain
        self.results = {}
        self.active_jobs = set()
        self.is_running = False
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for sniffer."""
        setup_logger(logger, self.config.logging_config, f"{self.domain}_sniffer")

    @abstractmethod
    async def sniff_file(self, file: str) -> Dict[str, Any]:
        """Sniff a single file.

        Args:
            file: File to sniff

        Returns:
            Sniffing results
        """
        pass

    @abstractmethod
    async def analyze_result(
        self,
        file: str,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze sniffing result.

        Args:
            file: Sniffed file
            result: Sniffing result

        Returns:
            Analysis results
        """
        pass

    @abstractmethod
    async def fix_issues(
        self,
        file: str,
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fix detected issues.

        Args:
            file: File to fix
            issues: Issues to fix

        Returns:
            Fix results
        """
        pass

    async def start(self) -> None:
        """Start sniffer."""
        try:
            logger.info(f"Starting {self.domain} sniffer")
            self.is_running = True

        except Exception as e:
            logger.error(f"Error starting {self.domain} sniffer: {e}")
            self.is_running = False

    async def stop(self) -> None:
        """Stop sniffer."""
        try:
            logger.info(f"Stopping {self.domain} sniffer")
            self.is_running = False

            # Wait for jobs to complete
            while self.active_jobs:
                await asyncio.sleep(0.1)

            logger.info(f"{self.domain} sniffer stopped")

        except Exception as e:
            logger.error(f"Error stopping {self.domain} sniffer: {e}")

    async def run_sniffing(
        self,
        file: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run sniffing with options.

        Args:
            file: File to sniff
            options: Sniffing options

        Returns:
            Sniffing results
        """
        try:
            # Create job ID
            job_id = f"sniff_{self.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_jobs.add(job_id)

            try:
                # Record job start
                record_job_start(f"{self.domain}_sniffer", "sniff")

                # Run sniffing
                result = await self.sniff_file(file)

                # Store result
                self.results[job_id] = {
                    "file": file,
                    "options": options,
                    "result": result,
                    "timestamp": datetime.now()
                }

                # Record job end
                record_job_end(
                    f"{self.domain}_sniffer",
                    "sniff",
                    datetime.now().timestamp() - self.results[job_id]["timestamp"].timestamp(),
                    True
                )

                return result

            finally:
                self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error running {self.domain} sniffing: {e}")
            record_job_end(
                f"{self.domain}_sniffer",
                "sniff",
                0,
                False
            )
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def run_analysis(
        self,
        file: str,
        result: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run result analysis with options.

        Args:
            file: Sniffed file
            result: Sniffing result
            options: Analysis options

        Returns:
            Analysis results
        """
        try:
            # Create job ID
            job_id = f"analyze_{self.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_jobs.add(job_id)

            try:
                # Record job start
                record_job_start(f"{self.domain}_sniffer", "analyze")

                # Run analysis
                analysis = await self.analyze_result(file, result)

                # Store result
                self.results[job_id] = {
                    "file": file,
                    "options": options,
                    "analysis": analysis,
                    "timestamp": datetime.now()
                }

                # Record job end
                record_job_end(
                    f"{self.domain}_sniffer",
                    "analyze",
                    datetime.now().timestamp() - self.results[job_id]["timestamp"].timestamp(),
                    True
                )

                return analysis

            finally:
                self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error running {self.domain} analysis: {e}")
            record_job_end(
                f"{self.domain}_sniffer",
                "analyze",
                0,
                False
            )
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def run_fixes(
        self,
        file: str,
        issues: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run issue fixes with options.

        Args:
            file: File to fix
            issues: Issues to fix
            options: Fix options

        Returns:
            Fix results
        """
        try:
            # Create job ID
            job_id = f"fix_{self.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.active_jobs.add(job_id)

            try:
                # Record job start
                record_job_start(f"{self.domain}_sniffer", "fix")

                # Run fixes
                fixes = await self.fix_issues(file, issues)

                # Store result
                self.results[job_id] = {
                    "file": file,
                    "options": options,
                    "fixes": fixes,
                    "timestamp": datetime.now()
                }

                # Record job end
                record_job_end(
                    f"{self.domain}_sniffer",
                    "fix",
                    datetime.now().timestamp() - self.results[job_id]["timestamp"].timestamp(),
                    True
                )

                return fixes

            finally:
                self.active_jobs.remove(job_id)

        except Exception as e:
            logger.error(f"Error running {self.domain} fixes: {e}")
            record_job_end(
                f"{self.domain}_sniffer",
                "fix",
                0,
                False
            )
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get sniffer metrics.

        Returns:
            Metrics dictionary
        """
        try:
            metrics = {
                "active_jobs": len(self.active_jobs),
                "stored_results": len(self.results),
                "domain": self.domain,
                "status": "running" if self.is_running else "stopped"
            }

            # Calculate success rate
            total = len(self.results)
            if total > 0:
                success = sum(
                    1 for r in self.results.values()
                    if r.get("result", {}).get("status") == "success"
                )
                metrics["success_rate"] = success / total

            return metrics

        except Exception as e:
            logger.error(f"Error getting {self.domain} metrics: {e}")
            return {}
