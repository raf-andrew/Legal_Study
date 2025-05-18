"""Mock registry service for testing."""

from typing import Dict, List, Any, Optional
from .registry import MockServiceRegistry

class MockRegistryService:
    """Mock implementation of registry service for testing."""
    
    def __init__(self):
        """Initialize mock registry service."""
        self.registry = MockServiceRegistry()
        self.is_running = False
        self.error_mode = False
        self.error_message = None
    
    def start(self) -> Dict[str, str]:
        """Start the registry service."""
        if self.error_mode:
            return {
                "status": "error",
                "error": self.error_message or "Failed to start registry service"
            }
        self.is_running = True
        return {"status": "success"}
    
    def stop(self) -> Dict[str, str]:
        """Stop the registry service."""
        if self.error_mode:
            return {
                "status": "error",
                "error": self.error_message or "Failed to stop registry service"
            }
        self.is_running = False
        return {"status": "success"}
    
    def reset(self) -> Dict[str, str]:
        """Reset the registry service."""
        if self.error_mode:
            return {
                "status": "error",
                "error": self.error_message or "Failed to reset registry service"
            }
        self.registry = MockServiceRegistry()
        self.is_running = False
        return {"status": "success"}
    
    def apply_config(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Apply configuration to registry service."""
        if not self.is_running:
            return {
                "status": "error",
                "error": "Registry service is not running"
            }
        if self.error_mode:
            return {
                "status": "error",
                "error": self.error_message or "Failed to apply configuration"
            }
        return self.registry.apply_config(config)
    
    def initialize(self) -> Dict[str, str]:
        """Initialize registry service."""
        if not self.is_running:
            return {
                "status": "error",
                "error": "Registry service is not running"
            }
        if self.error_mode:
            return {
                "status": "error",
                "error": self.error_message or "Failed to initialize registry"
            }
        return self.registry.initialize()
    
    def discover_services(self) -> List[str]:
        """Discover available services."""
        if not self.is_running:
            return []
        if self.error_mode:
            return []
        return self.registry.discover_services()
    
    def register_service(self, service_name: str, service_info: Dict[str, Any]) -> Dict[str, Any]:
        """Register a service with the registry."""
        if not self.is_running:
            return {
                "status": "error",
                "error": "Registry service is not running"
            }
        if self.error_mode:
            return {
                "status": "error",
                "error": self.error_message or "Failed to register service"
            }
        return self.registry.register_service(service_name, service_info)
    
    def unregister_service(self, service_name: str) -> Dict[str, Any]:
        """Unregister a service from the registry."""
        if not self.is_running:
            return {
                "status": "error",
                "error": "Registry service is not running"
            }
        if self.error_mode:
            return {
                "status": "error",
                "error": self.error_message or "Failed to unregister service"
            }
        return self.registry.unregister_service(service_name)
    
    def configure_health_check(self, service_name: str, check_info: Dict[str, Any]) -> Dict[str, Any]:
        """Configure health check for a service."""
        if not self.is_running:
            return {
                "status": "error",
                "error": "Registry service is not running"
            }
        if self.error_mode:
            return {
                "status": "error",
                "error": self.error_message or "Failed to configure health check"
            }
        return self.registry.configure_health_check(service_name, check_info)
    
    def resolve_dependencies(self, service_name: str, dependencies: List[str]) -> Dict[str, Any]:
        """Resolve service dependencies."""
        if not self.is_running:
            return {
                "status": "error",
                "error": "Registry service is not running"
            }
        if self.error_mode:
            return {
                "status": "error",
                "error": self.error_message or "Failed to resolve dependencies"
            }
        return self.registry.resolve_dependencies(service_name, dependencies)
    
    def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get service information."""
        if not self.is_running:
            return None
        if self.error_mode:
            return None
        return self.registry.get_service(service_name)
    
    def list_services(self) -> List[str]:
        """List all registered services."""
        if not self.is_running:
            return []
        if self.error_mode:
            return []
        return self.registry.list_services()
    
    def get_health_check(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get health check information for a service."""
        if not self.is_running:
            return None
        if self.error_mode:
            return None
        return self.registry.get_health_check(service_name)
    
    def get_dependencies(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get dependencies for a service."""
        if not self.is_running:
            return None
        if self.error_mode:
            return None
        return self.registry.get_dependencies(service_name)
    
    def set_error_mode(self, enabled: bool, message: Optional[str] = None):
        """Set error mode for testing error scenarios."""
        self.error_mode = enabled
        self.error_message = message 