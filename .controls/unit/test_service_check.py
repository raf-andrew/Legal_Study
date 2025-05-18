"""Unit tests for service health checks."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
import asyncio
import logging

from ..commands.health.checks.service import (
    ServiceHealthCheck,
    ServiceAvailabilityCheck,
    ServiceResponseTimeCheck,
    ServiceErrorRateCheck,
    ServiceResourceUsageCheck
)
from ..commands.health.base import HealthCheckResult
from ...mocks.registry import MockServiceRegistry

@pytest.fixture
def mock_registry() -> MagicMock:
    """Create mock service registry."""
    registry = MagicMock(spec=MockServiceRegistry)
    registry.list_services.return_value = ["api", "database", "cache"]
    return registry

@pytest.fixture
def service_check(mock_registry) -> ServiceHealthCheck:
    """Create service check instance."""
    return ServiceHealthCheck(mock_registry)

class TestServiceCheck(ServiceHealthCheck):
    """Test service check implementation."""
    
    def __init__(
        self,
        name: str = "test_service",
        service_name: str = "test",
        should_pass: bool = True,
        should_timeout: bool = False,
        should_raise: bool = False,
        required: bool = True,
        timeout_ms: int = 5000
    ):
        """Initialize test service check.
        
        Args:
            name: Check name
            service_name: Service name
            should_pass: Whether check should pass
            should_timeout: Whether check should timeout
            should_raise: Whether check should raise exception
            required: Whether service is required
            timeout_ms: Check timeout in milliseconds
        """
        super().__init__(name, service_name, required, timeout_ms)
        self.should_pass = should_pass
        self.should_timeout = should_timeout
        self.should_raise = should_raise
    
    async def _check_service(self) -> HealthCheckResult:
        """Execute test service check."""
        if self.should_timeout:
            await asyncio.sleep(self.timeout_ms / 1000 + 1)
            return self._create_result(status="healthy")
        
        if self.should_raise:
            raise Exception("Test service check error")
        
        if self.should_pass:
            return self._create_result(
                status="healthy",
                details={"test": True},
                metrics={"value": 42}
            )
        else:
            return self._create_result(
                status="unhealthy",
                error="Test service check failed",
                details={"test": False},
                metrics={"value": 0}
            )

@pytest.fixture
def service_check() -> TestServiceCheck:
    """Create test service check."""
    return TestServiceCheck()

@pytest.fixture
def failing_check() -> TestServiceCheck:
    """Create failing service check."""
    return TestServiceCheck(should_pass=False)

@pytest.fixture
def timeout_check() -> TestServiceCheck:
    """Create timing out service check."""
    return TestServiceCheck(should_timeout=True)

@pytest.fixture
def error_check() -> TestServiceCheck:
    """Create error raising service check."""
    return TestServiceCheck(should_raise=True)

@pytest.fixture
def optional_check() -> TestServiceCheck:
    """Create optional service check."""
    return TestServiceCheck(required=False)

@pytest.mark.asyncio
async def test_service_check_initialization(service_check):
    """Test service check initialization."""
    assert service_check.name == "test_service"
    assert service_check.service_name == "test"
    assert service_check.check_type == "service"
    assert service_check.required
    assert service_check.timeout_ms == 5000
    assert isinstance(service_check.logger, logging.Logger)

@pytest.mark.asyncio
async def test_successful_service_check(service_check):
    """Test successful service check execution."""
    result = await service_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "healthy"
    assert result.check_name == service_check.name
    assert result.check_type == "service"
    assert isinstance(result.timestamp, datetime)
    assert isinstance(result.duration_ms, float)
    assert result.details == {"test": True}
    assert result.metrics == {"value": 42}
    assert not result.error
    assert not result.warnings
    assert result.is_healthy
    assert not result.has_warnings

@pytest.mark.asyncio
async def test_failing_service_check(failing_check):
    """Test failing service check execution."""
    result = await failing_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert result.error == "Test service check failed"
    assert result.details == {"test": False}
    assert result.metrics == {"value": 0}
    assert not result.is_healthy

@pytest.mark.asyncio
async def test_service_check_timeout(timeout_check):
    """Test service check timeout."""
    result = await timeout_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert "timed out" in result.error
    assert not result.is_healthy

@pytest.mark.asyncio
async def test_service_check_error(error_check):
    """Test service check error."""
    result = await error_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert result.error == "Test service check error"
    assert not result.is_healthy

@pytest.mark.asyncio
async def test_optional_service_check(optional_check):
    """Test optional service check."""
    # Test timeout
    optional_check.should_timeout = True
    result = await optional_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "warning"
    assert "timed out" in result.warnings[0]
    assert result.is_healthy
    assert result.has_warnings
    
    # Test error
    optional_check.should_timeout = False
    optional_check.should_raise = True
    result = await optional_check.check_health()
    
    assert result.status == "warning"
    assert "Test service check error" in result.warnings[0]
    assert result.is_healthy
    assert result.has_warnings

@pytest.mark.asyncio
async def test_service_availability_check():
    """Test service availability check."""
    check = ServiceAvailabilityCheck("test", "test_service")
    result = await check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "healthy"
    assert result.details == {"available": True}
    assert result.metrics == {"uptime": 100}
    assert result.is_healthy

@pytest.mark.asyncio
async def test_service_response_time_check():
    """Test service response time check."""
    check = ServiceResponseTimeCheck(
        "test",
        "test_service",
        warning_threshold_ms=500,
        error_threshold_ms=1000
    )
    result = await check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "warning"
    assert "warning threshold" in result.warnings[0]
    assert result.details["response_time"] == 800
    assert result.metrics["response_time"] == 800
    assert result.is_healthy
    assert result.has_warnings

@pytest.mark.asyncio
async def test_service_error_rate_check():
    """Test service error rate check."""
    check = ServiceErrorRateCheck(
        "test",
        "test_service",
        warning_threshold=0.01,
        error_threshold=0.05
    )
    result = await check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "warning"
    assert "warning threshold" in result.warnings[0]
    assert result.details["error_rate"] == 0.02
    assert result.metrics["error_rate"] == 0.02
    assert result.is_healthy
    assert result.has_warnings

@pytest.mark.asyncio
async def test_service_resource_usage_check():
    """Test service resource usage check."""
    check = ServiceResourceUsageCheck(
        "test",
        "test_service",
        cpu_warning_threshold=0.8,
        cpu_error_threshold=0.95,
        memory_warning_threshold=0.8,
        memory_error_threshold=0.95
    )
    result = await check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "warning"
    assert "CPU usage" in result.warnings[0]
    assert result.details["cpu_usage"] == 0.85
    assert result.details["memory_usage"] == 0.75
    assert result.metrics["cpu_usage"] == 0.85
    assert result.metrics["memory_usage"] == 0.75
    assert result.is_healthy
    assert result.has_warnings

def test_service_check_all_healthy(service_check, mock_registry):
    """Test service check with all services healthy."""
    # Mock service metrics and errors
    mock_service = MagicMock()
    mock_service.get_metrics.return_value = {
        "started_at": datetime.now().isoformat(),
        "total_calls": 10,
        "total_errors": 0
    }
    mock_service.get_errors.return_value = []
    
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.execute()
    assert result["status"] == "healthy"
    assert "start_time" in result
    assert "end_time" in result
    assert "duration" in result
    assert result["details"]["healthy"] is True
    
    for service_status in result["details"]["services"].values():
        assert service_status["status"] == "healthy"
        assert service_status["total_errors"] == 0

def test_service_check_with_errors(service_check, mock_registry):
    """Test service check with service errors."""
    # Mock service with errors
    mock_service = MagicMock()
    mock_service.get_metrics.return_value = {
        "started_at": datetime.now().isoformat(),
        "total_calls": 10,
        "total_errors": 2
    }
    mock_service.get_errors.return_value = [
        {"error": "Test error", "timestamp": datetime.now().isoformat()}
    ]
    
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.execute()
    assert result["status"] == "unhealthy"
    assert result["details"]["healthy"] is False
    
    for service_status in result["details"]["services"].values():
        assert service_status["status"] == "unhealthy"
        assert service_status["total_errors"] == 2
        assert "errors" in service_status

def test_service_check_with_exception(service_check, mock_registry):
    """Test service check with exception."""
    # Mock service that raises exception
    mock_service = MagicMock()
    mock_service.get_metrics.side_effect = Exception("Test error")
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.execute()
    assert result["status"] == "unhealthy"
    assert result["details"]["healthy"] is False
    
    for service_status in result["details"]["services"].values():
        assert service_status["status"] == "error"
        assert "error" in service_status

def test_get_unhealthy_services(service_check, mock_registry):
    """Test getting unhealthy services."""
    # Mock services with different health states
    services = {
        "api": MagicMock(
            get_metrics=lambda: {"total_calls": 10, "total_errors": 0},
            get_errors=lambda: []
        ),
        "database": MagicMock(
            get_metrics=lambda: {"total_calls": 10, "total_errors": 2},
            get_errors=lambda: [{"error": "Test error"}]
        ),
        "cache": MagicMock(
            get_metrics=side_effect=Exception("Test error")
        )
    }
    
    def get_service(name):
        return services.get(name)
    
    mock_registry.get_service.side_effect = get_service
    mock_registry.list_services.return_value = list(services.keys())
    
    unhealthy_services = service_check.get_unhealthy_services()
    assert len(unhealthy_services) == 2
    assert "database" in unhealthy_services
    assert "cache" in unhealthy_services

def test_get_service_metrics(service_check, mock_registry):
    """Test getting service metrics."""
    # Mock service metrics
    metrics = {
        "started_at": datetime.now().isoformat(),
        "total_calls": 10,
        "total_errors": 0
    }
    mock_service = MagicMock()
    mock_service.get_metrics.return_value = metrics
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.get_service_metrics("api")
    assert result == metrics

def test_get_service_errors(service_check, mock_registry):
    """Test getting service errors."""
    # Mock service errors
    errors = [
        {"error": "Test error", "timestamp": datetime.now().isoformat()}
    ]
    mock_service = MagicMock()
    mock_service.get_errors.return_value = errors
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.get_service_errors("api")
    assert result == errors 