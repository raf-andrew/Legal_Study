"""Unit tests for service health check command."""

import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from ..commands.health.checks.service import ServiceCheck
from ..mocks.registry import MockServiceRegistry

@pytest.fixture
def mock_registry():
    """Create mock service registry."""
    registry = MagicMock(spec=MockServiceRegistry)
    registry.list_services.return_value = ["api", "database", "cache"]
    return registry

@pytest.fixture
def mock_service():
    """Create mock service."""
    service = MagicMock()
    
    # Basic health
    service.is_running.return_value = True
    service.get_health_info.return_value = {
        "uptime": 3600,
        "version": "1.0.0",
        "environment": "test"
    }
    
    # Dependencies
    service.list_dependencies.return_value = ["database", "cache"]
    service.check_dependency.return_value = {
        "available": True,
        "latency": 50
    }
    
    # Resources
    service.get_resource_metrics.return_value = {
        "cpu_usage": 45.0,
        "memory_usage": 60.0,
        "disk_usage": 55.0
    }
    service.get_resource_thresholds.return_value = {
        "cpu_usage": 80.0,
        "memory_usage": 80.0,
        "disk_usage": 80.0
    }
    
    # Endpoints
    service.list_endpoints.return_value = ["/health", "/status"]
    service.check_endpoint.return_value = {
        "healthy": True,
        "response_time": 50,
        "status_code": 200
    }
    
    return service

@pytest.fixture
def service_check(mock_registry):
    """Create service check instance."""
    return ServiceCheck(mock_registry)

def test_service_check_initialization(service_check):
    """Test service check initialization."""
    assert service_check.name == "service"
    assert service_check.description == "Check service health and status"
    assert isinstance(service_check.registry, MagicMock)

def test_service_check_validation(service_check):
    """Test service check validation."""
    assert service_check.validate() is None
    assert service_check.validate(services=["api"]) is None
    assert service_check.validate(services="api") == "Services must be a list"
    assert "Unknown services" in service_check.validate(services=["unknown"])

def test_service_check_execution(service_check, mock_registry, mock_service):
    """Test service check execution."""
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.execute()
    
    assert result["status"] == "healthy"
    assert "timestamp" in result
    assert all(
        service["healthy"] is True
        for service in result["details"]["services"].values()
    )

def test_service_check_specific_services(service_check, mock_registry, mock_service):
    """Test service check with specific services."""
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.execute(services=["api"])
    
    assert result["status"] == "healthy"
    assert len(result["details"]["services"]) == 1
    assert "api" in result["details"]["services"]

def test_service_check_service_not_found(service_check, mock_registry):
    """Test service check with non-existent service."""
    mock_registry.get_service.return_value = None
    
    result = service_check.execute(services=["unknown"])
    assert result["status"] == "unhealthy"
    assert result["details"]["services"]["unknown"]["healthy"] is False
    assert "Service not found" in result["details"]["services"]["unknown"]["error"]

def test_service_check_not_running(service_check, mock_registry, mock_service):
    """Test service check with service not running."""
    mock_service.is_running.return_value = False
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.execute()
    assert result["status"] == "unhealthy"
    assert all(
        not service["health"]["healthy"]
        for service in result["details"]["services"].values()
    )

def test_service_check_dependency_error(service_check, mock_registry, mock_service):
    """Test service check with dependency error."""
    mock_service.check_dependency.return_value = {
        "available": False,
        "error": "Connection failed"
    }
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.execute()
    assert result["status"] == "unhealthy"
    assert all(
        not service["dependencies"]["healthy"]
        for service in result["details"]["services"].values()
    )

def test_service_check_resource_issues(service_check, mock_registry, mock_service):
    """Test service check with resource issues."""
    mock_service.get_resource_metrics.return_value = {
        "cpu_usage": 90.0,
        "memory_usage": 85.0,
        "disk_usage": 75.0
    }
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.execute()
    assert result["status"] == "unhealthy"
    assert all(
        not service["resources"]["healthy"]
        for service in result["details"]["services"].values()
    )
    assert all(
        len(service["resources"]["issues"]) == 2  # CPU and memory exceed thresholds
        for service in result["details"]["services"].values()
    )

def test_service_check_endpoint_error(service_check, mock_registry, mock_service):
    """Test service check with endpoint error."""
    mock_service.check_endpoint.return_value = {
        "healthy": False,
        "error": "Endpoint not responding"
    }
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.execute()
    assert result["status"] == "unhealthy"
    assert all(
        not service["endpoints"]["healthy"]
        for service in result["details"]["services"].values()
    )

def test_service_check_exception_handling(service_check, mock_registry, mock_service):
    """Test service check exception handling."""
    mock_service.is_running.side_effect = Exception("Service check failed")
    mock_registry.get_service.return_value = mock_service
    
    result = service_check.execute()
    assert result["status"] == "unhealthy"
    assert all(
        service["status"] == "error"
        for service in result["details"]["services"].values()
    ) 