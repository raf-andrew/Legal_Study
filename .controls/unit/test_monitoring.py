"""Unit tests for monitoring service."""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from ..commands.health.monitoring import MonitoringService

@pytest.fixture
def monitoring_service() -> MonitoringService:
    """Create monitoring service instance."""
    with patch("prometheus_client.start_http_server"):
        service = MonitoringService()
        service.reset_metrics()
        return service

def test_monitoring_service_initialization():
    """Test monitoring service initialization."""
    with patch("prometheus_client.start_http_server") as mock_start:
        # Test default configuration
        service = MonitoringService()
        assert service.metrics_port == 9090
        assert service.metrics_enabled is True
        mock_start.assert_called_once_with(9090)
        
        # Test custom configuration
        with patch.dict(os.environ, {
            "METRICS_PORT": "8080",
            "METRICS_ENABLED": "false"
        }):
            service = MonitoringService()
            assert service.metrics_port == 8080
            assert service.metrics_enabled is False

def test_record_check(monitoring_service):
    """Test recording health check execution."""
    # Record successful check
    monitoring_service.record_check("services", 1.5)
    metrics = monitoring_service.get_check_metrics("services")
    assert metrics["total_checks_services"] == 1
    assert metrics["duration_services"] == 1.5
    assert "errors_services" not in metrics
    
    # Record check with error
    monitoring_service.record_check("services", 0.5, "Test error")
    metrics = monitoring_service.get_check_metrics("services")
    assert metrics["total_checks_services"] == 2
    assert metrics["duration_services"] == 0.5
    assert metrics["errors_services_str"] == 1

def test_record_service_health(monitoring_service):
    """Test recording service health status."""
    # Record healthy service
    monitoring_service.record_service_health("api", True)
    metrics = monitoring_service.get_service_metrics("api")
    assert metrics["health_api"] == 1
    
    # Record unhealthy service
    monitoring_service.record_service_health("database", False)
    metrics = monitoring_service.get_service_metrics("database")
    assert metrics["health_database"] == 0

def test_record_service_error(monitoring_service):
    """Test recording service error."""
    monitoring_service.record_service_error("api", "Test error")
    metrics = monitoring_service.get_service_metrics("api")
    assert metrics["errors_api_str"] == 1
    
    # Record another error
    monitoring_service.record_service_error("api", "Another error")
    metrics = monitoring_service.get_service_metrics("api")
    assert metrics["errors_api_str"] == 2

def test_get_check_metrics(monitoring_service):
    """Test getting health check metrics."""
    # Record some checks
    monitoring_service.record_check("services", 1.0)
    monitoring_service.record_check("metrics", 0.5)
    monitoring_service.record_check("services", 1.5, "Error")
    
    # Get all check metrics
    metrics = monitoring_service.get_check_metrics()
    assert metrics["total_checks_services"] == 2
    assert metrics["total_checks_metrics"] == 1
    assert metrics["errors_services_str"] == 1
    
    # Get filtered metrics
    metrics = monitoring_service.get_check_metrics("services")
    assert metrics["total_checks_services"] == 2
    assert "total_checks_metrics" not in metrics

def test_get_service_metrics(monitoring_service):
    """Test getting service metrics."""
    # Record some service states
    monitoring_service.record_service_health("api", True)
    monitoring_service.record_service_health("database", False)
    monitoring_service.record_service_error("api", "Error")
    
    # Get all service metrics
    metrics = monitoring_service.get_service_metrics()
    assert metrics["health_api"] == 1
    assert metrics["health_database"] == 0
    assert metrics["errors_api_str"] == 1
    
    # Get filtered metrics
    metrics = monitoring_service.get_service_metrics("api")
    assert metrics["health_api"] == 1
    assert "health_database" not in metrics

def test_get_all_metrics(monitoring_service):
    """Test getting all metrics."""
    # Record some data
    monitoring_service.record_check("services", 1.0)
    monitoring_service.record_service_health("api", True)
    monitoring_service.record_service_error("api", "Error")
    
    metrics = monitoring_service.get_all_metrics()
    assert "checks" in metrics
    assert "services" in metrics
    assert metrics["checks"]["total_checks_services"] == 1
    assert metrics["services"]["health_api"] == 1
    assert metrics["services"]["errors_api_str"] == 1

def test_reset_metrics(monitoring_service):
    """Test resetting metrics."""
    # Record some data
    monitoring_service.record_check("services", 1.0)
    monitoring_service.record_service_health("api", True)
    monitoring_service.record_service_error("api", "Error")
    
    # Reset metrics
    monitoring_service.reset_metrics()
    
    # Verify metrics are reset
    metrics = monitoring_service.get_all_metrics()
    assert not metrics["checks"]
    assert not metrics["services"]

def test_export_metrics(monitoring_service):
    """Test exporting metrics."""
    # Record some data
    monitoring_service.record_check("services", 1.0)
    monitoring_service.record_service_health("api", True)
    
    # Test JSON export
    json_metrics = monitoring_service.export_metrics("json")
    data = json.loads(json_metrics)
    assert "checks" in data
    assert "services" in data
    
    # Test Prometheus export
    with patch("prometheus_client.exposition.generate_latest") as mock_generate:
        mock_generate.return_value = b"metric_name{label=\"value\"} 1.0\n"
        prom_metrics = monitoring_service.export_metrics("prometheus")
        assert "metric_name" in prom_metrics
        mock_generate.assert_called_once()
    
    # Test invalid format
    with pytest.raises(ValueError):
        monitoring_service.export_metrics("invalid")

def test_service_lifecycle(monitoring_service):
    """Test service lifecycle."""
    with patch("prometheus_client.start_http_server") as mock_start:
        # Test start
        monitoring_service.metrics_enabled = False
        monitoring_service.start()
        assert monitoring_service.metrics_enabled is True
        mock_start.assert_called_once_with(monitoring_service.metrics_port)
        
        # Test stop
        monitoring_service.stop()
        assert monitoring_service.metrics_enabled is False 