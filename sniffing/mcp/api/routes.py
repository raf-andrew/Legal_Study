"""
API routes for MCP server.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from .models import (
    AnalyzeRequest,
    AnalyzeResult,
    FixRequest,
    FixResult,
    HealthResponse,
    MetricsResponse,
    SniffRequest,
    SniffResult,
    StatusResponse
)

logger = logging.getLogger("api_routes")

router = APIRouter()
mcp_server = None

@router.post("/sniff", response_model=SniffResult)
async def sniff(request: SniffRequest) -> SniffResult:
    """Run sniffing based on request.

    Args:
        request: Sniffing request

    Returns:
        Sniffing result
    """
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")

        result = await mcp_server.sniff(request.dict())
        return SniffResult(**result)

    except Exception as e:
        logger.error(f"Error handling sniff request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fix", response_model=FixResult)
async def fix(request: FixRequest) -> FixResult:
    """Fix issues based on request.

    Args:
        request: Fix request

    Returns:
        Fix result
    """
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")

        result = await mcp_server.fix(request.dict())
        return FixResult(**result)

    except Exception as e:
        logger.error(f"Error handling fix request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=AnalyzeResult)
async def analyze(request: AnalyzeRequest) -> AnalyzeResult:
    """Analyze results based on request.

    Args:
        request: Analysis request

    Returns:
        Analysis result
    """
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")

        result = await mcp_server.analyze(request.dict())
        return AnalyzeResult(**result)

    except Exception as e:
        logger.error(f"Error handling analyze request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Get MCP server status.

    Returns:
        Server status
    """
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")

        # Get scheduler status
        scheduler_status = mcp_server.scheduler.get_queue_status()
        active_jobs = len(mcp_server.scheduler.active_jobs)
        queued_jobs = sum(q["size"] for q in scheduler_status.values())

        # Get runner status
        runner_status = mcp_server.orchestrator.get_all_runner_status()

        # Get metrics
        metrics = {
            "scheduler": scheduler_status,
            "runners": {
                domain: status.get("metrics", {})
                for domain, status in runner_status.items()
            }
        }

        return StatusResponse(
            status="running" if mcp_server.running else "stopped",
            timestamp=datetime.now(),
            active_jobs=active_jobs,
            queued_jobs=queued_jobs,
            runners=runner_status,
            metrics=metrics
        )

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Get MCP server health.

    Returns:
        Server health
    """
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")

        # Get component health
        scheduler_health = await mcp_server.scheduler.get_health()
        orchestrator_health = await mcp_server.orchestrator.get_health()
        runner_health = {
            domain: await runner.get_health()
            for domain, runner in mcp_server.orchestrator.runners.items()
        }

        # Calculate overall health
        components_healthy = all([
            scheduler_health["status"] == "healthy",
            orchestrator_health["status"] == "healthy",
            all(h["status"] == "healthy" for h in runner_health.values())
        ])

        # Get metrics
        metrics = {
            "scheduler": scheduler_health.get("metrics", {}),
            "orchestrator": orchestrator_health.get("metrics", {}),
            "runners": {
                domain: health.get("metrics", {})
                for domain, health in runner_health.items()
            }
        }

        return HealthResponse(
            status="healthy" if components_healthy else "unhealthy",
            timestamp=datetime.now(),
            checks={
                "scheduler": scheduler_health,
                "orchestrator": orchestrator_health,
                "runners": runner_health
            },
            metrics=metrics
        )

    except Exception as e:
        logger.error(f"Error getting health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """Get MCP server metrics.

    Returns:
        Server metrics
    """
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")

        # Get component metrics
        scheduler_metrics = mcp_server.scheduler.get_metrics()
        orchestrator_metrics = mcp_server.orchestrator.get_metrics()
        runner_metrics = {
            domain: runner.get_metrics()
            for domain, runner in mcp_server.orchestrator.runners.items()
        }

        # Collect all metrics
        metrics = {
            "scheduler": scheduler_metrics,
            "orchestrator": orchestrator_metrics,
            "runners": runner_metrics
        }

        # Get metric labels
        labels = {
            "scheduler": scheduler_metrics.get("labels", {}),
            "orchestrator": orchestrator_metrics.get("labels", {}),
            "runners": {
                domain: m.get("labels", {})
                for domain, m in runner_metrics.items()
            }
        }

        # Get metric help
        help_text = {
            "scheduler": scheduler_metrics.get("help", {}),
            "orchestrator": orchestrator_metrics.get("help", {}),
            "runners": {
                domain: m.get("help", {})
                for domain, m in runner_metrics.items()
            }
        }

        return MetricsResponse(
            timestamp=datetime.now(),
            metrics=metrics,
            labels=labels,
            help=help_text
        )

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{domain}/sniff", response_model=SniffResult)
async def sniff_domain(domain: str, request: SniffRequest) -> SniffResult:
    """Run domain-specific sniffing.

    Args:
        domain: Domain to sniff
        request: Sniffing request

    Returns:
        Sniffing result
    """
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")

        # Override domains in request
        request_dict = request.dict()
        request_dict["domains"] = [domain]

        result = await mcp_server.sniff(request_dict)
        return SniffResult(**result)

    except Exception as e:
        logger.error(f"Error handling domain sniff request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{domain}/status", response_model=StatusResponse)
async def get_domain_status(domain: str) -> StatusResponse:
    """Get domain-specific status.

    Args:
        domain: Domain to get status for

    Returns:
        Domain status
    """
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")

        # Get runner status
        runner_status = mcp_server.orchestrator.get_runner_status(domain)
        if not runner_status:
            raise HTTPException(status_code=404, detail=f"Domain not found: {domain}")

        # Get metrics
        metrics = runner_status.get("metrics", {})

        return StatusResponse(
            status=runner_status["status"],
            timestamp=datetime.now(),
            active_jobs=runner_status.get("active_jobs", 0),
            queued_jobs=runner_status.get("queued_jobs", 0),
            runners={domain: runner_status},
            metrics=metrics
        )

    except Exception as e:
        logger.error(f"Error getting domain status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{domain}/health", response_model=HealthResponse)
async def get_domain_health(domain: str) -> HealthResponse:
    """Get domain-specific health.

    Args:
        domain: Domain to get health for

    Returns:
        Domain health
    """
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")

        # Get runner health
        runner = mcp_server.orchestrator.runners.get(domain)
        if not runner:
            raise HTTPException(status_code=404, detail=f"Domain not found: {domain}")

        runner_health = await runner.get_health()

        return HealthResponse(
            status=runner_health["status"],
            timestamp=datetime.now(),
            checks={"runner": runner_health},
            metrics=runner_health.get("metrics", {})
        )

    except Exception as e:
        logger.error(f"Error getting domain health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{domain}/metrics", response_model=MetricsResponse)
async def get_domain_metrics(domain: str) -> MetricsResponse:
    """Get domain-specific metrics.

    Args:
        domain: Domain to get metrics for

    Returns:
        Domain metrics
    """
    try:
        if not mcp_server:
            raise HTTPException(status_code=503, detail="MCP server not available")

        # Get runner metrics
        runner = mcp_server.orchestrator.runners.get(domain)
        if not runner:
            raise HTTPException(status_code=404, detail=f"Domain not found: {domain}")

        metrics = runner.get_metrics()

        return MetricsResponse(
            timestamp=datetime.now(),
            metrics=metrics,
            labels=metrics.get("labels", {}),
            help=metrics.get("help", {})
        )

    except Exception as e:
        logger.error(f"Error getting domain metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
