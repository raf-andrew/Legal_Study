"""Mock service registry for testing."""

from typing import Dict, List, Optional, Any
from datetime import datetime

class MockServiceRegistry:
    """Mock implementation of service registry for testing."""
    
    def __init__(self):
        """Initialize mock service registry."""
        self.services = {}
        self.health_checks = {}
        self.dependencies = {}
        self.config = {
            "max_services": 100,
            "discovery_interval": 300,
            "health_check_interval": 60,
            "dependency_timeout": 30
        }
    
    def apply_config(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Apply configuration to registry."""
        self.config.update(config)
        return {"status": "success"}
    
    def apply_default_config(self) -> Dict[str, str]:
        """Apply default configuration."""
        self.config = {
            "max_services": 100,
            "discovery_interval": 300,
            "health_check_interval": 60,
            "dependency_timeout": 30
        }
        return {"status": "success"}
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config
    
    def reset_config(self) -> Dict[str, str]:
        """Reset configuration to defaults."""
        self.config = {
            "max_services": 100,
            "discovery_interval": 300,
            "health_check_interval": 60,
            "dependency_timeout": 30
        }
        return {"status": "success"}
    
    def initialize(self) -> Dict[str, str]:
        """Initialize registry service."""
        self.services = {}
        self.health_checks = {}
        self.dependencies = {}
        return {"status": "success"}
    
    def discover_services(self) -> List[str]:
        """Discover available services."""
        return list(self.services.keys())
    
    def register_service(self, service_name: str, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """Register a service with the registry."""
        if len(self.services) >= self.config["max_services"]:
            return {
                "status": "error",
                "error": "Maximum number of services reached"
            }
        
        self.services[service_name] = {
            **service_info,
            "registered_at": datetime.now().isoformat()
        }
        return {
            "status": "success",
            "registered": True,
            "service": service_name
        }
    
    def unregister_service(self, service_name: str) -> Dict[str, Any]:
        """Unregister a service from the registry."""
        if service_name not in self.services:
            return {
                "status": "error",
                "error": f"Service {service_name} not found"
            }
        
        del self.services[service_name]
        return {
            "status": "success",
            "unregistered": True,
            "service": service_name
        }
    
    def configure_health_check(self, service_name: str, check_info: Dict[str, Any]) -> Dict[str, Any]:
        """Configure health check for a service."""
        if service_name not in self.services:
            return {
                "status": "error",
                "error": f"Service {service_name} not found"
            }
        
        self.health_checks[service_name] = {
            **check_info,
            "last_check": None,
            "status": "unknown"
        }
        return {
            "status": "success",
            "configured": True,
            "service": service_name
        }
    
    def resolve_dependencies(self, service_name: str, dependencies: List[str]) -> Dict[str, Any]:
        """Resolve service dependencies."""
        if service_name not in self.services:
            return {
                "status": "error",
                "error": f"Service {service_name} not found"
            }
        
        missing = [dep for dep in dependencies if dep not in self.services]
        if missing:
            return {
                "status": "error",
                "error": f"Dependencies not found: {', '.join(missing)}"
            }
        
        self.dependencies[service_name] = {
            "dependencies": dependencies,
            "resolved_at": datetime.now().isoformat()
        }
        return {
            "status": "success",
            "resolved": True,
            "service": service_name,
            "dependencies": dependencies
        }
    
    def stop(self) -> Dict[str, str]:
        """Stop the registry service."""
        self.services = {}
        self.health_checks = {}
        self.dependencies = {}
        return {"status": "success"}
    
    def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get service information."""
        return self.services.get(service_name)
    
    def list_services(self) -> List[str]:
        """List all registered services."""
        return list(self.services.keys())
    
    def get_health_check(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get health check information for a service."""
        return self.health_checks.get(service_name)
    
    def get_dependencies(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get dependencies for a service."""
        return self.dependencies.get(service_name) 