"""Unit tests for service registry setup command."""

import os
import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

from ..commands.init.registry import ServiceRegistryCommand
from ..mocks.registry import MockServiceRegistry

@pytest.fixture
def mock_registry():
    """Create mock service registry."""
    registry = MagicMock(spec=MockServiceRegistry)
    registry.list_services.return_value = ["api", "database", "cache"]
    return registry

@pytest.fixture
def mock_registry_service():
    """Create mock registry service."""
    registry_service = MagicMock()
    
    # Configuration
    registry_service.apply_config.return_value = {"status": "success"}
    registry_service.apply_default_config.return_value = {"status": "success"}
    registry_service.get_config.return_value = {
        "max_services": 100,
        "discovery_interval": 300
    }
    registry_service.reset_config.return_value = {"status": "success"}
    
    # Initialization
    registry_service.initialize.return_value = {"status": "success"}
    
    # Service discovery
    registry_service.discover_services.return_value = [
        "api",
        "database",
        "cache"
    ]
    
    # Service registration
    registry_service.register_service.return_value = {
        "status": "success",
        "registered": True
    }
    registry_service.unregister_service.return_value = {
        "status": "success",
        "unregistered": True
    }
    
    # Health checks
    registry_service.configure_health_check.return_value = {
        "status": "success",
        "configured": True
    }
    
    # Dependencies
    registry_service.resolve_dependencies.return_value = {
        "status": "success",
        "resolved": True
    }
    
    # Service operations
    registry_service.stop.return_value = {"status": "success"}
    
    return registry_service

@pytest.fixture
def registry_command(mock_registry):
    """Create service registry command instance."""
    return ServiceRegistryCommand(mock_registry)

def test_registry_command_initialization(registry_command):
    """Test service registry command initialization."""
    assert registry_command.name == "init-registry"
    assert registry_command.description == "Initialize service registry and configuration"
    assert isinstance(registry_command.registry, MagicMock)

def test_registry_command_validation(registry_command):
    """Test service registry command validation."""
    assert registry_command.validate() is None
    assert registry_command.validate(config="config.json") is None
    assert registry_command.validate(config=123) == "Config file must be a string"

def test_registry_command_execution(registry_command, mock_registry, mock_registry_service):
    """Test service registry command execution."""
    mock_registry.get_service.return_value = mock_registry_service
    
    with patch("builtins.open", mock_open(read_data="test config")):
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = registry_command.execute(config="config.json")
    
    assert result["status"] == "success"
    assert result["setup"]["status"] == "success"
    assert result["services"]["status"] == "success"
    assert result["health_checks"]["status"] == "success"
    assert result["dependencies"]["status"] == "success"

def test_registry_command_no_service(registry_command, mock_registry):
    """Test service registry command without registry service."""
    mock_registry.get_service.return_value = None
    
    result = registry_command.execute()
    assert result["status"] == "error"
    assert "Service registry service not available" in result["error"]

def test_registry_command_setup_error(registry_command, mock_registry, mock_registry_service):
    """Test service registry command with setup error."""
    mock_registry_service.apply_config.side_effect = Exception("Setup error")
    mock_registry.get_service.return_value = mock_registry_service
    
    with patch("builtins.open", mock_open(read_data="test config")):
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = registry_command.execute(config="config.json")
    
    assert result["status"] == "error"
    assert result["setup"]["status"] == "error"
    assert "Setup error" in result["setup"]["error"]

def test_registry_command_service_registration_error(registry_command, mock_registry, mock_registry_service):
    """Test service registry command with registration error."""
    mock_registry_service.register_service.side_effect = Exception("Registration error")
    mock_registry.get_service.return_value = mock_registry_service
    
    result = registry_command.execute()
    assert result["status"] == "error"
    assert result["services"]["status"] == "error"
    assert any(
        "Registration error" in service["error"]
        for service in result["services"]["services"]
    )

def test_registry_command_health_check_error(registry_command, mock_registry, mock_registry_service):
    """Test service registry command with health check error."""
    mock_registry_service.configure_health_check.side_effect = Exception("Health check error")
    mock_registry.get_service.return_value = mock_registry_service
    
    result = registry_command.execute()
    assert result["status"] == "error"
    assert result["health_checks"]["status"] == "error"
    assert any(
        "Health check error" in check["error"]
        for check in result["health_checks"]["health_checks"]
    )

def test_registry_command_dependency_error(registry_command, mock_registry, mock_registry_service):
    """Test service registry command with dependency error."""
    mock_registry_service.resolve_dependencies.side_effect = Exception("Dependency error")
    mock_registry.get_service.return_value = mock_registry_service
    
    result = registry_command.execute()
    assert result["status"] == "error"
    assert result["dependencies"]["status"] == "error"
    assert any(
        "Dependency error" in dep["error"]
        for dep in result["dependencies"]["dependencies"]
    )

def test_registry_command_file_not_found(registry_command, mock_registry, mock_registry_service):
    """Test service registry command with missing file."""
    mock_registry.get_service.return_value = mock_registry_service
    
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False
        result = registry_command.execute(config="missing.json")
    
    assert result["status"] == "error"
    assert result["setup"]["status"] == "error"
    assert "File not found" in result["setup"]["error"]

def test_registry_command_file_read_error(registry_command, mock_registry, mock_registry_service):
    """Test service registry command with file read error."""
    mock_registry.get_service.return_value = mock_registry_service
    
    with patch("builtins.open") as mock_open:
        mock_open.side_effect = IOError("Read error")
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = registry_command.execute(config="config.json")
    
    assert result["status"] == "error"
    assert result["setup"]["status"] == "error"
    assert "Failed to read file" in result["setup"]["error"]

def test_registry_command_reset(registry_command, mock_registry, mock_registry_service):
    """Test service registry command reset."""
    mock_registry.get_service.return_value = mock_registry_service
    
    result = registry_command.reset(mock_registry_service)
    assert result["status"] == "success"
    assert "unregistered" in result
    assert all(
        service["status"] == "success"
        for service in result["unregistered"]
    )

def test_registry_command_reset_error(registry_command, mock_registry, mock_registry_service):
    """Test service registry command reset with error."""
    mock_registry_service.unregister_service.side_effect = Exception("Reset error")
    mock_registry.get_service.return_value = mock_registry_service
    
    result = registry_command.reset(mock_registry_service)
    assert result["status"] == "error"
    assert any(
        "Reset error" in service["error"]
        for service in result["unregistered"]
    ) 