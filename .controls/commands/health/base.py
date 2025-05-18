"""Base interface for health checks."""

import abc
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

@dataclass
class HealthCheckResult:
    """Result of a health check execution."""
    
    status: str  # "healthy", "unhealthy", "warning"
    check_name: str
    check_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    @property
    def is_healthy(self) -> bool:
        """Check if result indicates healthy status."""
        return self.status == "healthy"
    
    @property
    def has_warnings(self) -> bool:
        """Check if result has warnings."""
        return len(self.warnings) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status,
            "check_name": self.check_name,
            "check_type": self.check_type,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "details": self.details,
            "metrics": self.metrics,
            "error": self.error,
            "warnings": self.warnings
        }

class HealthCheck(abc.ABC):
    """Base class for health checks."""
    
    def __init__(self, name: str, check_type: str):
        """Initialize health check.
        
        Args:
            name: Name of the health check
            check_type: Type of health check (e.g., "service", "database")
        """
        self.name = name
        self.check_type = check_type
        self.logger = logging.getLogger(f"health.{check_type}.{name}")
        self._dependencies: Set[str] = set()
    
    @property
    def dependencies(self) -> Set[str]:
        """Get health check dependencies.
        
        Returns:
            Set of dependency check names
        """
        return self._dependencies
    
    def add_dependency(self, check_name: str) -> None:
        """Add a dependency check.
        
        Args:
            check_name: Name of dependent check
        """
        self._dependencies.add(check_name)
    
    def remove_dependency(self, check_name: str) -> None:
        """Remove a dependency check.
        
        Args:
            check_name: Name of dependency to remove
        """
        self._dependencies.discard(check_name)
    
    @abc.abstractmethod
    async def check_health(self) -> HealthCheckResult:
        """Execute health check.
        
        Returns:
            Health check result
            
        Raises:
            HealthCheckError: If check fails unexpectedly
        """
        raise NotImplementedError("Health checks must implement check_health")
    
    def _create_result(
        self,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, float]] = None,
        error: Optional[str] = None,
        warnings: Optional[List[str]] = None,
        duration_ms: Optional[float] = None
    ) -> HealthCheckResult:
        """Create a health check result.
        
        Args:
            status: Health status
            details: Optional check details
            metrics: Optional check metrics
            error: Optional error message
            warnings: Optional warning messages
            duration_ms: Optional check duration in milliseconds
            
        Returns:
            Health check result
        """
        return HealthCheckResult(
            status=status,
            check_name=self.name,
            check_type=self.check_type,
            details=details or {},
            metrics=metrics or {},
            error=error,
            warnings=warnings or [],
            duration_ms=duration_ms
        )

class HealthCheckError(Exception):
    """Base class for health check errors."""
    pass

class HealthCheckTimeout(HealthCheckError):
    """Error raised when health check times out."""
    pass

class HealthCheckDependencyError(HealthCheckError):
    """Error raised when dependency check fails."""
    pass 