"""Service dependency health check implementation."""

import asyncio
import logging
from typing import Dict, List, Optional, Set

from ..base import HealthCheck, HealthCheckResult
from .service import ServiceHealthCheck

class ServiceDependencyCheck(ServiceHealthCheck):
    """Check service dependencies."""
    
    def __init__(
        self,
        name: str,
        service_name: str,
        dependencies: List[ServiceHealthCheck],
        required: bool = True,
        timeout_ms: int = 5000
    ):
        """Initialize dependency check.
        
        Args:
            name: Check name
            service_name: Name of service to check
            dependencies: List of dependency checks
            required: Whether service is required
            timeout_ms: Check timeout in milliseconds
        """
        super().__init__(name, service_name, required, timeout_ms)
        self.dependencies = dependencies
        self.logger = logging.getLogger(f"health.service.dependency.{service_name}")
    
    async def _check_service(self) -> HealthCheckResult:
        """Check service dependencies."""
        dependency_results = {}
        dependency_metrics = {}
        warnings = []
        errors = []
        
        # Run dependency checks concurrently
        tasks = [
            self._check_dependency(dep)
            for dep in self.dependencies
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for dependency, result in zip(self.dependencies, results):
            if isinstance(result, Exception):
                # Handle check failure
                error_msg = f"Dependency check failed for {dependency.service_name}: {str(result)}"
                if self.required:
                    errors.append(error_msg)
                else:
                    warnings.append(error_msg)
                continue
            
            # Store result
            dependency_results[dependency.service_name] = {
                "status": result.status,
                "error": result.error,
                "warnings": result.warnings,
                "details": result.details,
                "metrics": result.metrics
            }
            
            # Aggregate metrics
            for key, value in result.metrics.items():
                metric_key = f"{dependency.service_name}.{key}"
                dependency_metrics[metric_key] = value
            
            # Check status
            if not result.is_healthy:
                error_msg = (
                    f"Dependency {dependency.service_name} is unhealthy: "
                    f"{result.error or 'unknown error'}"
                )
                if self.required:
                    errors.append(error_msg)
                else:
                    warnings.append(error_msg)
            elif result.has_warnings:
                for warning in result.warnings:
                    warnings.append(
                        f"Dependency {dependency.service_name}: {warning}"
                    )
        
        # Determine overall status
        if errors:
            status = "unhealthy"
            error = errors[0]  # Use first error as main error
        elif warnings:
            status = "warning"
            error = None
        else:
            status = "healthy"
            error = None
        
        return self._create_result(
            status=status,
            error=error,
            warnings=warnings,
            details={
                "dependencies": dependency_results,
                "total_dependencies": len(self.dependencies),
                "failed_dependencies": len(errors)
            },
            metrics=dependency_metrics
        )
    
    async def _check_dependency(
        self,
        dependency: ServiceHealthCheck
    ) -> HealthCheckResult:
        """Check a single dependency.
        
        Args:
            dependency: Dependency to check
            
        Returns:
            Health check result
            
        Raises:
            Exception: If check fails
        """
        try:
            return await dependency.check_health()
        except Exception as e:
            self.logger.error(
                f"Failed to check dependency {dependency.service_name}",
                exc_info=True
            )
            raise

class ServiceDependencyGraphCheck(ServiceHealthCheck):
    """Check service dependency graph."""
    
    def __init__(
        self,
        name: str,
        service_name: str,
        dependencies: Dict[str, Set[str]],
        checks: Dict[str, ServiceHealthCheck],
        required: bool = True,
        timeout_ms: int = 5000
    ):
        """Initialize dependency graph check.
        
        Args:
            name: Check name
            service_name: Name of service to check
            dependencies: Mapping of service names to dependency sets
            checks: Mapping of service names to health checks
            required: Whether service is required
            timeout_ms: Check timeout in milliseconds
        """
        super().__init__(name, service_name, required, timeout_ms)
        self.dependencies = dependencies
        self.checks = checks
        self.logger = logging.getLogger(f"health.service.dependency_graph.{service_name}")
    
    async def _check_service(self) -> HealthCheckResult:
        """Check service dependency graph."""
        # Build execution order
        try:
            execution_order = self._build_execution_order()
        except ValueError as e:
            return self._create_result(
                status="unhealthy",
                error=f"Invalid dependency graph: {str(e)}",
                details={"dependencies": self.dependencies}
            )
        
        # Check services in order
        service_results = {}
        service_metrics = {}
        warnings = []
        errors = []
        
        for service_name in execution_order:
            # Skip if service not in checks
            if service_name not in self.checks:
                warnings.append(f"No health check for service: {service_name}")
                continue
            
            # Check service
            try:
                result = await self.checks[service_name].check_health()
                
                # Store result
                service_results[service_name] = {
                    "status": result.status,
                    "error": result.error,
                    "warnings": result.warnings,
                    "details": result.details,
                    "metrics": result.metrics,
                    "dependencies": list(self.dependencies.get(service_name, set()))
                }
                
                # Aggregate metrics
                for key, value in result.metrics.items():
                    metric_key = f"{service_name}.{key}"
                    service_metrics[metric_key] = value
                
                # Check status
                if not result.is_healthy:
                    error_msg = (
                        f"Service {service_name} is unhealthy: "
                        f"{result.error or 'unknown error'}"
                    )
                    if self.required:
                        errors.append(error_msg)
                    else:
                        warnings.append(error_msg)
                elif result.has_warnings:
                    for warning in result.warnings:
                        warnings.append(f"Service {service_name}: {warning}")
            
            except Exception as e:
                self.logger.error(
                    f"Failed to check service {service_name}",
                    exc_info=True
                )
                error_msg = f"Service check failed for {service_name}: {str(e)}"
                if self.required:
                    errors.append(error_msg)
                else:
                    warnings.append(error_msg)
        
        # Determine overall status
        if errors:
            status = "unhealthy"
            error = errors[0]  # Use first error as main error
        elif warnings:
            status = "warning"
            error = None
        else:
            status = "healthy"
            error = None
        
        return self._create_result(
            status=status,
            error=error,
            warnings=warnings,
            details={
                "services": service_results,
                "execution_order": execution_order,
                "total_services": len(execution_order),
                "failed_services": len(errors)
            },
            metrics=service_metrics
        )
    
    def _build_execution_order(self) -> List[str]:
        """Build service execution order based on dependencies.
        
        Returns:
            List of service names in execution order
            
        Raises:
            ValueError: If dependency graph has cycles
        """
        # Initialize
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service: str) -> None:
            """Visit service in dependency graph.
            
            Args:
                service: Service to visit
                
            Raises:
                ValueError: If cycle detected
            """
            # Check for cycle
            if service in temp_visited:
                raise ValueError(
                    f"Dependency cycle detected involving service: {service}"
                )
            
            # Skip if already visited
            if service in visited:
                return
            
            # Mark as temporarily visited
            temp_visited.add(service)
            
            # Visit dependencies
            for dependency in self.dependencies.get(service, set()):
                visit(dependency)
            
            # Mark as visited and add to order
            temp_visited.remove(service)
            visited.add(service)
            order.append(service)
        
        # Visit all services
        for service in self.dependencies:
            if service not in visited:
                visit(service)
        
        # Reverse to get correct order
        return list(reversed(order)) 