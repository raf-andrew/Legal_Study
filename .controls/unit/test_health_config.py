"""Unit tests for health check configuration."""

import json
import pytest
from pathlib import Path
from typing import Dict, Set

from ..commands.health.config import (
    HealthCheckConfig,
    HealthCheckConfiguration,
    HealthCheckConfigurationError
)

@pytest.fixture
def config_path(tmp_path) -> Path:
    """Create temporary config path."""
    return tmp_path / "health_config.json"

@pytest.fixture
def test_config() -> Dict[str, Dict]:
    """Create test configuration data."""
    return {
        "check1": {
            "enabled": True,
            "timeout_ms": 1000,
            "interval_ms": 5000,
            "retries": 3,
            "retry_delay_ms": 500,
            "dependencies": ["dep1", "dep2"],
            "parameters": {"url": "http://test.com"}
        },
        "check2": {
            "enabled": False,
            "timeout_ms": 2000,
            "dependencies": ["dep3"],
            "parameters": {"threshold": 0.9}
        }
    }

@pytest.fixture
def config_file(config_path, test_config) -> Path:
    """Create test configuration file."""
    with open(config_path, "w") as f:
        json.dump(test_config, f)
    return config_path

@pytest.fixture
def configuration(config_path) -> HealthCheckConfiguration:
    """Create configuration handler."""
    return HealthCheckConfiguration(config_path)

def test_config_initialization():
    """Test configuration initialization."""
    config = HealthCheckConfig()
    assert config.enabled
    assert config.timeout_ms == 5000
    assert config.interval_ms is None
    assert config.retries == 0
    assert config.retry_delay_ms == 1000
    assert not config.dependencies
    assert not config.parameters

def test_configuration_initialization(configuration):
    """Test configuration handler initialization."""
    assert isinstance(configuration.config_path, Path)
    assert isinstance(configuration._configs, dict)
    assert isinstance(configuration.logger, logging.Logger)

def test_load_config(configuration, config_file, test_config):
    """Test loading configuration from file."""
    configuration.load_config()
    
    # Check loaded configurations
    assert len(configuration._configs) == 2
    
    # Check check1 config
    check1_config = configuration.get_config("check1")
    assert check1_config.enabled
    assert check1_config.timeout_ms == 1000
    assert check1_config.interval_ms == 5000
    assert check1_config.retries == 3
    assert check1_config.retry_delay_ms == 500
    assert check1_config.dependencies == {"dep1", "dep2"}
    assert check1_config.parameters == {"url": "http://test.com"}
    
    # Check check2 config
    check2_config = configuration.get_config("check2")
    assert not check2_config.enabled
    assert check2_config.timeout_ms == 2000
    assert check2_config.interval_ms is None
    assert check2_config.retries == 0
    assert check2_config.retry_delay_ms == 1000
    assert check2_config.dependencies == {"dep3"}
    assert check2_config.parameters == {"threshold": 0.9}

def test_load_invalid_config(configuration, config_path):
    """Test loading invalid configuration."""
    # Create invalid JSON file
    with open(config_path, "w") as f:
        f.write("invalid json")
    
    with pytest.raises(HealthCheckConfigurationError) as exc:
        configuration.load_config()
    assert "Failed to load configuration" in str(exc.value)

def test_save_config(configuration, test_config):
    """Test saving configuration to file."""
    # Set configurations
    for name, config_data in test_config.items():
        config = HealthCheckConfig(
            enabled=config_data["enabled"],
            timeout_ms=config_data["timeout_ms"],
            interval_ms=config_data.get("interval_ms"),
            retries=config_data.get("retries", 0),
            retry_delay_ms=config_data.get("retry_delay_ms", 1000),
            dependencies=set(config_data.get("dependencies", [])),
            parameters=config_data.get("parameters", {})
        )
        configuration.set_config(name, config)
    
    # Save configuration
    configuration.save_config()
    
    # Load saved configuration
    with open(configuration.config_path) as f:
        saved_config = json.load(f)
    
    # Verify saved data
    assert len(saved_config) == 2
    assert saved_config["check1"]["enabled"]
    assert saved_config["check1"]["timeout_ms"] == 1000
    assert saved_config["check1"]["interval_ms"] == 5000
    assert saved_config["check1"]["dependencies"] == ["dep1", "dep2"]
    assert not saved_config["check2"]["enabled"]
    assert saved_config["check2"]["timeout_ms"] == 2000

def test_get_config(configuration, test_config):
    """Test getting check configuration."""
    # Get non-existent config (should return default)
    config = configuration.get_config("non_existent")
    assert isinstance(config, HealthCheckConfig)
    assert config.enabled
    assert config.timeout_ms == 5000
    
    # Set and get config
    configuration.set_config(
        "test",
        HealthCheckConfig(
            enabled=False,
            timeout_ms=1000
        )
    )
    config = configuration.get_config("test")
    assert not config.enabled
    assert config.timeout_ms == 1000

def test_enable_disable_check(configuration):
    """Test enabling and disabling checks."""
    # Enable check
    configuration.enable_check("test")
    assert configuration.get_config("test").enabled
    
    # Disable check
    configuration.disable_check("test")
    assert not configuration.get_config("test").enabled

def test_set_check_interval(configuration):
    """Test setting check interval."""
    configuration.set_check_interval("test", 1000)
    assert configuration.get_config("test").interval_ms == 1000
    
    configuration.set_check_interval("test", None)
    assert configuration.get_config("test").interval_ms is None

def test_set_check_timeout(configuration):
    """Test setting check timeout."""
    configuration.set_check_timeout("test", 2000)
    assert configuration.get_config("test").timeout_ms == 2000

def test_set_check_retries(configuration):
    """Test setting check retries."""
    # Set retries only
    configuration.set_check_retries("test", 3)
    config = configuration.get_config("test")
    assert config.retries == 3
    assert config.retry_delay_ms == 1000
    
    # Set retries and delay
    configuration.set_check_retries("test", 5, 2000)
    config = configuration.get_config("test")
    assert config.retries == 5
    assert config.retry_delay_ms == 2000

def test_set_check_dependencies(configuration):
    """Test setting check dependencies."""
    configuration.set_check_dependencies("test", {"dep1", "dep2"})
    assert configuration.get_config("test").dependencies == {"dep1", "dep2"}

def test_set_check_parameters(configuration):
    """Test setting check parameters."""
    configuration.set_check_parameters("test", {"key": "value"})
    assert configuration.get_config("test").parameters == {"key": "value"}

def test_list_enabled_checks(configuration, test_config):
    """Test listing enabled checks."""
    # Set configurations
    for name, config_data in test_config.items():
        config = HealthCheckConfig(
            enabled=config_data["enabled"],
            timeout_ms=config_data["timeout_ms"]
        )
        configuration.set_config(name, config)
    
    enabled_checks = configuration.list_enabled_checks()
    assert len(enabled_checks) == 1
    assert "check1" in enabled_checks
    assert "check2" not in enabled_checks

def test_list_scheduled_checks(configuration, test_config):
    """Test listing scheduled checks."""
    # Set configurations
    for name, config_data in test_config.items():
        config = HealthCheckConfig(
            enabled=config_data["enabled"],
            timeout_ms=config_data["timeout_ms"],
            interval_ms=config_data.get("interval_ms")
        )
        configuration.set_config(name, config)
    
    scheduled_checks = configuration.list_scheduled_checks()
    assert len(scheduled_checks) == 1
    assert "check1" in scheduled_checks
    assert "check2" not in scheduled_checks 