"""Logs health check implementation."""

from typing import Any, Dict, List
from datetime import datetime, timedelta
from .base import BaseCheck
from ...mocks.registry import MockServiceRegistry

class LogsCheck(BaseCheck):
    """Logs health check implementation."""
    
    def __init__(self, registry: MockServiceRegistry):
        """Initialize logs check.
        
        Args:
            registry: Service registry instance
        """
        super().__init__("logs")
        self.registry = registry
    
    def _execute(self) -> Dict[str, Any]:
        """Execute logs health check.
        
        Returns:
            Logs health check results
        """
        logging_service = self.registry.get_service("logging")
        if not logging_service:
            return {
                "healthy": False,
                "error": "Logging service not available"
            }
        
        try:
            # Check log handlers
            handlers = logging_service.list_handlers()
            handler_stats = {}
            
            for handler in handlers:
                try:
                    records = logging_service.get_records(handler)
                    last_record = records[-1] if records else None
                    
                    handler_stats[handler] = {
                        "status": "active",
                        "total_records": len(records),
                        "last_record": last_record,
                        "last_record_time": last_record["timestamp"]
                        if last_record else None
                    }
                except Exception as e:
                    handler_stats[handler] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Check service logs
            service_logs = {}
            for service_name in self.registry.list_services():
                service = self.registry.get_service(service_name)
                if not service:
                    continue
                
                try:
                    logs = service.get_logs()
                    service_logs[service_name] = {
                        "status": "collected",
                        "total_logs": len(logs),
                        "last_log": logs[-1] if logs else None
                    }
                except Exception as e:
                    service_logs[service_name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Check log freshness
            now = datetime.now()
            stale_threshold = now - timedelta(minutes=5)
            
            stale_handlers = [
                name for name, stats in handler_stats.items()
                if stats["status"] == "active" and
                (not stats["last_record_time"] or
                 datetime.fromisoformat(stats["last_record_time"]) < stale_threshold)
            ]
            
            inactive_handlers = [
                name for name, stats in handler_stats.items()
                if stats["status"] == "error"
            ]
            
            return {
                "healthy": len(stale_handlers) == 0 and len(inactive_handlers) == 0,
                "handlers": handler_stats,
                "services": service_logs,
                "stale_handlers": stale_handlers,
                "inactive_handlers": inactive_handlers
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def get_handler_stats(self, handler: str) -> Dict[str, Any]:
        """Get statistics for specific log handler.
        
        Args:
            handler: Name of the handler
            
        Returns:
            Handler statistics
        """
        logging_service = self.registry.get_service("logging")
        if not logging_service:
            return {
                "error": "Logging service not available"
            }
        
        try:
            records = logging_service.get_records(handler)
            return {
                "total_records": len(records),
                "last_record": records[-1] if records else None,
                "levels": self._count_log_levels(records)
            }
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def get_service_logs(self, service_name: str) -> List[Dict[str, Any]]:
        """Get logs for specific service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service logs
        """
        service = self.registry.get_service(service_name)
        if not service:
            return [{
                "error": f"Service {service_name} not found"
            }]
        
        try:
            return service.get_logs()
        except Exception as e:
            return [{
                "error": str(e)
            }]
    
    def get_logs_by_level(self, level: str) -> List[Dict[str, Any]]:
        """Get logs by level.
        
        Args:
            level: Log level to filter
            
        Returns:
            Filtered logs
        """
        logging_service = self.registry.get_service("logging")
        if not logging_service:
            return [{
                "error": "Logging service not available"
            }]
        
        try:
            return logging_service.get_logs_by_level(level)
        except Exception as e:
            return [{
                "error": str(e)
            }]
    
    def _count_log_levels(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count logs by level.
        
        Args:
            records: List of log records
            
        Returns:
            Count of logs by level
        """
        counts = {}
        for record in records:
            level = record.get("level", "UNKNOWN")
            counts[level] = counts.get(level, 0) + 1
        return counts 