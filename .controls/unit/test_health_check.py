"""Unit tests for health check base implementation."""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from ..commands.health.base import (
    HealthCheck,
    HealthCheckResult,
    HealthCheckError,
    HealthCheckTimeout,
    HealthCheckDependencyError
)

class TestHealthCheck(HealthCheck):
    """Test health check implementation."""
    
    def __init__(
        self,
        name: str = "test_check",
        check_type: str = "test",
        should_pass: bool = True,
        execution_time: float = 0.1
    ):
        """Initialize test check.
        
        Args:
            name: Check name
            check_type: Check type
            should_pass: Whether check should pass
            execution_time: Simulated execution time in seconds
        """
        super().__init__(name, check_type)
        self.should_pass = should_pass
        self.execution_time = execution_time
    
    async def check_health(self) -> HealthCheckResult:
        """Execute test health check."""
        # Simulate check execution
        await asyncio.sleep(self.execution_time)
        
        if self.should_pass:
            return self._create_result(
                status="healthy",
                details={"test": True},
                metrics={"execution_time": self.execution_time},
                duration_ms=self.execution_time * 1000
            )
        else:
            return self._create_result(
                status="unhealthy",
                error="Test check failed",
                details={"test": False},
                metrics={"execution_time": self.execution_time},
                duration_ms=self.execution_time * 1000
            )

@pytest.fixture
def health_check() -> TestHealthCheck:
    """Create test health check."""
    return TestHealthCheck()

@pytest.fixture
def failing_check() -> TestHealthCheck:
    """Create failing test health check."""
    return TestHealthCheck(should_pass=False)

@pytest.fixture
def slow_check() -> TestHealthCheck:
    """Create slow test health check."""
    return TestHealthCheck(execution_time=1.0)

def test_health_check_initialization(health_check):
    """Test health check initialization."""
    assert health_check.name == "test_check"
    assert health_check.check_type == "test"
    assert isinstance(health_check.logger, logging.Logger)
    assert not health_check.dependencies

def test_health_check_dependencies(health_check):
    """Test health check dependency management."""
    # Add dependencies
    health_check.add_dependency("dep1")
    health_check.add_dependency("dep2")
    assert health_check.dependencies == {"dep1", "dep2"}
    
    # Remove dependency
    health_check.remove_dependency("dep1")
    assert health_check.dependencies == {"dep2"}
    
    # Remove non-existent dependency
    health_check.remove_dependency("dep3")
    assert health_check.dependencies == {"dep2"}

@pytest.mark.asyncio
async def test_successful_health_check(health_check):
    """Test successful health check execution."""
    result = await health_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "healthy"
    assert result.check_name == health_check.name
    assert result.check_type == health_check.check_type
    assert isinstance(result.timestamp, datetime)
    assert result.duration_ms == pytest.approx(100, rel=0.1)
    assert result.details == {"test": True}
    assert result.metrics == {"execution_time": 0.1}
    assert not result.error
    assert not result.warnings
    assert result.is_healthy
    assert not result.has_warnings

@pytest.mark.asyncio
async def test_failing_health_check(failing_check):
    """Test failing health check execution."""
    result = await failing_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert result.error == "Test check failed"
    assert not result.is_healthy

@pytest.mark.asyncio
async def test_slow_health_check(slow_check):
    """Test slow health check execution."""
    result = await slow_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "healthy"
    assert result.duration_ms == pytest.approx(1000, rel=0.1)

def test_health_check_result_serialization(health_check):
    """Test health check result serialization."""
    result = HealthCheckResult(
        status="healthy",
        check_name="test",
        check_type="test",
        timestamp=datetime.now(),
        duration_ms=100,
        details={"test": True},
        metrics={"value": 42},
        warnings=["test warning"]
    )
    
    data = result.to_dict()
    assert isinstance(data, dict)
    assert data["status"] == "healthy"
    assert data["check_name"] == "test"
    assert data["check_type"] == "test"
    assert isinstance(data["timestamp"], str)
    assert data["duration_ms"] == 100
    assert data["details"] == {"test": True}
    assert data["metrics"] == {"value": 42}
    assert not data["error"]
    assert data["warnings"] == ["test warning"]

def test_health_check_result_properties():
    """Test health check result properties."""
    # Healthy result
    result = HealthCheckResult(
        status="healthy",
        check_name="test",
        check_type="test"
    )
    assert result.is_healthy
    assert not result.has_warnings
    
    # Unhealthy result
    result = HealthCheckResult(
        status="unhealthy",
        check_name="test",
        check_type="test",
        error="Test error"
    )
    assert not result.is_healthy
    assert not result.has_warnings
    
    # Result with warnings
    result = HealthCheckResult(
        status="healthy",
        check_name="test",
        check_type="test",
        warnings=["Test warning"]
    )
    assert result.is_healthy
    assert result.has_warnings 