"""Unit tests for database health checks."""

import pytest
from typing import Dict, Any
from ..commands.health.checks.database import (
    DatabaseHealthCheck,
    DatabaseConnectionCheck,
    DatabaseQueryCheck,
    DatabaseConnectionPoolCheck,
    DatabaseDeadlockCheck,
    DatabaseReplicationCheck,
    DatabaseBackupCheck
)

@pytest.fixture
def db_config() -> Dict[str, Any]:
    """Database configuration fixture."""
    return {
        "name": "test_db",
        "connection_string": "postgresql://user:pass@localhost:5432/test_db",
        "required": True,
        "timeout_ms": 1000
    }

@pytest.mark.asyncio
async def test_connection_check(db_config):
    """Test database connection check."""
    check = DatabaseConnectionCheck(
        name="test_connection",
        database_name=db_config["name"],
        connection_string=db_config["connection_string"],
        required=db_config["required"],
        timeout_ms=db_config["timeout_ms"]
    )
    
    result = await check._check_database()
    
    assert result.status == "healthy"
    assert result.details["database"] == db_config["name"]
    assert result.details["connected"] is True
    assert "connection_time_ms" in result.metrics

@pytest.mark.asyncio
async def test_query_check(db_config):
    """Test database query check."""
    check = DatabaseQueryCheck(
        name="test_query",
        database_name=db_config["name"],
        connection_string=db_config["connection_string"],
        query="SELECT 1",
        warning_threshold_ms=100,
        error_threshold_ms=1000,
        required=db_config["required"],
        timeout_ms=db_config["timeout_ms"]
    )
    
    result = await check._check_database()
    
    assert result.status in ["healthy", "warning"]
    assert result.details["database"] == db_config["name"]
    assert result.details["query"] == "SELECT 1"
    assert "query_time_ms" in result.metrics

@pytest.mark.asyncio
async def test_connection_pool_check(db_config):
    """Test database connection pool check."""
    check = DatabaseConnectionPoolCheck(
        name="test_pool",
        database_name=db_config["name"],
        connection_string=db_config["connection_string"],
        min_connections=1,
        max_connections=10,
        warning_threshold=0.8,
        error_threshold=0.95,
        required=db_config["required"],
        timeout_ms=db_config["timeout_ms"]
    )
    
    result = await check._check_database()
    
    assert result.status in ["healthy", "warning", "unhealthy"]
    assert result.details["database"] == db_config["name"]
    assert "total_connections" in result.metrics
    assert "active_connections" in result.metrics
    assert "idle_connections" in result.metrics
    assert "pool_usage" in result.metrics

@pytest.mark.asyncio
async def test_deadlock_check(db_config):
    """Test database deadlock check."""
    check = DatabaseDeadlockCheck(
        name="test_deadlock",
        database_name=db_config["name"],
        connection_string=db_config["connection_string"],
        warning_threshold=5,
        error_threshold=10,
        check_period_seconds=300,
        required=db_config["required"],
        timeout_ms=db_config["timeout_ms"]
    )
    
    result = await check._check_database()
    
    assert result.status in ["healthy", "warning", "unhealthy"]
    assert result.details["database"] == db_config["name"]
    assert "deadlock_count" in result.metrics
    assert "deadlock_wait_time_ms" in result.metrics

@pytest.mark.asyncio
async def test_replication_check(db_config):
    """Test database replication check."""
    check = DatabaseReplicationCheck(
        name="test_replication",
        database_name=db_config["name"],
        connection_string=db_config["connection_string"],
        warning_lag_seconds=60,
        error_lag_seconds=300,
        required=db_config["required"],
        timeout_ms=db_config["timeout_ms"]
    )
    
    result = await check._check_database()
    
    assert result.status in ["healthy", "warning", "unhealthy"]
    assert result.details["database"] == db_config["name"]
    assert "replication_status" in result.details
    assert "replication_lag_seconds" in result.metrics

@pytest.mark.asyncio
async def test_backup_check(db_config):
    """Test database backup check."""
    check = DatabaseBackupCheck(
        name="test_backup",
        database_name=db_config["name"],
        connection_string=db_config["connection_string"],
        warning_age_hours=24,
        error_age_hours=48,
        required=db_config["required"],
        timeout_ms=db_config["timeout_ms"]
    )
    
    result = await check._check_database()
    
    assert result.status in ["healthy", "warning", "unhealthy"]
    assert result.details["database"] == db_config["name"]
    assert "backup_status" in result.details
    assert "last_backup_age_hours" in result.metrics
    assert "backup_size_bytes" in result.metrics

@pytest.mark.asyncio
async def test_required_vs_optional():
    """Test required vs optional database checks."""
    # Test with required=True
    required_check = DatabaseConnectionCheck(
        name="required_test",
        database_name="test_db",
        connection_string="invalid_connection_string",
        required=True
    )
    
    required_result = await required_check._check_database()
    assert required_result.status == "unhealthy"
    
    # Test with required=False
    optional_check = DatabaseConnectionCheck(
        name="optional_test",
        database_name="test_db",
        connection_string="invalid_connection_string",
        required=False
    )
    
    optional_result = await optional_check._check_database()
    assert optional_result.status == "warning"

@pytest.mark.asyncio
async def test_threshold_handling():
    """Test threshold handling in checks."""
    check = DatabaseQueryCheck(
        name="threshold_test",
        database_name="test_db",
        connection_string="test_connection",
        query="SELECT 1",
        warning_threshold_ms=100,
        error_threshold_ms=200
    )
    
    # Mock different query times and verify status
    # Note: In real implementation, we'd use dependency injection or mocking
    # to control the query time. Here we're relying on the mock implementation.
    result = await check._check_database()
    
    assert result.status in ["healthy", "warning", "unhealthy"]
    if result.metrics["query_time_ms"] >= 200:
        assert result.status == "unhealthy"
    elif result.metrics["query_time_ms"] >= 100:
        assert result.status == "warning"
    else:
        assert result.status == "healthy"

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in checks."""
    # Create a check with invalid connection string to trigger errors
    check = DatabaseConnectionCheck(
        name="error_test",
        database_name="test_db",
        connection_string="invalid://connection:string"
    )
    
    result = await check._check_database()
    
    assert result.status == "unhealthy"
    assert result.error is not None
    assert result.details["connected"] is False 