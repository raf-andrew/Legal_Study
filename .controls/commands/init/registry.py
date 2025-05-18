"""Service registry setup command implementation."""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from .. import BaseCommand
from ...mocks.registry import MockServiceRegistry

class ServiceRegistryCommand(BaseCommand):
    """Service registry setup command."""
    
    def __init__(self, registry: MockServiceRegistry):
        """Initialize service registry setup command.
        
        Args:
            registry: Service registry
        """
        super().__init__(
            name="init-registry",
            description="Initialize service registry and configuration"
        )
        self.registry = registry
    
    def validate(self, **kwargs) -> Optional[str]:
        """Validate initialization arguments.
        
        Args:
            **kwargs: Command arguments
            
        Returns:
            Error message if validation fails, None otherwise
        """
        if "config" in kwargs and not isinstance(kwargs["config"], str):
            return "Config file must be a string"
        
        return None
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute service registry setup.
        
        Args:
            **kwargs: Command arguments
                config: Config file path
            
        Returns:
            Setup results
        """
        registry_service = self.registry.get_service("registry")
        if not registry_service:
            return {
                "status": "error",
                "error": "Service registry service not available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "setup": self._setup_registry(registry_service, kwargs.get("config")),
            "services": self._register_services(registry_service),
            "health_checks": self._configure_health_checks(registry_service),
            "dependencies": self._resolve_dependencies(registry_service)
        }
        
        # Determine overall status
        success = all(
            result["status"] == "success"
            for result in results.values()
            if isinstance(result, dict) and "status" in result
        )
        
        results["status"] = "success" if success else "error"
        return results
    
    def _setup_registry(self, registry_service: Any, config_file: Optional[str]) -> Dict[str, Any]:
        """Set up service registry.
        
        Args:
            registry_service: Service registry service
            config_file: Config file path
            
        Returns:
            Setup results
        """
        try:
            # Load and apply configuration
            if config_file:
                config = self._load_file(config_file)
                registry_service.apply_config(config)
            else:
                registry_service.apply_default_config()
            
            # Initialize registry service
            registry_service.initialize()
            
            # Get current configuration
            current_config = registry_service.get_config()
            
            return {
                "status": "success",
                "config": current_config
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _register_services(self, registry_service: Any) -> Dict[str, Any]:
        """Register available services.
        
        Args:
            registry_service: Service registry service
            
        Returns:
            Registration results
        """
        try:
            # Get available services
            services = registry_service.discover_services()
            
            results = []
            for service in services:
                try:
                    result = registry_service.register_service(service)
                    results.append({
                        "service": service,
                        "status": "success",
                        "details": result
                    })
                except Exception as e:
                    results.append({
                        "service": service,
                        "status": "error",
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "services": results
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _configure_health_checks(self, registry_service: Any) -> Dict[str, Any]:
        """Configure service health checks.
        
        Args:
            registry_service: Service registry service
            
        Returns:
            Health check configuration results
        """
        try:
            # Get registered services
            services = registry_service.list_services()
            
            results = []
            for service in services:
                try:
                    result = registry_service.configure_health_check(service)
                    results.append({
                        "service": service,
                        "status": "success",
                        "details": result
                    })
                except Exception as e:
                    results.append({
                        "service": service,
                        "status": "error",
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "health_checks": results
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _resolve_dependencies(self, registry_service: Any) -> Dict[str, Any]:
        """Resolve service dependencies.
        
        Args:
            registry_service: Service registry service
            
        Returns:
            Dependency resolution results
        """
        try:
            # Get registered services
            services = registry_service.list_services()
            
            results = []
            for service in services:
                try:
                    result = registry_service.resolve_dependencies(service)
                    results.append({
                        "service": service,
                        "status": "success",
                        "details": result
                    })
                except Exception as e:
                    results.append({
                        "service": service,
                        "status": "error",
                        "error": str(e)
                    })
            
            return {
                "status": "success",
                "dependencies": results
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _load_file(self, file_path: str) -> str:
        """Load file contents.
        
        Args:
            file_path: Path to file
            
        Returns:
            File contents
            
        Raises:
            FileNotFoundError: If file does not exist
            IOError: If file cannot be read
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, "r") as f:
                return f.read()
        except IOError as e:
            raise IOError(f"Failed to read file {file_path}: {str(e)}")
    
    def reset(self, registry_service: Any) -> Dict[str, Any]:
        """Reset service registry.
        
        Args:
            registry_service: Service registry service
            
        Returns:
            Reset results
        """
        try:
            # Unregister all services
            services = registry_service.list_services()
            unregister_results = []
            
            for service in services:
                try:
                    result = registry_service.unregister_service(service)
                    unregister_results.append({
                        "service": service,
                        "status": "success",
                        "details": result
                    })
                except Exception as e:
                    unregister_results.append({
                        "service": service,
                        "status": "error",
                        "error": str(e)
                    })
            
            # Reset configuration
            registry_service.reset_config()
            
            # Stop service
            registry_service.stop()
            
            return {
                "status": "success",
                "unregistered": unregister_results
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            } 