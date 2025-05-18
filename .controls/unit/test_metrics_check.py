"""Unit tests for metrics health check."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime
from typing import Dict, Any

from ..commands.health.checks.metrics import MetricsCheck
from ...mocks.registry import MockServiceRegistry

@pytest.fixture
def mock_registry() -> MagicMock:
    """Create mock service registry."""
    registry = MagicMock(spec=MockServiceRegistry)
    registry.list_services.return_value = ["api", "database", "cache"]
    return registry

@pytest.fixture
def metrics_check(mock_registry) -> MetricsCheck:
    """Create metrics check instance."""
    return MetricsCheck(mock_registry)

def test_metrics_check_initialization(metrics_check):
    """Test metrics check initialization."""
    assert metrics_check.name == "metrics"
    assert isinstance(metrics_check.registry, MagicMock)

def test_metrics_check_all_healthy(metrics_check, mock_registry):
    """Test metrics check with all services healthy."""
    # Mock metrics service
    metrics_service = MagicMock()
    metrics_service.collect_system_metrics.return_value = {
        "cpu": 50.0,
        "memory": 60.0,
        "disk": 70.0
    }
    
    # Mock regular service
    service = MagicMock()
    service.get_metrics.return_value = {
        "started_at": datetime.now().isoformat(),
        "total_calls": 10,
        "total_errors": 0
    }
    
    def get_service(name):
        return metrics_service if name == "metrics" else service
    
    mock_registry.get_service.side_effect = get_service
    
    result = metrics_check.execute()
    assert result["status"] == "healthy"
    assert result["details"]["healthy"] is True
    assert "system" in result["details"]
    assert len(result["details"]["services"]) == 3
    assert len(result["details"]["unhealthy_services"]) == 0

def test_metrics_check_with_errors(metrics_check, mock_registry):
    """Test metrics check with service errors."""
    # Mock metrics service
    metrics_service = MagicMock()
    metrics_service.collect_system_metrics.return_value = {
        "cpu": 50.0,
        "memory": 60.0,
        "disk": 70.0
    }
    
    # Mock services with different states
    services = {
        "api": MagicMock(
            get_metrics=lambda: {
                "total_calls": 10,
                "total_errors": 0
            }
        ),
        "database": MagicMock(
            get_metrics=lambda: {
                "total_calls": 10,
                "total_errors": 2
            }
        ),
        "cache": MagicMock(
            get_metrics=side_effect=Exception("Test error")
        )
    }
    
    def get_service(name):
        if name == "metrics":
            return metrics_service
        return services.get(name)
    
    mock_registry.get_service.side_effect = get_service
    mock_registry.list_services.return_value = list(services.keys())
    
    result = metrics_check.execute()
    assert result["status"] == "unhealthy"
    assert result["details"]["healthy"] is False
    assert len(result["details"]["unhealthy_services"]) == 2
    assert "database" in result["details"]["unhealthy_services"]
    assert "cache" in result["details"]["unhealthy_services"]

def test_metrics_check_no_metrics_service(metrics_check, mock_registry):
    """Test metrics check without metrics service."""
    mock_registry.get_service.return_value = None
    
    result = metrics_check.execute()
    assert result["status"] == "error"
    assert "Metrics service not available" in result["error"]

def test_get_service_metrics(metrics_check, mock_registry):
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
    
    result = metrics_check.get_service_metrics("api")
    assert result == metrics

def test_get_system_metrics(metrics_check, mock_registry):
    """Test getting system metrics."""
    # Mock metrics service
    system_metrics = {
        "cpu": 50.0,
        "memory": 60.0,
        "disk": 70.0
    }
    metrics_service = MagicMock()
    metrics_service.collect_system_metrics.return_value = system_metrics
    mock_registry.get_service.return_value = metrics_service
    
    result = metrics_check.get_system_metrics()
    assert result == system_metrics

def test_get_metrics_by_type(metrics_check, mock_registry):
    """Test getting metrics by type."""
    # Mock metrics service
    type_metrics = {
        "requests": {
            "total": 100,
            "success": 95,
            "error": 5
        }
    }
    metrics_service = MagicMock()
    metrics_service.collect_metrics_by_type.return_value = type_metrics
    mock_registry.get_service.return_value = metrics_service
    
    result = metrics_check.get_metrics_by_type("requests")
    assert result == type_metrics

def test_get_metrics_summary(metrics_check, mock_registry):
    """Test getting metrics summary."""
    # Mock metrics service
    metrics_service = MagicMock()
    metrics_service.collect_system_metrics.return_value = {
        "cpu": 50.0,
        "memory": 60.0,
        "disk": 70.0
    }
    
    # Mock services
    services = {
        "api": MagicMock(
            get_metrics=lambda: {
                "total_calls": 10,
                "total_errors": 0
            }
        ),
        "database": MagicMock(
            get_metrics=lambda: {
                "total_calls": 10,
                "total_errors": 2
            }
        )
    }
    
    def get_service(name):
        if name == "metrics":
            return metrics_service
        return services.get(name)
    
    mock_registry.get_service.side_effect = get_service
    mock_registry.list_services.return_value = list(services.keys())
    
    result = metrics_check.get_metrics_summary()
    assert result["total_services"] == 2
    assert result["healthy_services"] == 1
    assert result["unhealthy_services"] == 1
    assert result["health_percentage"] == 50.0 