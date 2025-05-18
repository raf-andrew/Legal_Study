"""Unit tests for logs health check."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ..commands.health.checks.logs import LogsCheck
from ...mocks.registry import MockServiceRegistry

@pytest.fixture
def mock_registry() -> MagicMock:
    """Create mock service registry."""
    registry = MagicMock(spec=MockServiceRegistry)
    registry.list_services.return_value = ["api", "database", "cache"]
    return registry

@pytest.fixture
def logs_check(mock_registry) -> LogsCheck:
    """Create logs check instance."""
    return LogsCheck(mock_registry)

@pytest.fixture
def sample_log_records() -> List[Dict[str, Any]]:
    """Create sample log records."""
    now = datetime.now()
    return [
        {
            "timestamp": now.isoformat(),
            "level": "INFO",
            "message": "Test message 1"
        },
        {
            "timestamp": (now - timedelta(minutes=1)).isoformat(),
            "level": "WARNING",
            "message": "Test message 2"
        },
        {
            "timestamp": (now - timedelta(minutes=2)).isoformat(),
            "level": "ERROR",
            "message": "Test message 3"
        }
    ]

def test_logs_check_initialization(logs_check):
    """Test logs check initialization."""
    assert logs_check.name == "logs"
    assert isinstance(logs_check.registry, MagicMock)

def test_logs_check_all_healthy(logs_check, mock_registry, sample_log_records):
    """Test logs check with all handlers healthy."""
    # Mock logging service
    logging_service = MagicMock()
    logging_service.list_handlers.return_value = ["console", "file"]
    logging_service.get_records.return_value = sample_log_records
    
    # Mock regular service
    service = MagicMock()
    service.get_logs.return_value = sample_log_records
    
    def get_service(name):
        return logging_service if name == "logging" else service
    
    mock_registry.get_service.side_effect = get_service
    
    result = logs_check.execute()
    assert result["status"] == "healthy"
    assert result["details"]["healthy"] is True
    assert len(result["details"]["handlers"]) == 2
    assert len(result["details"]["stale_handlers"]) == 0
    assert len(result["details"]["inactive_handlers"]) == 0

def test_logs_check_with_stale_handler(logs_check, mock_registry):
    """Test logs check with stale handler."""
    # Mock logging service
    logging_service = MagicMock()
    logging_service.list_handlers.return_value = ["console", "file"]
    
    stale_time = datetime.now() - timedelta(minutes=10)
    logging_service.get_records.return_value = [{
        "timestamp": stale_time.isoformat(),
        "level": "INFO",
        "message": "Old message"
    }]
    
    mock_registry.get_service.return_value = logging_service
    
    result = logs_check.execute()
    assert result["status"] == "unhealthy"
    assert result["details"]["healthy"] is False
    assert len(result["details"]["stale_handlers"]) > 0

def test_logs_check_with_inactive_handler(logs_check, mock_registry):
    """Test logs check with inactive handler."""
    # Mock logging service
    logging_service = MagicMock()
    logging_service.list_handlers.return_value = ["console", "file"]
    logging_service.get_records.side_effect = Exception("Handler error")
    
    mock_registry.get_service.return_value = logging_service
    
    result = logs_check.execute()
    assert result["status"] == "unhealthy"
    assert result["details"]["healthy"] is False
    assert len(result["details"]["inactive_handlers"]) > 0

def test_logs_check_no_logging_service(logs_check, mock_registry):
    """Test logs check without logging service."""
    mock_registry.get_service.return_value = None
    
    result = logs_check.execute()
    assert result["status"] == "error"
    assert "Logging service not available" in result["error"]

def test_get_handler_stats(logs_check, mock_registry, sample_log_records):
    """Test getting handler statistics."""
    # Mock logging service
    logging_service = MagicMock()
    logging_service.get_records.return_value = sample_log_records
    mock_registry.get_service.return_value = logging_service
    
    result = logs_check.get_handler_stats("console")
    assert result["total_records"] == 3
    assert result["last_record"] == sample_log_records[-1]
    assert result["levels"] == {
        "INFO": 1,
        "WARNING": 1,
        "ERROR": 1
    }

def test_get_service_logs(logs_check, mock_registry, sample_log_records):
    """Test getting service logs."""
    # Mock service
    service = MagicMock()
    service.get_logs.return_value = sample_log_records
    mock_registry.get_service.return_value = service
    
    result = logs_check.get_service_logs("api")
    assert result == sample_log_records

def test_get_logs_by_level(logs_check, mock_registry, sample_log_records):
    """Test getting logs by level."""
    # Mock logging service
    logging_service = MagicMock()
    logging_service.get_logs_by_level.return_value = [
        record for record in sample_log_records
        if record["level"] == "ERROR"
    ]
    mock_registry.get_service.return_value = logging_service
    
    result = logs_check.get_logs_by_level("ERROR")
    assert len(result) == 1
    assert result[0]["level"] == "ERROR"

def test_count_log_levels(logs_check, sample_log_records):
    """Test counting log levels."""
    counts = logs_check._count_log_levels(sample_log_records)
    assert counts == {
        "INFO": 1,
        "WARNING": 1,
        "ERROR": 1
    } 