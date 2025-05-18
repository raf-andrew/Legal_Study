"""
MCP metrics utilities.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from prometheus_client import Counter, Gauge, Histogram, Summary

logger = logging.getLogger("mcp_metrics")

# Define metrics
JOB_COUNTER = Counter(
    "mcp_jobs_total",
    "Total number of jobs",
    ["component", "type"]
)

JOB_DURATION = Histogram(
    "mcp_job_duration_seconds",
    "Duration of jobs",
    ["component", "type"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

JOB_SUCCESS = Counter(
    "mcp_job_success_total",
    "Total number of successful jobs",
    ["component", "type"]
)

JOB_FAILURE = Counter(
    "mcp_job_failure_total",
    "Total number of failed jobs",
    ["component", "type"]
)

JOB_ACTIVE = Gauge(
    "mcp_jobs_active",
    "Number of active jobs",
    ["component", "type"]
)

JOB_QUEUED = Gauge(
    "mcp_jobs_queued",
    "Number of queued jobs",
    ["component", "type"]
)

MEMORY_USAGE = Gauge(
    "mcp_memory_bytes",
    "Memory usage",
    ["component"]
)

CPU_USAGE = Gauge(
    "mcp_cpu_percent",
    "CPU usage",
    ["component"]
)

def record_job_start(
    component: str,
    job_type: str
) -> None:
    """Record job start.

    Args:
        component: Component name
        job_type: Job type
    """
    try:
        JOB_COUNTER.labels(
            component=component,
            type=job_type
        ).inc()
        JOB_ACTIVE.labels(
            component=component,
            type=job_type
        ).inc()

    except Exception as e:
        logger.error(f"Error recording job start: {e}")

def record_job_end(
    component: str,
    job_type: str,
    duration: float,
    success: bool
) -> None:
    """Record job end.

    Args:
        component: Component name
        job_type: Job type
        duration: Duration in seconds
        success: Whether job was successful
    """
    try:
        JOB_DURATION.labels(
            component=component,
            type=job_type
        ).observe(duration)
        JOB_ACTIVE.labels(
            component=component,
            type=job_type
        ).dec()

        if success:
            JOB_SUCCESS.labels(
                component=component,
                type=job_type
            ).inc()
        else:
            JOB_FAILURE.labels(
                component=component,
                type=job_type
            ).inc()

    except Exception as e:
        logger.error(f"Error recording job end: {e}")

def record_job_queue(
    component: str,
    job_type: str,
    count: int
) -> None:
    """Record job queue.

    Args:
        component: Component name
        job_type: Job type
        count: Number of queued jobs
    """
    try:
        JOB_QUEUED.labels(
            component=component,
            type=job_type
        ).set(count)

    except Exception as e:
        logger.error(f"Error recording job queue: {e}")

def record_memory_usage(
    component: str,
    bytes: int
) -> None:
    """Record memory usage.

    Args:
        component: Component name
        bytes: Memory usage in bytes
    """
    try:
        MEMORY_USAGE.labels(component=component).set(bytes)

    except Exception as e:
        logger.error(f"Error recording memory usage: {e}")

def record_cpu_usage(
    component: str,
    percent: float
) -> None:
    """Record CPU usage.

    Args:
        component: Component name
        percent: CPU usage percentage
    """
    try:
        CPU_USAGE.labels(component=component).set(percent)

    except Exception as e:
        logger.error(f"Error recording CPU usage: {e}")

def get_metrics(component: str) -> Dict[str, Any]:
    """Get metrics for component.

    Args:
        component: Component name

    Returns:
        Metrics dictionary
    """
    try:
        return {
            "jobs": {
                "total": JOB_COUNTER.labels(
                    component=component,
                    type="total"
                )._value.get(),
                "success": JOB_SUCCESS.labels(
                    component=component,
                    type="total"
                )._value.get(),
                "failure": JOB_FAILURE.labels(
                    component=component,
                    type="total"
                )._value.get(),
                "active": JOB_ACTIVE.labels(
                    component=component,
                    type="total"
                )._value.get(),
                "queued": JOB_QUEUED.labels(
                    component=component,
                    type="total"
                )._value.get()
            },
            "duration": {
                "count": JOB_DURATION.labels(
                    component=component,
                    type="total"
                )._count.get(),
                "sum": JOB_DURATION.labels(
                    component=component,
                    type="total"
                )._sum.get()
            },
            "resources": {
                "memory": MEMORY_USAGE.labels(
                    component=component
                )._value.get(),
                "cpu": CPU_USAGE.labels(
                    component=component
                )._value.get()
            },
            "timestamp": datetime.now()
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {}

def reset_metrics(component: str) -> None:
    """Reset metrics for component.

    Args:
        component: Component name
    """
    try:
        JOB_COUNTER.labels(
            component=component,
            type="total"
        )._value.set(0)
        JOB_SUCCESS.labels(
            component=component,
            type="total"
        )._value.set(0)
        JOB_FAILURE.labels(
            component=component,
            type="total"
        )._value.set(0)
        JOB_ACTIVE.labels(
            component=component,
            type="total"
        )._value.set(0)
        JOB_QUEUED.labels(
            component=component,
            type="total"
        )._value.set(0)
        JOB_DURATION.labels(
            component=component,
            type="total"
        )._count.set(0)
        JOB_DURATION.labels(
            component=component,
            type="total"
        )._sum.set(0)
        MEMORY_USAGE.labels(component=component)._value.set(0)
        CPU_USAGE.labels(component=component)._value.set(0)

    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")

def export_metrics(component: str) -> Dict[str, Any]:
    """Export metrics for component.

    Args:
        component: Component name

    Returns:
        Metrics dictionary with metadata
    """
    try:
        return {
            "metrics": get_metrics(component),
            "metadata": {
                "component": component,
                "timestamp": datetime.now(),
                "version": "1.0.0"
            },
            "labels": {
                "mcp_jobs_total": "Total number of jobs",
                "mcp_job_duration_seconds": "Duration of jobs",
                "mcp_job_success_total": "Total number of successful jobs",
                "mcp_job_failure_total": "Total number of failed jobs",
                "mcp_jobs_active": "Number of active jobs",
                "mcp_jobs_queued": "Number of queued jobs",
                "mcp_memory_bytes": "Memory usage",
                "mcp_cpu_percent": "CPU usage"
            }
        }

    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        return {}
