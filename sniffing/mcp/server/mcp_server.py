"""
Enhanced MCP (Master Control Program) server for orchestrating sniffing operations.
"""
import asyncio
import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import FastAPI, HTTPException, BackgroundTasks
from prometheus_client import start_http_server, Counter, Gauge, Histogram
from pydantic import BaseModel

from ...core.utils.result import SniffingResult
from ..orchestration.test_orchestrator import TestOrchestrator
from ...domains.security.security_sniffer import SecuritySniffer
from ...domains.browser.browser_sniffer import BrowserSniffer
from ...domains.functional.functional_sniffer import FunctionalSniffer
from ...domains.unit.unit_sniffer import UnitSniffer
from ...domains.documentation.documentation_sniffer import DocumentationSniffer

logger = logging.getLogger("mcp_server")

# Prometheus metrics
SNIFFING_REQUESTS = Counter("sniffing_requests_total", "Total sniffing requests")
SNIFFING_ERRORS = Counter("sniffing_errors_total", "Total sniffing errors")
ACTIVE_SNIFFING_JOBS = Gauge("active_sniffing_jobs", "Number of active sniffing jobs")
SNIFFING_DURATION = Histogram("sniffing_duration_seconds", "Sniffing operation duration")

class SniffingRequest(BaseModel):
    """Sniffing request model."""
    files: List[str]
    domains: Optional[List[str]] = None
    priority: Optional[int] = 1
    fix: Optional[bool] = True

class MCPServer:
    """Enhanced Master Control Program server."""

    def __init__(self, config_path: str):
        """Initialize MCP server.

        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.app = FastAPI(title="MCP Server", version="1.0.0")
        self.orchestrator = TestOrchestrator(self.config)
        self.sniffers = self._initialize_sniffers()
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self._setup_routes()
        self._setup_monitoring()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file.

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise

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

    def _setup_routes(self) -> None:
        """Set up API routes."""
        # Sniffing endpoints
        self.app.post("/api/v1/sniff")(self.sniff)
        self.app.post("/api/v1/sniff/file")(self.sniff_file)
        self.app.get("/api/v1/sniff/status/{job_id}")(self.get_sniffing_status)
        self.app.post("/api/v1/sniff/cancel/{job_id}")(self.cancel_sniffing)

        # Domain-specific endpoints
        self.app.post("/api/v1/sniff/{domain}")(self.sniff_domain)
        self.app.get("/api/v1/domains")(self.get_domains)
        self.app.get("/api/v1/domain/{domain}/config")(self.get_domain_config)

        # Health and monitoring endpoints
        self.app.get("/health")(self.health_check)
        self.app.get("/metrics")(self.get_metrics)

        # Git integration endpoints
        self.app.post("/api/v1/git/pre-commit")(self.git_pre_commit)
        self.app.post("/api/v1/git/pre-push")(self.git_pre_push)

    def _setup_monitoring(self) -> None:
        """Set up monitoring and metrics."""
        try:
            # Start Prometheus metrics server
            prometheus_port = self.config["mcp"]["monitoring"]["prometheus_port"]
            start_http_server(prometheus_port)
            logger.info(f"Prometheus metrics server started on port {prometheus_port}")

        except Exception as e:
            logger.error(f"Error setting up monitoring: {e}")
            raise

    async def sniff(self, request: SniffingRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        """Handle sniffing request.

        Args:
            request: Sniffing request
            background_tasks: FastAPI background tasks

        Returns:
            Response dictionary
        """
        try:
            SNIFFING_REQUESTS.inc()

            # Validate request
            if not request.files:
                raise HTTPException(status_code=400, message="No files specified")

            # Create job ID
            job_id = f"sniff_{len(self.active_jobs)}"

            # Start sniffing task
            task = asyncio.create_task(self._run_sniffing(
                job_id,
                request.files,
                request.domains,
                request.priority,
                request.fix
            ))
            self.active_jobs[job_id] = task

            # Add cleanup task
            background_tasks.add_task(self._cleanup_job, job_id)

            return {
                "job_id": job_id,
                "status": "started",
                "files": len(request.files),
                "domains": request.domains
            }

        except Exception as e:
            SNIFFING_ERRORS.inc()
            logger.error(f"Error handling sniffing request: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def sniff_file(self, file: str, domains: Optional[List[str]] = None) -> Dict[str, Any]:
        """Sniff a single file.

        Args:
            file: File to sniff
            domains: Optional list of domains to sniff

        Returns:
            Sniffing results
        """
        try:
            results = {}
            domains = domains or list(self.sniffers.keys())

            for domain in domains:
                if domain not in self.sniffers:
                    continue

                sniffer = self.sniffers[domain]
                if not sniffer.config.get("enabled", True):
                    continue

                result = await sniffer.sniff_file(file)
                results[domain] = result.to_dict()

            return {
                "file": file,
                "results": results
            }

        except Exception as e:
            logger.error(f"Error sniffing file {file}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_sniffing_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of sniffing job.

        Args:
            job_id: Job ID

        Returns:
            Job status
        """
        try:
            if job_id not in self.active_jobs:
                raise HTTPException(status_code=404, detail="Job not found")

            task = self.active_jobs[job_id]
            return {
                "job_id": job_id,
                "status": "running" if not task.done() else "completed",
                "result": task.result() if task.done() else None
            }

        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def cancel_sniffing(self, job_id: str) -> Dict[str, Any]:
        """Cancel sniffing job.

        Args:
            job_id: Job ID

        Returns:
            Cancellation status
        """
        try:
            if job_id not in self.active_jobs:
                raise HTTPException(status_code=404, detail="Job not found")

            task = self.active_jobs[job_id]
            if not task.done():
                task.cancel()

            return {
                "job_id": job_id,
                "status": "cancelled"
            }

        except Exception as e:
            logger.error(f"Error cancelling job: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def sniff_domain(self, domain: str, request: SniffingRequest) -> Dict[str, Any]:
        """Sniff files in specific domain.

        Args:
            domain: Domain to sniff
            request: Sniffing request

        Returns:
            Domain sniffing results
        """
        try:
            if domain not in self.sniffers:
                raise HTTPException(status_code=404, detail="Domain not found")

            sniffer = self.sniffers[domain]
            if not sniffer.config.get("enabled", True):
                raise HTTPException(status_code=400, detail="Domain disabled")

            results = []
            for file in request.files:
                result = await sniffer.sniff_file(file)
                results.append(result.to_dict())

            return {
                "domain": domain,
                "files": len(request.files),
                "results": results
            }

        except Exception as e:
            logger.error(f"Error sniffing domain {domain}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_domains(self) -> Dict[str, Any]:
        """Get available domains and their status.

        Returns:
            Domain information
        """
        return {
            domain: {
                "enabled": sniffer.config.get("enabled", True),
                "priority": sniffer.config.get("priority", 1)
            }
            for domain, sniffer in self.sniffers.items()
        }

    async def get_domain_config(self, domain: str) -> Dict[str, Any]:
        """Get domain configuration.

        Args:
            domain: Domain name

        Returns:
            Domain configuration
        """
        try:
            if domain not in self.sniffers:
                raise HTTPException(status_code=404, detail="Domain not found")

            return self.sniffers[domain].config

        except Exception as e:
            logger.error(f"Error getting domain config: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check.

        Returns:
            Health status
        """
        try:
            status = {
                "status": "healthy",
                "active_jobs": len(self.active_jobs),
                "domains": {
                    domain: "healthy" if sniffer.health.is_healthy() else "unhealthy"
                    for domain, sniffer in self.sniffers.items()
                }
            }

            if any(s == "unhealthy" for s in status["domains"].values()):
                status["status"] = "degraded"

            return status

        except Exception as e:
            logger.error(f"Error performing health check: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics.

        Returns:
            System metrics
        """
        try:
            return {
                "sniffing_requests": SNIFFING_REQUESTS._value.get(),
                "sniffing_errors": SNIFFING_ERRORS._value.get(),
                "active_jobs": ACTIVE_SNIFFING_JOBS._value.get(),
                "domain_metrics": {
                    domain: sniffer.get_metrics()
                    for domain, sniffer in self.sniffers.items()
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def git_pre_commit(self, files: List[str]) -> Dict[str, Any]:
        """Handle git pre-commit hook.

        Args:
            files: Changed files

        Returns:
            Pre-commit check results
        """
        try:
            results = {}
            for file in files:
                result = await self.sniff_file(file)
                results[file] = result

            # Check if any critical issues
            has_critical = any(
                any(r.has_critical_issues() for r in domain_results.values())
                for domain_results in results.values()
            )

            return {
                "status": "failed" if has_critical else "passed",
                "results": results
            }

        except Exception as e:
            logger.error(f"Error in pre-commit hook: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def git_pre_push(self, branch: str, files: List[str]) -> Dict[str, Any]:
        """Handle git pre-push hook.

        Args:
            branch: Target branch
            files: Changed files

        Returns:
            Pre-push check results
        """
        try:
            # Get branch protection rules
            protection = self.config["git"]["branch_protection"]
            if not protection.get("enabled", True):
                return {"status": "skipped"}

            # Run required checks
            results = {}
            for check in protection.get("required_checks", []):
                if check not in self.sniffers:
                    continue

                sniffer = self.sniffers[check]
                if not sniffer.config.get("enabled", True):
                    continue

                domain_results = []
                for file in files:
                    result = await sniffer.sniff_file(file)
                    domain_results.append(result)

                results[check] = domain_results

            # Check if all required checks pass
            has_critical = any(
                any(r.has_critical_issues() for r in domain_results)
                for domain_results in results.values()
            )

            return {
                "status": "failed" if has_critical else "passed",
                "branch": branch,
                "results": results
            }

        except Exception as e:
            logger.error(f"Error in pre-push hook: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _run_sniffing(
        self,
        job_id: str,
        files: List[str],
        domains: Optional[List[str]] = None,
        priority: int = 1,
        fix: bool = True
    ) -> Dict[str, Any]:
        """Run sniffing operation.

        Args:
            job_id: Job ID
            files: Files to sniff
            domains: Optional list of domains to sniff
            priority: Job priority
            fix: Whether to fix issues

        Returns:
            Sniffing results
        """
        try:
            ACTIVE_SNIFFING_JOBS.inc()
            start_time = asyncio.get_event_loop().time()

            # Run sniffing through orchestrator
            results = await self.orchestrator.run_tests(
                files,
                domains,
                priority,
                fix
            )

            duration = asyncio.get_event_loop().time() - start_time
            SNIFFING_DURATION.observe(duration)

            return {
                "job_id": job_id,
                "status": "completed",
                "duration": duration,
                "results": results
            }

        except Exception as e:
            logger.error(f"Error running sniffing job {job_id}: {e}")
            return {
                "job_id": job_id,
                "status": "failed",
                "error": str(e)
            }

        finally:
            ACTIVE_SNIFFING_JOBS.dec()

    async def _cleanup_job(self, job_id: str) -> None:
        """Clean up completed job.

        Args:
            job_id: Job ID to clean up
        """
        try:
            task = self.active_jobs[job_id]
            await task
            del self.active_jobs[job_id]

        except Exception as e:
            logger.error(f"Error cleaning up job {job_id}: {e}")

    def start(self) -> None:
        """Start the MCP server."""
        try:
            import uvicorn
            host = self.config["mcp"]["host"]
            port = self.config["mcp"]["port"]
            uvicorn.run(self.app, host=host, port=port)

        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the MCP server."""
        try:
            # Cancel all active jobs
            for job_id, task in self.active_jobs.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Clean up resources
            self.active_jobs.clear()
            for sniffer in self.sniffers.values():
                await sniffer.cleanup()

        except Exception as e:
            logger.error(f"Error shutting down server: {e}")
            raise
