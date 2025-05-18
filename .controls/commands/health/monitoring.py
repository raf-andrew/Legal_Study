"""Monitoring service for health check command."""

import os
import time
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from prometheus_client import Counter, Gauge, Histogram, start_http_server

class MonitoringService:
    """Monitoring service for health check command."""
    
    def __init__(self):
        """Initialize monitoring service."""
        self.metrics_port = int(os.getenv("METRICS_PORT", "9090"))
        self.metrics_enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        
        # Initialize metrics
        self.check_counter = Counter(
            "health_check_total",
            "Total number of health checks",
            ["check_type"]
        )
        
        self.check_duration = Histogram(
            "health_check_duration_seconds",
            "Health check duration in seconds",
            ["check_type"]
        )
        
        self.check_errors = Counter(
            "health_check_errors_total",
            "Total number of health check errors",
            ["check_type", "error_type"]
        )
        
        self.service_health = Gauge(
            "service_health",
            "Service health status (1 = healthy, 0 = unhealthy)",
            ["service"]
        )
        
        self.service_errors = Counter(
            "service_errors_total",
            "Total number of service errors",
            ["service", "error_type"]
        )
        
        # Start metrics server if enabled
        if self.metrics_enabled:
            start_http_server(self.metrics_port)
    
    def record_check(self, check_type: str, duration: float,
                    error: Optional[str] = None) -> None:
        """Record health check execution.
        
        Args:
            check_type: Type of health check
            duration: Check duration in seconds
            error: Optional error message
        """
        self.check_counter.labels(check_type=check_type).inc()
        self.check_duration.labels(check_type=check_type).observe(duration)
        
        if error:
            self.check_errors.labels(
                check_type=check_type,
                error_type=type(error).__name__
            ).inc()
    
    def record_service_health(self, service: str, healthy: bool) -> None:
        """Record service health status.
        
        Args:
            service: Name of the service
            healthy: Whether the service is healthy
        """
        self.service_health.labels(service=service).set(1 if healthy else 0)
    
    def record_service_error(self, service: str, error: str) -> None:
        """Record service error.
        
        Args:
            service: Name of the service
            error: Error message
        """
        self.service_errors.labels(
            service=service,
            error_type=type(error).__name__
        ).inc()
    
    def get_check_metrics(self, check_type: Optional[str] = None) -> Dict[str, Any]:
        """Get health check metrics.
        
        Args:
            check_type: Optional check type to filter
            
        Returns:
            Health check metrics
        """
        metrics = {}
        
        # Get counter values
        counter_values = self.check_counter._metrics
        for labels, value in counter_values.items():
            if not check_type or labels[0] == check_type:
                metrics[f"total_checks_{labels[0]}"] = value
        
        # Get duration values
        duration_values = self.check_duration._metrics
        for labels, value in duration_values.items():
            if not check_type or labels[0] == check_type:
                metrics[f"duration_{labels[0]}"] = value
        
        # Get error values
        error_values = self.check_errors._metrics
        for labels, value in error_values.items():
            if not check_type or labels[0] == check_type:
                metrics[f"errors_{labels[0]}_{labels[1]}"] = value
        
        return metrics
    
    def get_service_metrics(self, service: Optional[str] = None) -> Dict[str, Any]:
        """Get service metrics.
        
        Args:
            service: Optional service name to filter
            
        Returns:
            Service metrics
        """
        metrics = {}
        
        # Get health values
        health_values = self.service_health._metrics
        for labels, value in health_values.items():
            if not service or labels[0] == service:
                metrics[f"health_{labels[0]}"] = value
        
        # Get error values
        error_values = self.service_errors._metrics
        for labels, value in error_values.items():
            if not service or labels[0] == service:
                metrics[f"errors_{labels[0]}_{labels[1]}"] = value
        
        return metrics
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics.
        
        Returns:
            All metrics
        """
        return {
            "checks": self.get_check_metrics(),
            "services": self.get_service_metrics()
        }
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        # Reset counters
        for counter in [self.check_counter, self.check_errors, self.service_errors]:
            counter._metrics.clear()
        
        # Reset histogram
        self.check_duration._metrics.clear()
        
        # Reset gauge
        self.service_health._metrics.clear()
    
    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format.
        
        Args:
            format: Output format (json or prometheus)
            
        Returns:
            Formatted metrics string
        """
        if format == "json":
            return json.dumps(self.get_all_metrics(), indent=2)
        elif format == "prometheus":
            from prometheus_client.exposition import generate_latest
            return generate_latest().decode()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def start(self) -> None:
        """Start monitoring service."""
        if not self.metrics_enabled:
            self.metrics_enabled = True
            start_http_server(self.metrics_port)
    
    def stop(self) -> None:
        """Stop monitoring service."""
        self.metrics_enabled = False
        # Note: Prometheus client doesn't provide a way to stop the server
        # In a real implementation, we would need to track and stop the server 