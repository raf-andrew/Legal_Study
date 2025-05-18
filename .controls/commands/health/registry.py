"""Registry for managing health checks."""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Type

from .base import HealthCheck, HealthCheckResult, HealthCheckDependencyError

class HealthCheckRegistry:
    """Registry for managing and executing health checks."""
    
    def __init__(self):
        """Initialize health check registry."""
        self._checks: Dict[str, HealthCheck] = {}
        self.logger = logging.getLogger("health.registry")
    
    def register(self, check: HealthCheck) -> None:
        """Register a health check.
        
        Args:
            check: Health check to register
            
        Raises:
            ValueError: If check with same name already registered
        """
        if check.name in self._checks:
            raise ValueError(f"Health check already registered: {check.name}")
        
        self._checks[check.name] = check
        self.logger.info(f"Registered health check: {check.name} ({check.check_type})")
    
    def unregister(self, check_name: str) -> None:
        """Unregister a health check.
        
        Args:
            check_name: Name of check to unregister
            
        Raises:
            KeyError: If check not registered
        """
        if check_name not in self._checks:
            raise KeyError(f"Health check not registered: {check_name}")
        
        # Check for dependent checks
        dependent_checks = self._get_dependent_checks(check_name)
        if dependent_checks:
            raise ValueError(
                f"Cannot unregister check with dependencies: {check_name} "
                f"(dependent checks: {', '.join(dependent_checks)})"
            )
        
        del self._checks[check_name]
        self.logger.info(f"Unregistered health check: {check_name}")
    
    def get_check(self, check_name: str) -> HealthCheck:
        """Get a registered health check.
        
        Args:
            check_name: Name of check to get
            
        Returns:
            Registered health check
            
        Raises:
            KeyError: If check not registered
        """
        if check_name not in self._checks:
            raise KeyError(f"Health check not registered: {check_name}")
        return self._checks[check_name]
    
    def list_checks(
        self,
        check_type: Optional[str] = None
    ) -> List[HealthCheck]:
        """List registered health checks.
        
        Args:
            check_type: Optional type to filter by
            
        Returns:
            List of registered checks
        """
        if check_type:
            return [
                check for check in self._checks.values()
                if check.check_type == check_type
            ]
        return list(self._checks.values())
    
    def _get_dependent_checks(self, check_name: str) -> Set[str]:
        """Get checks that depend on a check.
        
        Args:
            check_name: Name of check to find dependents for
            
        Returns:
            Set of dependent check names
        """
        return {
            name for name, check in self._checks.items()
            if check_name in check.dependencies
        }
    
    def _validate_dependencies(self, check: HealthCheck) -> None:
        """Validate check dependencies.
        
        Args:
            check: Check to validate dependencies for
            
        Raises:
            HealthCheckDependencyError: If dependencies invalid
        """
        for dependency in check.dependencies:
            if dependency not in self._checks:
                raise HealthCheckDependencyError(
                    f"Missing dependency for {check.name}: {dependency}"
                )
    
    async def run_check(self, check_name: str) -> HealthCheckResult:
        """Run a specific health check.
        
        Args:
            check_name: Name of check to run
            
        Returns:
            Health check result
            
        Raises:
            KeyError: If check not registered
            HealthCheckDependencyError: If dependencies fail
        """
        check = self.get_check(check_name)
        self._validate_dependencies(check)
        
        # Run dependency checks first
        for dependency in check.dependencies:
            result = await self.run_check(dependency)
            if not result.is_healthy:
                raise HealthCheckDependencyError(
                    f"Dependency check failed for {check_name}: {dependency} "
                    f"({result.error or 'unknown error'})"
                )
        
        self.logger.debug(f"Running health check: {check_name}")
        return await check.check_health()
    
    async def run_all_checks(
        self,
        check_type: Optional[str] = None
    ) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks.
        
        Args:
            check_type: Optional type to filter by
            
        Returns:
            Dictionary of check names to results
        """
        checks = self.list_checks(check_type)
        results = {}
        
        for check in checks:
            try:
                results[check.name] = await self.run_check(check.name)
            except Exception as e:
                self.logger.error(
                    f"Health check failed: {check.name}",
                    exc_info=True
                )
                results[check.name] = check._create_result(
                    status="unhealthy",
                    error=str(e)
                )
        
        return results 