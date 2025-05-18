"""Cache initialization command implementation."""

import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from .. import BaseCommand
from ...mocks.registry import MockServiceRegistry

class CacheInitCommand(BaseCommand):
    """Cache initialization command."""
    
    def __init__(self, registry: MockServiceRegistry):
        """Initialize cache initialization command.
        
        Args:
            registry: Service registry
        """
        super().__init__(
            name="init-cache",
            description="Initialize cache service and configuration"
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
        
        if "warm_up" in kwargs and not isinstance(kwargs["warm_up"], bool):
            return "Warm-up flag must be a boolean"
        
        if "clear" in kwargs and not isinstance(kwargs["clear"], bool):
            return "Clear flag must be a boolean"
        
        return None
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute cache initialization.
        
        Args:
            **kwargs: Command arguments
                config: Config file path
                warm_up: Whether to warm up cache
                clear: Whether to clear existing cache
            
        Returns:
            Initialization results
        """
        cache_service = self.registry.get_service("cache")
        if not cache_service:
            return {
                "status": "error",
                "error": "Cache service not available",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "setup": self._setup_cache(cache_service, kwargs.get("config")),
            "clear": self._clear_cache(cache_service) if kwargs.get("clear") else None,
            "warm_up": self._warm_up_cache(cache_service) if kwargs.get("warm_up") else None
        }
        
        # Determine overall status
        success = all(
            result["status"] == "success"
            for result in results.values()
            if isinstance(result, dict) and "status" in result
        )
        
        results["status"] = "success" if success else "error"
        return results
    
    def _setup_cache(self, cache_service: Any, config_file: Optional[str]) -> Dict[str, Any]:
        """Set up cache service.
        
        Args:
            cache_service: Cache service
            config_file: Config file path
            
        Returns:
            Setup results
        """
        try:
            # Load and apply configuration
            if config_file:
                config = self._load_file(config_file)
                cache_service.apply_config(config)
            else:
                cache_service.apply_default_config()
            
            # Initialize cache service
            cache_service.initialize()
            
            # Get current configuration
            current_config = cache_service.get_config()
            
            return {
                "status": "success",
                "config": current_config
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _clear_cache(self, cache_service: Any) -> Dict[str, Any]:
        """Clear cache data.
        
        Args:
            cache_service: Cache service
            
        Returns:
            Clear results
        """
        try:
            # Get cache stats before clearing
            before_stats = cache_service.get_stats()
            
            # Clear cache
            cache_service.clear()
            
            # Get cache stats after clearing
            after_stats = cache_service.get_stats()
            
            return {
                "status": "success",
                "before": before_stats,
                "after": after_stats
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _warm_up_cache(self, cache_service: Any) -> Dict[str, Any]:
        """Warm up cache.
        
        Args:
            cache_service: Cache service
            
        Returns:
            Warm-up results
        """
        try:
            # Get warm-up queries
            queries = cache_service.get_warm_up_queries()
            
            results = []
            for query in queries:
                try:
                    result = cache_service.execute_warm_up_query(query)
                    results.append({
                        "query": query,
                        "status": "success",
                        "details": result
                    })
                except Exception as e:
                    results.append({
                        "query": query,
                        "status": "error",
                        "error": str(e)
                    })
            
            # Get cache stats after warm-up
            stats = cache_service.get_stats()
            
            return {
                "status": "success",
                "queries": results,
                "stats": stats
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
    
    def reset(self, cache_service: Any) -> Dict[str, Any]:
        """Reset cache service.
        
        Args:
            cache_service: Cache service
            
        Returns:
            Reset results
        """
        try:
            # Clear all data
            clear_result = self._clear_cache(cache_service)
            if clear_result["status"] != "success":
                return clear_result
            
            # Reset configuration
            cache_service.reset_config()
            
            # Stop service
            cache_service.stop()
            
            return {
                "status": "success",
                "clear": clear_result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            } 