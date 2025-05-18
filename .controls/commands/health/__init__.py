"""Health check command package."""

from .command import HealthCheckCommand
from .cli import cli
from typing import Dict, Any, Optional, List
from ..import BaseCommand

__version__ = "1.0.0"
__all__ = ["HealthCheckCommand", "cli"]

class HealthCheckCommand(BaseCommand):
    """Base class for health check commands."""
    
    def __init__(self, name: str, description: str, timeout: int = 30):
        """Initialize health check command.
        
        Args:
            name: Command name
            description: Command description
            timeout: Command timeout in seconds
        """
        super().__init__(name, description)
        self.timeout = timeout
    
    def validate(self, **kwargs) -> Optional[str]:
        """Validate health check arguments.
        
        Args:
            **kwargs: Command arguments
            
        Returns:
            Error message if validation fails, None otherwise
        """
        if "services" in kwargs and not isinstance(kwargs["services"], list):
            return "Services must be a list"
        return None
    
    def format_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format health check results.
        
        Args:
            results: Raw health check results
            
        Returns:
            Formatted results
        """
        return {
            "status": "healthy" if all(
                service.get("healthy", False) 
                for service in results.get("services", {}).values()
            ) else "unhealthy",
            "timestamp": results.get("timestamp"),
            "details": results
        }
    
    def get_service_status(self, service: Any) -> Dict[str, Any]:
        """Get service health status.
        
        Args:
            service: Service to check
            
        Returns:
            Service health status
        """
        try:
            return {
                "healthy": service.is_healthy(),
                "status": service.get_status(),
                "metrics": service.get_metrics()
            }
        except Exception as e:
            return {
                "healthy": False,
                "status": "error",
                "error": str(e)
            } 