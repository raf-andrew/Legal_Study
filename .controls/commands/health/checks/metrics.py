"""Metrics health check implementation."""

from typing import Any, Dict, List
from .base import BaseCheck
from ...mocks.registry import MockServiceRegistry

class MetricsCheck(BaseCheck):
    """Metrics health check implementation."""
    
    def __init__(self, registry: MockServiceRegistry):
        """Initialize metrics check.
        
        Args:
            registry: Service registry instance
        """
        super().__init__("metrics")
        self.registry = registry
    
    def _execute(self) -> Dict[str, Any]:
        """Execute metrics health check.
        
        Returns:
            Metrics health check results
        """
        metrics_service = self.registry.get_service("metrics")
        if not metrics_service:
            return {
                "healthy": False,
                "error": "Metrics service not available"
            }
        
        try:
            # Collect metrics from all services
            service_metrics = {}
            for service_name in self.registry.list_services():
                service = self.registry.get_service(service_name)
                if not service:
                    continue
                
                try:
                    metrics = service.get_metrics()
                    service_metrics[service_name] = {
                        "status": "collected",
                        "metrics": metrics
                    }
                except Exception as e:
                    service_metrics[service_name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Collect system metrics
            system_metrics = metrics_service.collect_system_metrics()
            
            # Analyze metrics health
            unhealthy_services = [
                name for name, data in service_metrics.items()
                if data["status"] == "error" or
                (data["status"] == "collected" and
                 data["metrics"].get("total_errors", 0) > 0)
            ]
            
            return {
                "healthy": len(unhealthy_services) == 0,
                "services": service_metrics,
                "system": system_metrics,
                "unhealthy_services": unhealthy_services
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def get_service_metrics(self, service_name: str) -> Dict[str, Any]:
        """Get metrics for specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service metrics
        """
        service = self.registry.get_service(service_name)
        if not service:
            return {
                "error": f"Service {service_name} not found"
            }
        
        try:
            return service.get_metrics()
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics.
        
        Returns:
            System metrics
        """
        metrics_service = self.registry.get_service("metrics")
        if not metrics_service:
            return {
                "error": "Metrics service not available"
            }
        
        try:
            return metrics_service.collect_system_metrics()
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def get_metrics_by_type(self, metric_type: str) -> Dict[str, Any]:
        """Get metrics by type.
        
        Args:
            metric_type: Type of metrics to collect
            
        Returns:
            Metrics of specified type
        """
        metrics_service = self.registry.get_service("metrics")
        if not metrics_service:
            return {
                "error": "Metrics service not available"
            }
        
        try:
            return metrics_service.collect_metrics_by_type(metric_type)
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary.
        
        Returns:
            Summary of all metrics
        """
        result = self._execute()
        if "error" in result:
            return result
        
        total_services = len(result["services"])
        healthy_services = sum(
            1 for data in result["services"].values()
            if data["status"] == "collected" and
            data["metrics"].get("total_errors", 0) == 0
        )
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": len(result["unhealthy_services"]),
            "system_metrics": result["system"],
            "health_percentage": (healthy_services / total_services * 100)
            if total_services > 0 else 0
        } 