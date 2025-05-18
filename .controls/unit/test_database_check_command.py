"""Unit tests for database health check command."""

import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from ..commands.health.checks.database import DatabaseCheck
from ..mocks.registry import MockServiceRegistry

@pytest.fixture
def mock_registry():
    """Create mock service registry."""
    registry = MagicMock(spec=MockServiceRegistry)
    registry.list_services.return_value = ["api", "database", "cache"]
    return registry

@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    db_service = MagicMock()
    
    # Connection
    db_service.is_connected.return_value = True
    db_service.get_connection_info.return_value = {
        "host": "localhost",
        "port": 5432,
        "database": "test_db"
    }
    
    # Queries
    db_service.execute_test_query.return_value = {"rows": 1}
    db_service.get_query_stats.return_value = {
        "executed": 100,
        "failed": 0,
        "avg_time_ms": 50
    }
    
    # Connection Pool
    db_service.get_pool_stats.return_value = {
        "total": 10,
        "active": 5,
        "idle": 5
    }
    db_service.get_pool_config.return_value = {
        "min_connections": 1,
        "max_connections": 20,
        "idle_timeout": 300
    }
    
    # Transactions
    db_service.test_transaction.return_value = {"success": True}
    db_service.get_transaction_stats.return_value = {
        "committed": 50,
        "rolled_back": 2,
        "active": 3
    }
    
    # Performance
    db_service.get_performance_metrics.return_value = {
        "cpu_usage": 45.0,
        "memory_usage": 60.0,
        "disk_usage": 55.0
    }
    db_service.get_performance_thresholds.return_value = {
        "cpu_usage": 80.0,
        "memory_usage": 80.0,
        "disk_usage": 80.0
    }
    
    return db_service

@pytest.fixture
def database_check(mock_registry):
    """Create database check instance."""
    return DatabaseCheck(mock_registry)

def test_database_check_initialization(database_check):
    """Test database check initialization."""
    assert database_check.name == "database"
    assert database_check.description == "Check database connection and status"
    assert isinstance(database_check.registry, MagicMock)

def test_database_check_validation(database_check):
    """Test database check validation."""
    assert database_check.validate() is None
    assert database_check.validate(services=["database"]) is None
    assert database_check.validate(services="database") == "Services must be a list"

def test_database_check_execution(database_check, mock_registry, mock_db_service):
    """Test database check execution."""
    mock_registry.get_service.return_value = mock_db_service
    
    result = database_check.execute()
    
    assert result["status"] == "healthy"
    assert "timestamp" in result
    assert result["details"]["connection"]["healthy"] is True
    assert result["details"]["queries"]["healthy"] is True
    assert result["details"]["pool"]["healthy"] is True
    assert result["details"]["transactions"]["healthy"] is True
    assert result["details"]["performance"]["healthy"] is True

def test_database_check_no_service(database_check, mock_registry):
    """Test database check without database service."""
    mock_registry.get_service.return_value = None
    
    result = database_check.execute()
    assert result["status"] == "error"
    assert "Database service not available" in result["error"]

def test_database_check_not_connected(database_check, mock_registry, mock_db_service):
    """Test database check with database not connected."""
    mock_db_service.is_connected.return_value = False
    mock_registry.get_service.return_value = mock_db_service
    
    result = database_check.execute()
    assert result["status"] == "unhealthy"
    assert result["details"]["connection"]["healthy"] is False
    assert result["details"]["connection"]["status"] == "disconnected"

def test_database_check_query_error(database_check, mock_registry, mock_db_service):
    """Test database check with query error."""
    mock_db_service.execute_test_query.side_effect = Exception("Query failed")
    mock_registry.get_service.return_value = mock_db_service
    
    result = database_check.execute()
    assert result["status"] == "unhealthy"
    assert result["details"]["queries"]["healthy"] is False
    assert "Query failed" in result["details"]["queries"]["execution"]["error"]

def test_database_check_pool_full(database_check, mock_registry, mock_db_service):
    """Test database check with connection pool full."""
    mock_db_service.get_pool_stats.return_value = {
        "total": 20,
        "active": 20,
        "idle": 0
    }
    mock_registry.get_service.return_value = mock_db_service
    
    result = database_check.execute()
    assert result["status"] == "unhealthy"
    assert result["details"]["pool"]["healthy"] is False

def test_database_check_transaction_error(database_check, mock_registry, mock_db_service):
    """Test database check with transaction error."""
    mock_db_service.test_transaction.side_effect = Exception("Transaction failed")
    mock_registry.get_service.return_value = mock_db_service
    
    result = database_check.execute()
    assert result["status"] == "unhealthy"
    assert result["details"]["transactions"]["healthy"] is False
    assert "Transaction failed" in result["details"]["transactions"]["execution"]["error"]

def test_database_check_performance_issues(database_check, mock_registry, mock_db_service):
    """Test database check with performance issues."""
    mock_db_service.get_performance_metrics.return_value = {
        "cpu_usage": 90.0,
        "memory_usage": 85.0,
        "disk_usage": 75.0
    }
    mock_registry.get_service.return_value = mock_db_service
    
    result = database_check.execute()
    assert result["status"] == "unhealthy"
    assert result["details"]["performance"]["healthy"] is False
    assert len(result["details"]["performance"]["issues"]) == 2  # CPU and memory exceed thresholds 