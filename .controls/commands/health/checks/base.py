"""Base class for health checks."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

class BaseCheck(ABC):
    """Base class for health checks."""
    
    def __init__(self, name: str):
        """Initialize health check.
        
        Args:
            name: Name of the health check
        """
        self.name = name
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
    def execute(self) -> Dict[str, Any]:
        """Execute health check.
        
        Returns:
            Health check results
        """
        self.start_time = datetime.now()
        try:
            result = self._execute()
            self.end_time = datetime.now()
            return {
                "name": self.name,
                "status": "healthy" if result["healthy"] else "unhealthy",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration": (self.end_time - self.start_time).total_seconds(),
                "details": result
            }
        except Exception as e:
            self.end_time = datetime.now()
            return {
                "name": self.name,
                "status": "error",
                "start_time": self.start_time.isoformat(),
                "end_time": self.end_time.isoformat(),
                "duration": (self.end_time - self.start_time).total_seconds(),
                "error": str(e)
            }
    
    @abstractmethod
    def _execute(self) -> Dict[str, Any]:
        """Execute health check implementation.
        
        Returns:
            Health check results
        """
        pass 