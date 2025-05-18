"""Service health check implementation."""

from typing import Any, Dict, List
from .base import BaseCheck
from ...mocks.registry import MockServiceRegistry

class ServiceCheck(BaseCheck):
    """Service health check implementation."""
    
    def __init__(self, registry: MockServiceRegistry):
        """Initialize service check.
        
        Args:
            registry: Service registry instance
        """
        super().__init__("services")
        self.registry = registry
    
    def _execute(self) -> Dict[str, Any]:
        """Execute service health check.
        
        Returns:
            Service health check results
        """
        results = {
            "healthy": True,
            "services": {}
        }
        
        for service_name in self.registry.list_services():
            service = self.registry.get_service(service_name)
            if not service:
                continue
            
            try:
                metrics = service.get_metrics()
                errors = service.get_errors()
                
                service_status = {
                    "status": "healthy",
                    "started_at": metrics.get("started_at"),
                    "total_calls": metrics.get("total_calls", 0),
                    "total_errors": metrics.get("total_errors", 0)
                }
                
                if errors:
                    service_status["status"] = "unhealthy"
                    service_status["errors"] = errors
                    results["healthy"] = False
                
                results["services"][service_name] = service_status
                
            except Exception as e:
                results["services"][service_name] = {
                    "status": "error",
                    "error": str(e)
                }
                results["healthy"] = False
        
        return results
    
    def get_unhealthy_services(self) -> List[str]:
        """Get list of unhealthy services.
        
        Returns:
            List of unhealthy service names
        """
        result = self._execute()
        return [
            name for name, status in result["services"].items()
            if status["status"] != "healthy"
        ]
    
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
    
    def get_service_errors(self, service_name: str) -> List[Dict[str, Any]]:
        """Get errors for specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            List of service errors
        """
        service = self.registry.get_service(service_name)
        if not service:
            return [{
                "error": f"Service {service_name} not found"
            }]
        
        try:
            return service.get_errors()
        except Exception as e:
            return [{
                "error": str(e)
            }] 