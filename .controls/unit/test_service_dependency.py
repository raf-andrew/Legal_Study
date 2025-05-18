"""Unit tests for service dependency checks."""

import pytest
from typing import Dict, List, Set

from ..commands.health.checks.service_dependency import (
    ServiceDependencyCheck,
    ServiceDependencyGraphCheck
)
from ..commands.health.checks.service import ServiceHealthCheck
from ..commands.health.base import HealthCheckResult

class MockServiceCheck(ServiceHealthCheck):
    """Mock service check for testing."""
    
    def __init__(
        self,
        name: str,
        service_name: str,
        should_pass: bool = True,
        should_warn: bool = False,
        should_raise: bool = False,
        required: bool = True,
        timeout_ms: int = 5000
    ):
        """Initialize mock service check."""
        super().__init__(name, service_name, required, timeout_ms)
        self.should_pass = should_pass
        self.should_warn = should_warn
        self.should_raise = should_raise
    
    async def _check_service(self) -> HealthCheckResult:
        """Execute mock service check."""
        if self.should_raise:
            raise Exception("Mock service check error")
        
        status = "healthy"
        error = None
        warnings = []
        
        if not self.should_pass:
            status = "unhealthy"
            error = "Mock service check failed"
        elif self.should_warn:
            warnings = ["Mock service warning"]
        
        return self._create_result(
            status=status,
            error=error,
            warnings=warnings,
            details={"mock": True},
            metrics={"value": 42 if self.should_pass else 0}
        )

@pytest.fixture
def mock_dependencies() -> List[MockServiceCheck]:
    """Create mock dependency checks."""
    return [
        MockServiceCheck("dep1", "service1"),
        MockServiceCheck("dep2", "service2"),
        MockServiceCheck("dep3", "service3", should_warn=True),
        MockServiceCheck("dep4", "service4", should_pass=False),
        MockServiceCheck("dep5", "service5", should_raise=True)
    ]

@pytest.fixture
def dependency_check(mock_dependencies) -> ServiceDependencyCheck:
    """Create service dependency check."""
    return ServiceDependencyCheck(
        "test_dependencies",
        "test_service",
        mock_dependencies
    )

@pytest.fixture
def dependency_graph() -> Dict[str, Set[str]]:
    """Create test dependency graph."""
    return {
        "service1": {"service2", "service3"},
        "service2": {"service4"},
        "service3": {"service4", "service5"},
        "service4": {"service5"},
        "service5": set()
    }

@pytest.fixture
def graph_checks() -> Dict[str, MockServiceCheck]:
    """Create test graph checks."""
    return {
        "service1": MockServiceCheck("check1", "service1"),
        "service2": MockServiceCheck("check2", "service2"),
        "service3": MockServiceCheck("check3", "service3", should_warn=True),
        "service4": MockServiceCheck("check4", "service4", should_pass=False),
        "service5": MockServiceCheck("check5", "service5")
    }

@pytest.fixture
def graph_check(dependency_graph, graph_checks) -> ServiceDependencyGraphCheck:
    """Create service dependency graph check."""
    return ServiceDependencyGraphCheck(
        "test_graph",
        "test_service",
        dependency_graph,
        graph_checks
    )

@pytest.mark.asyncio
async def test_dependency_check_all_healthy(dependency_check):
    """Test dependency check with all healthy dependencies."""
    # Override dependencies to all healthy
    dependency_check.dependencies = [
        MockServiceCheck(f"dep{i}", f"service{i}")
        for i in range(3)
    ]
    
    result = await dependency_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "healthy"
    assert not result.error
    assert not result.warnings
    assert result.details["total_dependencies"] == 3
    assert result.details["failed_dependencies"] == 0
    assert len(result.details["dependencies"]) == 3
    assert all(
        dep["status"] == "healthy"
        for dep in result.details["dependencies"].values()
    )

@pytest.mark.asyncio
async def test_dependency_check_with_warnings(dependency_check):
    """Test dependency check with warnings."""
    result = await dependency_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "warning"
    assert not result.error
    assert len(result.warnings) == 3  # One warning, one error, one exception
    assert result.details["total_dependencies"] == 5
    assert result.details["failed_dependencies"] == 2
    assert len(result.details["dependencies"]) == 3  # Two failed checks not included

@pytest.mark.asyncio
async def test_dependency_check_with_failures(dependency_check):
    """Test dependency check with failures."""
    # Make check required
    dependency_check.required = True
    
    result = await dependency_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert result.error
    assert len(result.warnings) == 1  # Just the warning
    assert result.details["total_dependencies"] == 5
    assert result.details["failed_dependencies"] == 2
    assert len(result.details["dependencies"]) == 3

@pytest.mark.asyncio
async def test_dependency_check_optional(dependency_check):
    """Test optional dependency check."""
    # Make check optional
    dependency_check.required = False
    
    result = await dependency_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "warning"
    assert not result.error
    assert len(result.warnings) == 3
    assert result.details["total_dependencies"] == 5
    assert result.details["failed_dependencies"] == 2
    assert len(result.details["dependencies"]) == 3

@pytest.mark.asyncio
async def test_dependency_graph_check_valid(graph_check):
    """Test dependency graph check with valid graph."""
    result = await graph_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"  # service4 fails
    assert result.error
    assert len(result.warnings) == 1  # service3 warning
    assert result.details["total_services"] == 5
    assert result.details["failed_services"] == 1
    assert len(result.details["services"]) == 5
    
    # Verify execution order
    order = result.details["execution_order"]
    assert len(order) == 5
    assert order.index("service5") < order.index("service4")
    assert order.index("service4") < order.index("service2")
    assert order.index("service4") < order.index("service3")
    assert order.index("service2") < order.index("service1")
    assert order.index("service3") < order.index("service1")

@pytest.mark.asyncio
async def test_dependency_graph_check_cycle():
    """Test dependency graph check with cycle."""
    # Create graph with cycle
    cyclic_graph = {
        "service1": {"service2"},
        "service2": {"service3"},
        "service3": {"service1"}
    }
    
    check = ServiceDependencyGraphCheck(
        "test_cycle",
        "test_service",
        cyclic_graph,
        {
            "service1": MockServiceCheck("check1", "service1"),
            "service2": MockServiceCheck("check2", "service2"),
            "service3": MockServiceCheck("check3", "service3")
        }
    )
    
    result = await check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert "cycle detected" in result.error
    assert result.details["dependencies"] == cyclic_graph

@pytest.mark.asyncio
async def test_dependency_graph_check_missing_check(graph_check):
    """Test dependency graph check with missing check."""
    # Remove a check
    del graph_check.checks["service5"]
    
    result = await graph_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "warning"
    assert "No health check for service: service5" in result.warnings
    assert len(result.details["services"]) == 4

@pytest.mark.asyncio
async def test_dependency_graph_check_optional(graph_check):
    """Test optional dependency graph check."""
    # Make check optional
    graph_check.required = False
    
    result = await graph_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "warning"
    assert not result.error
    assert len(result.warnings) == 2  # service3 warning and service4 failure
    assert result.details["total_services"] == 5
    assert result.details["failed_services"] == 1
    assert len(result.details["services"]) == 5 