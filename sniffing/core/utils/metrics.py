"""
Metrics utilities for sniffers.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import threading
from collections import defaultdict

from prometheus_client import Counter, Gauge, Histogram, Summary

logger = logging.getLogger("metrics_utils")

# Define metrics
SNIFF_COUNTER = Counter(
    "sniff_total",
    "Total number of sniffing operations",
    ["domain"]
)

SNIFF_DURATION = Histogram(
    "sniff_duration_seconds",
    "Duration of sniffing operations",
    ["domain"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

SNIFF_COVERAGE = Gauge(
    "sniff_coverage_percent",
    "Coverage percentage of sniffing operations",
    ["domain"]
)

SNIFF_ISSUES = Counter(
    "sniff_issues_total",
    "Total number of issues found",
    ["domain", "severity"]
)

SNIFF_FIXES = Counter(
    "sniff_fixes_total",
    "Total number of fixes generated",
    ["domain"]
)

SNIFF_SUCCESS = Counter(
    "sniff_success_total",
    "Total number of successful sniffing operations",
    ["domain"]
)

SNIFF_FAILURE = Counter(
    "sniff_failure_total",
    "Total number of failed sniffing operations",
    ["domain"]
)

SNIFF_FILES = Histogram(
    "sniff_files_total",
    "Number of files processed",
    ["domain"],
    buckets=[1, 5, 10, 50, 100, 500, 1000]
)

SNIFF_ACTIVE = Gauge(
    "sniff_active_jobs",
    "Number of active sniffing jobs",
    ["domain"]
)

SNIFF_QUEUED = Gauge(
    "sniff_queued_jobs",
    "Number of queued sniffing jobs",
    ["domain"]
)

SNIFF_MEMORY = Gauge(
    "sniff_memory_bytes",
    "Memory usage of sniffing operations",
    ["domain"]
)

SNIFF_CPU = Gauge(
    "sniff_cpu_percent",
    "CPU usage of sniffing operations",
    ["domain"]
)

class MetricsCollector:
    """Collects and manages metrics for monitoring."""

    def __init__(self, name: str):
        """Initialize metrics collector.

        Args:
            name: Collector name
        """
        self.name = name
        self._metrics = defaultdict(lambda: defaultdict(int))
        self._timings = {}
        self._lock = threading.Lock()

    def record_start(self, operation: str) -> None:
        """Record operation start time.

        Args:
            operation: Operation name
        """
        try:
            with self._lock:
                self._timings[operation] = datetime.now()
                self._metrics[operation]["starts"] += 1

        except Exception as e:
            logger.error(f"Error recording start for {operation}: {e}")

    def record_end(
        self,
        operation: str,
        success: bool = True,
        metadata: Optional[Dict] = None
    ) -> None:
        """Record operation end time and status.

        Args:
            operation: Operation name
            success: Whether operation succeeded
            metadata: Optional metadata
        """
        try:
            with self._lock:
                # Get timing
                start_time = self._timings.pop(operation, None)
                if start_time:
                    duration = (datetime.now() - start_time).total_seconds()
                    self._metrics[operation]["duration_total"] += duration
                    self._metrics[operation]["count"] += 1

                # Record status
                if success:
                    self._metrics[operation]["successes"] += 1
                else:
                    self._metrics[operation]["failures"] += 1

                # Record metadata
                if metadata:
                    for key, value in metadata.items():
                        if isinstance(value, (int, float)):
                            self._metrics[operation][f"meta_{key}"] += value

        except Exception as e:
            logger.error(f"Error recording end for {operation}: {e}")

    def increment(
        self,
        metric: str,
        value: int = 1,
        metadata: Optional[Dict] = None
    ) -> None:
        """Increment metric counter.

        Args:
            metric: Metric name
            value: Value to increment by
            metadata: Optional metadata
        """
        try:
            with self._lock:
                self._metrics[metric]["value"] += value

                # Record metadata
                if metadata:
                    for key, val in metadata.items():
                        if isinstance(val, (int, float)):
                            self._metrics[metric][f"meta_{key}"] += val

        except Exception as e:
            logger.error(f"Error incrementing metric {metric}: {e}")

    def set_gauge(
        self,
        metric: str,
        value: float,
        metadata: Optional[Dict] = None
    ) -> None:
        """Set gauge metric value.

        Args:
            metric: Metric name
            value: Gauge value
            metadata: Optional metadata
        """
        try:
            with self._lock:
                self._metrics[metric]["value"] = value

                # Record metadata
                if metadata:
                    for key, val in metadata.items():
                        if isinstance(val, (int, float)):
                            self._metrics[metric][f"meta_{key}"] = val

        except Exception as e:
            logger.error(f"Error setting gauge {metric}: {e}")

    def get_metrics(self) -> Dict:
        """Get current metrics.

        Returns:
            Metrics dictionary
        """
        try:
            with self._lock:
                metrics = {}

                # Process metrics
                for operation, data in self._metrics.items():
                    metrics[operation] = dict(data)

                    # Calculate averages
                    if "duration_total" in data and "count" in data:
                        count = data["count"]
                        if count > 0:
                            metrics[operation]["duration_avg"] = \
                                data["duration_total"] / count

                    # Calculate success rate
                    if "successes" in data and "failures" in data:
                        total = data["successes"] + data["failures"]
                        if total > 0:
                            metrics[operation]["success_rate"] = \
                                data["successes"] / total

                return metrics

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {}

    def reset(self) -> None:
        """Reset all metrics."""
        try:
            with self._lock:
                self._metrics.clear()
                self._timings.clear()

        except Exception as e:
            logger.error(f"Error resetting metrics: {e}")

class OperationMetrics:
    """Context manager for operation metrics."""

    def __init__(
        self,
        collector: MetricsCollector,
        operation: str,
        metadata: Optional[Dict] = None
    ):
        """Initialize operation metrics.

        Args:
            collector: Metrics collector
            operation: Operation name
            metadata: Optional metadata
        """
        self.collector = collector
        self.operation = operation
        self.metadata = metadata
        self.success = True

    def __enter__(self):
        """Enter context and record start."""
        self.collector.record_start(self.operation)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and record end."""
        if exc_type is not None:
            self.success = False
        self.collector.record_end(
            self.operation,
            self.success,
            self.metadata
        )

def track_operation(
    collector: MetricsCollector,
    operation: str,
    metadata: Optional[Dict] = None
):
    """Decorator for tracking operation metrics.

    Args:
        collector: Metrics collector
        operation: Operation name
        metadata: Optional metadata
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with OperationMetrics(collector, operation, metadata):
                return await func(*args, **kwargs)
        return wrapper
    return decorator

def record_sniff_start(domain: str) -> None:
    """Record start of sniffing operation.

    Args:
        domain: Domain name
    """
    try:
        SNIFF_COUNTER.labels(domain=domain).inc()
        SNIFF_ACTIVE.labels(domain=domain).inc()

    except Exception as e:
        logger.error(f"Error recording sniff start: {e}")

def record_sniff_end(
    domain: str,
    duration: float,
    success: bool
) -> None:
    """Record end of sniffing operation.

    Args:
        domain: Domain name
        duration: Duration in seconds
        success: Whether operation was successful
    """
    try:
        SNIFF_DURATION.labels(domain=domain).observe(duration)
        SNIFF_ACTIVE.labels(domain=domain).dec()

        if success:
            SNIFF_SUCCESS.labels(domain=domain).inc()
        else:
            SNIFF_FAILURE.labels(domain=domain).inc()

    except Exception as e:
        logger.error(f"Error recording sniff end: {e}")

def record_coverage(domain: str, coverage: float) -> None:
    """Record coverage percentage.

    Args:
        domain: Domain name
        coverage: Coverage percentage
    """
    try:
        SNIFF_COVERAGE.labels(domain=domain).set(coverage)

    except Exception as e:
        logger.error(f"Error recording coverage: {e}")

def record_issues(
    domain: str,
    issues: List[Dict[str, Any]]
) -> None:
    """Record issues found.

    Args:
        domain: Domain name
        issues: List of issues
    """
    try:
        for issue in issues:
            severity = issue.get("severity", "unknown")
            SNIFF_ISSUES.labels(
                domain=domain,
                severity=severity
            ).inc()

    except Exception as e:
        logger.error(f"Error recording issues: {e}")

def record_fixes(
    domain: str,
    fixes: List[Dict[str, Any]]
) -> None:
    """Record fixes generated.

    Args:
        domain: Domain name
        fixes: List of fixes
    """
    try:
        SNIFF_FIXES.labels(domain=domain).inc(len(fixes))

    except Exception as e:
        logger.error(f"Error recording fixes: {e}")

def record_files(domain: str, count: int) -> None:
    """Record number of files processed.

    Args:
        domain: Domain name
        count: Number of files
    """
    try:
        SNIFF_FILES.labels(domain=domain).observe(count)

    except Exception as e:
        logger.error(f"Error recording files: {e}")

def record_queue(domain: str, count: int) -> None:
    """Record number of queued jobs.

    Args:
        domain: Domain name
        count: Number of jobs
    """
    try:
        SNIFF_QUEUED.labels(domain=domain).set(count)

    except Exception as e:
        logger.error(f"Error recording queue: {e}")

def record_memory(domain: str, bytes: int) -> None:
    """Record memory usage.

    Args:
        domain: Domain name
        bytes: Memory usage in bytes
    """
    try:
        SNIFF_MEMORY.labels(domain=domain).set(bytes)

    except Exception as e:
        logger.error(f"Error recording memory: {e}")

def record_cpu(domain: str, percent: float) -> None:
    """Record CPU usage.

    Args:
        domain: Domain name
        percent: CPU usage percentage
    """
    try:
        SNIFF_CPU.labels(domain=domain).set(percent)

    except Exception as e:
        logger.error(f"Error recording CPU: {e}")

def get_metrics(domain: str) -> Dict[str, Any]:
    """Get current metrics for domain.

    Args:
        domain: Domain name

    Returns:
        Metrics dictionary
    """
    try:
        return {
            "total": SNIFF_COUNTER.labels(domain=domain)._value.get(),
            "duration": {
                "count": SNIFF_DURATION.labels(domain=domain)._count.get(),
                "sum": SNIFF_DURATION.labels(domain=domain)._sum.get()
            },
            "coverage": SNIFF_COVERAGE.labels(domain=domain)._value.get(),
            "issues": {
                severity: SNIFF_ISSUES.labels(
                    domain=domain,
                    severity=severity
                )._value.get()
                for severity in ["critical", "high", "medium", "low"]
            },
            "fixes": SNIFF_FIXES.labels(domain=domain)._value.get(),
            "success": SNIFF_SUCCESS.labels(domain=domain)._value.get(),
            "failure": SNIFF_FAILURE.labels(domain=domain)._value.get(),
            "files": {
                "count": SNIFF_FILES.labels(domain=domain)._count.get(),
                "sum": SNIFF_FILES.labels(domain=domain)._sum.get()
            },
            "active": SNIFF_ACTIVE.labels(domain=domain)._value.get(),
            "queued": SNIFF_QUEUED.labels(domain=domain)._value.get(),
            "memory": SNIFF_MEMORY.labels(domain=domain)._value.get(),
            "cpu": SNIFF_CPU.labels(domain=domain)._value.get()
        }

    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return {}

def reset_metrics(domain: str) -> None:
    """Reset metrics for domain.

    Args:
        domain: Domain name
    """
    try:
        SNIFF_COUNTER.labels(domain=domain)._value.set(0)
        SNIFF_DURATION.labels(domain=domain)._count.set(0)
        SNIFF_DURATION.labels(domain=domain)._sum.set(0)
        SNIFF_COVERAGE.labels(domain=domain)._value.set(0)
        for severity in ["critical", "high", "medium", "low"]:
            SNIFF_ISSUES.labels(
                domain=domain,
                severity=severity
            )._value.set(0)
        SNIFF_FIXES.labels(domain=domain)._value.set(0)
        SNIFF_SUCCESS.labels(domain=domain)._value.set(0)
        SNIFF_FAILURE.labels(domain=domain)._value.set(0)
        SNIFF_FILES.labels(domain=domain)._count.set(0)
        SNIFF_FILES.labels(domain=domain)._sum.set(0)
        SNIFF_ACTIVE.labels(domain=domain)._value.set(0)
        SNIFF_QUEUED.labels(domain=domain)._value.set(0)
        SNIFF_MEMORY.labels(domain=domain)._value.set(0)
        SNIFF_CPU.labels(domain=domain)._value.set(0)

    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")

def export_metrics(domain: str) -> Dict[str, Any]:
    """Export metrics for domain.

    Args:
        domain: Domain name

    Returns:
        Metrics dictionary with metadata
    """
    try:
        return {
            "metrics": get_metrics(domain),
            "metadata": {
                "domain": domain,
                "timestamp": datetime.now(),
                "version": "1.0.0"
            },
            "labels": {
                "sniff_total": "Total number of sniffing operations",
                "sniff_duration_seconds": "Duration of sniffing operations",
                "sniff_coverage_percent": "Coverage percentage of sniffing operations",
                "sniff_issues_total": "Total number of issues found",
                "sniff_fixes_total": "Total number of fixes generated",
                "sniff_success_total": "Total number of successful sniffing operations",
                "sniff_failure_total": "Total number of failed sniffing operations",
                "sniff_files_total": "Number of files processed",
                "sniff_active_jobs": "Number of active sniffing jobs",
                "sniff_queued_jobs": "Number of queued sniffing jobs",
                "sniff_memory_bytes": "Memory usage of sniffing operations",
                "sniff_cpu_percent": "CPU usage of sniffing operations"
            }
        }

    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        return {}
