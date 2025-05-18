"""
Core MCP server implementation providing centralized control and orchestration.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..api.models import SniffRequest, SniffResult
from .config import ServerConfig
from .scheduler import TestScheduler
from .orchestrator import TestOrchestrator
from ..orchestration.runners import get_runner
from ..orchestration.queues import get_queue
from ..orchestration.results import ResultManager

logger = logging.getLogger("mcp_server")

class MCPServer:
    """Master Control Program server for orchestrating sniffing operations."""

    def __init__(self, config_path: str):
        """Initialize MCP server.

        Args:
            config_path: Path to server configuration file
        """
        self.config = ServerConfig(config_path)
        self.scheduler = TestScheduler(self.config)
        self.orchestrator = TestOrchestrator(self.config)
        self.runners = self._init_runners()
        self.queues = self._init_queues()
        self.results = ResultManager(self.config)
        self.running = False
        self._setup_logging()

    async def start(self) -> None:
        """Start the MCP server."""
        try:
            logger.info("Starting MCP server...")
            self.running = True

            # Start components
            await self._start_api_server()
            await self._start_test_scheduler()
            await self._start_result_manager()
            await self._start_analyzers()

            logger.info("MCP server started successfully")

        except Exception as e:
            logger.error(f"Error starting MCP server: {e}")
            self.running = False
            raise

    async def shutdown(self) -> None:
        """Shutdown the MCP server."""
        try:
            logger.info("Shutting down MCP server...")
            self.running = False

            # Stop components
            await self._stop_api_server()
            await self._stop_test_scheduler()
            await self._stop_result_manager()
            await self._stop_analyzers()

            logger.info("MCP server shutdown complete")

        except Exception as e:
            logger.error(f"Error shutting down MCP server: {e}")
            raise

    async def sniff(self, request: SniffRequest) -> SniffResult:
        """Run sniffing based on request.

        Args:
            request: Sniffing request

        Returns:
            Sniffing result
        """
        try:
            # Validate request
            self._validate_request(request)

            # Create job
            job = await self._create_job(request)

            # Schedule job
            await self.scheduler.schedule(job)

            # Wait for results
            return await self.results.wait_for(job.id)

        except Exception as e:
            logger.error(f"Error running sniff: {e}")
            return SniffResult(
                status="failed",
                error=str(e),
                timestamp=datetime.now()
            )

    def _init_runners(self) -> Dict[str, Any]:
        """Initialize test runners.

        Returns:
            Dictionary of test runners
        """
        runners = {}
        for domain in self.config.domains:
            runners[domain] = get_runner(domain, self.config)
        return runners

    def _init_queues(self) -> Dict[str, Any]:
        """Initialize job queues.

        Returns:
            Dictionary of job queues
        """
        queues = {}
        for queue_type in ["priority", "domain", "file", "analysis"]:
            queues[queue_type] = get_queue(queue_type, self.config)
        return queues

    def _setup_logging(self) -> None:
        """Set up logging for MCP server."""
        try:
            # Get logging config
            log_config = self.config.logging
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

    def _validate_request(self, request: SniffRequest) -> None:
        """Validate sniffing request.

        Args:
            request: Request to validate

        Raises:
            ValueError: If request is invalid
        """
        if not request.files and not request.domains:
            raise ValueError("Request must specify files or domains")

        if request.domains:
            for domain in request.domains:
                if domain not in self.config.domains:
                    raise ValueError(f"Invalid domain: {domain}")

    async def _create_job(self, request: SniffRequest) -> Dict[str, Any]:
        """Create job from request.

        Args:
            request: Request to create job from

        Returns:
            Job dictionary
        """
        return {
            "id": f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "request": request.dict(),
            "status": "pending",
            "priority": request.priority,
            "timestamp": datetime.now()
        }

    async def _start_api_server(self) -> None:
        """Start API server."""
        try:
            # Import here to avoid circular imports
            from ..api.server import start_server
            await start_server(self)

        except Exception as e:
            logger.error(f"Error starting API server: {e}")
            raise

    async def _start_test_scheduler(self) -> None:
        """Start test scheduler."""
        try:
            await self.scheduler.start()

        except Exception as e:
            logger.error(f"Error starting test scheduler: {e}")
            raise

    async def _start_result_manager(self) -> None:
        """Start result manager."""
        try:
            await self.results.start()

        except Exception as e:
            logger.error(f"Error starting result manager: {e}")
            raise

    async def _start_analyzers(self) -> None:
        """Start analyzers."""
        try:
            for runner in self.runners.values():
                await runner.start_analyzer()

        except Exception as e:
            logger.error(f"Error starting analyzers: {e}")
            raise

    async def _stop_api_server(self) -> None:
        """Stop API server."""
        try:
            # Import here to avoid circular imports
            from ..api.server import stop_server
            await stop_server()

        except Exception as e:
            logger.error(f"Error stopping API server: {e}")
            raise

    async def _stop_test_scheduler(self) -> None:
        """Stop test scheduler."""
        try:
            await self.scheduler.stop()

        except Exception as e:
            logger.error(f"Error stopping test scheduler: {e}")
            raise

    async def _stop_result_manager(self) -> None:
        """Stop result manager."""
        try:
            await self.results.stop()

        except Exception as e:
            logger.error(f"Error stopping result manager: {e}")
            raise

    async def _stop_analyzers(self) -> None:
        """Stop analyzers."""
        try:
            for runner in self.runners.values():
                await runner.stop_analyzer()

        except Exception as e:
            logger.error(f"Error stopping analyzers: {e}")
            raise
