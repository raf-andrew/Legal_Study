"""Unit tests for service configuration checks."""

import pytest
from pathlib import Path
from typing import Any, Dict, Optional, Set

from ..commands.health.checks.service_config import (
    ServiceConfigCheck,
    ServiceConfigValueCheck
)
from ..commands.health.base import HealthCheckResult

@pytest.fixture
def config_path(tmp_path) -> Path:
    """Create temporary config path."""
    return tmp_path / "test_config.json"

@pytest.fixture
def required_settings() -> Set[str]:
    """Create required settings set."""
    return {"host", "port", "timeout"}

@pytest.fixture
def optional_settings() -> Set[str]:
    """Create optional settings set."""
    return {"debug", "log_level"}

@pytest.fixture
def value_validators() -> Dict[str, callable]:
    """Create value validators."""
    return {
        "port": lambda x: isinstance(x, int) and 1024 <= x <= 65535,
        "timeout": lambda x: isinstance(x, int) and x > 0,
        "log_level": lambda x: x in ["DEBUG", "INFO", "WARNING", "ERROR"]
    }

@pytest.fixture
def config_check(
    config_path,
    required_settings,
    optional_settings,
    value_validators
) -> ServiceConfigCheck:
    """Create service configuration check."""
    return ServiceConfigCheck(
        "test_config",
        "test_service",
        config_path,
        required_settings,
        optional_settings,
        value_validators
    )

@pytest.fixture
def value_checks() -> Dict[str, Dict[str, Any]]:
    """Create value checks."""
    return {
        "port": {
            "type": int,
            "min": 1024,
            "max": 65535
        },
        "timeout": {
            "type": int,
            "min": 0,
            "max": 3600
        },
        "log_level": {
            "type": str,
            "allowed": ["DEBUG", "INFO", "WARNING", "ERROR"]
        },
        "host": {
            "type": str,
            "min_length": 3,
            "max_length": 255
        }
    }

@pytest.fixture
def value_check(config_path, value_checks) -> ServiceConfigValueCheck:
    """Create service configuration value check."""
    return ServiceConfigValueCheck(
        "test_config_values",
        "test_service",
        config_path,
        value_checks
    )

@pytest.mark.asyncio
async def test_config_check_missing_file(config_check):
    """Test configuration check with missing file."""
    result = await config_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert "not found" in result.error
    assert result.details["config_path"] == str(config_check.config_path)

@pytest.mark.asyncio
async def test_config_check_all_valid(config_check):
    """Test configuration check with all valid settings."""
    result = await config_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "healthy"
    assert not result.error
    assert not result.warnings
    assert result.details["missing_settings"] == []
    assert result.details["invalid_settings"] == []
    assert result.metrics["total_settings"] > 0
    assert result.metrics["missing_settings"] == 0
    assert result.metrics["invalid_settings"] == 0

@pytest.mark.asyncio
async def test_config_check_missing_required(config_check, monkeypatch):
    """Test configuration check with missing required settings."""
    # Mock config loading to return incomplete config
    monkeypatch.setattr(
        config_check,
        "_load_config",
        lambda: {"host": "localhost", "debug": False}
    )
    
    result = await config_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert "Missing required settings" in result.error
    assert "port" in result.details["missing_settings"]
    assert "timeout" in result.details["missing_settings"]
    assert result.metrics["missing_settings"] == 2

@pytest.mark.asyncio
async def test_config_check_invalid_values(config_check, monkeypatch):
    """Test configuration check with invalid values."""
    # Mock config loading to return invalid values
    monkeypatch.setattr(
        config_check,
        "_load_config",
        lambda: {
            "host": "localhost",
            "port": "invalid",  # Should be int
            "timeout": -1,      # Should be positive
            "log_level": "INVALID"  # Not in allowed values
        }
    )
    
    result = await config_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert "Invalid required settings" in result.error
    assert "port" in result.details["invalid_settings"]
    assert "timeout" in result.details["invalid_settings"]
    assert result.metrics["invalid_settings"] == 2

@pytest.mark.asyncio
async def test_config_check_unknown_settings(config_check, monkeypatch):
    """Test configuration check with unknown settings."""
    # Mock config loading to return unknown settings
    monkeypatch.setattr(
        config_check,
        "_load_config",
        lambda: {
            "host": "localhost",
            "port": 8080,
            "timeout": 30,
            "unknown_setting": "value"
        }
    )
    
    result = await config_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "healthy"
    assert "Unknown settings found" in result.warnings[0]
    assert "unknown_setting" in result.details["unknown_settings"]

@pytest.mark.asyncio
async def test_config_check_optional_invalid(config_check, monkeypatch):
    """Test configuration check with invalid optional settings."""
    # Mock config loading to return invalid optional values
    monkeypatch.setattr(
        config_check,
        "_load_config",
        lambda: {
            "host": "localhost",
            "port": 8080,
            "timeout": 30,
            "log_level": "INVALID"
        }
    )
    
    result = await config_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "warning"
    assert "Invalid value for optional setting" in result.warnings[0]

@pytest.mark.asyncio
async def test_value_check_all_valid(value_check):
    """Test value check with all valid values."""
    result = await value_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "healthy"
    assert not result.error
    assert not result.warnings
    assert result.details["invalid_values"] == []
    assert result.metrics["total_checks"] == len(value_check.value_checks)
    assert result.metrics["invalid_values"] == 0

@pytest.mark.asyncio
async def test_value_check_invalid_types(value_check, monkeypatch):
    """Test value check with invalid types."""
    # Mock config loading to return invalid types
    monkeypatch.setattr(
        value_check,
        "_load_config",
        lambda: {
            "host": "localhost",
            "port": "8080",  # Should be int
            "timeout": "30",  # Should be int
            "log_level": 123  # Should be str
        }
    )
    
    result = await value_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert "Invalid configuration values" in result.error
    assert len(result.details["invalid_values"]) == 3
    assert result.metrics["invalid_values"] == 3

@pytest.mark.asyncio
async def test_value_check_invalid_bounds(value_check, monkeypatch):
    """Test value check with out-of-bounds values."""
    # Mock config loading to return out-of-bounds values
    monkeypatch.setattr(
        value_check,
        "_load_config",
        lambda: {
            "host": "localhost",
            "port": 80,        # Below min
            "timeout": 7200,   # Above max
            "log_level": "INFO"
        }
    )
    
    result = await value_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert "Invalid configuration values" in result.error
    assert len(result.details["invalid_values"]) == 2
    assert result.metrics["invalid_values"] == 2

@pytest.mark.asyncio
async def test_value_check_invalid_allowed(value_check, monkeypatch):
    """Test value check with invalid allowed values."""
    # Mock config loading to return invalid allowed values
    monkeypatch.setattr(
        value_check,
        "_load_config",
        lambda: {
            "host": "localhost",
            "port": 8080,
            "timeout": 30,
            "log_level": "INVALID"  # Not in allowed values
        }
    )
    
    result = await value_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert "Invalid configuration values" in result.error
    assert len(result.details["invalid_values"]) == 1
    assert result.metrics["invalid_values"] == 1

@pytest.mark.asyncio
async def test_value_check_string_length(value_check, monkeypatch):
    """Test value check with invalid string lengths."""
    # Mock config loading to return invalid string lengths
    monkeypatch.setattr(
        value_check,
        "_load_config",
        lambda: {
            "host": "a",  # Too short
            "port": 8080,
            "timeout": 30,
            "log_level": "INFO"
        }
    )
    
    result = await value_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "unhealthy"
    assert "Invalid configuration values" in result.error
    assert len(result.details["invalid_values"]) == 1
    assert result.metrics["invalid_values"] == 1

@pytest.mark.asyncio
async def test_value_check_missing_settings(value_check, monkeypatch):
    """Test value check with missing settings."""
    # Mock config loading to return missing settings
    monkeypatch.setattr(
        value_check,
        "_load_config",
        lambda: {
            "host": "localhost",
            "port": 8080
        }
    )
    
    result = await value_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.status == "warning"
    assert "Setting not found" in result.warnings[0]
    assert len(result.warnings) == 2  # timeout and log_level missing

@pytest.mark.asyncio
async def test_config_sanitization(value_check, monkeypatch):
    """Test configuration sanitization."""
    # Mock config loading to return sensitive values
    monkeypatch.setattr(
        value_check,
        "_load_config",
        lambda: {
            "host": "localhost",
            "port": 8080,
            "api_key": "secret123",
            "password": "sensitive",
            "token": "private"
        }
    )
    
    result = await value_check.check_health()
    
    assert isinstance(result, HealthCheckResult)
    assert result.details["config"]["api_key"] == "***"
    assert result.details["config"]["password"] == "***"
    assert result.details["config"]["token"] == "***"
    assert result.details["config"]["host"] == "localhost"
    assert result.details["config"]["port"] == 8080 