"""Monitoring routes module."""

from fastapi import APIRouter
from app.services.monitoring_service import MonitoringService

router = APIRouter()

@router.get("/metrics")
async def get_metrics():
    """Get system metrics."""
    return MonitoringService.get_system_metrics()

@router.get("/errors")
async def get_errors():
    """Get error logs."""
    return MonitoringService.get_error_logs()

@router.get("/health")
async def get_health():
    """Get health metrics."""
    return MonitoringService.get_health_metrics() 