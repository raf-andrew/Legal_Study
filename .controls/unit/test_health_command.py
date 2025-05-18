"""Unit tests for health check command."""
import pytest
import click
import json
import yaml
from typing import Dict, Any
from datetime import datetime
from unittest.mock import MagicMock, patch
from ..commands.health import HealthCheckCommand
from ..commands.registry import CommandRegistry
from ..commands.executor import CommandExecutor

@pytest.fixture
def mock_registry() -> MagicMock:
    """Create mock service registry."""
    registry = MagicMock(spec=MockServiceRegistry)
    registry.list_services.return_value = ["api", "database", "cache"]
    return registry

@pytest.fixture
def health_command() -> HealthCheckCommand:
    """Create a health check command instance."""
    return HealthCheckCommand()

@pytest.fixture
def registry() -> CommandRegistry:
    """Create a command registry instance."""
    return CommandRegistry()

@pytest.fixture
def executor(registry: CommandRegistry) -> CommandExecutor:
    """Create a command executor instance."""
    return CommandExecutor(registry)

def test_health_command_initialization(health_command: HealthCheckCommand):
    """Test health command initialization."""
    assert health_command.name == "health:check"
    assert health_command.description == "Check system health"
    assert health_command.logger.name == "command.health:check"

def test_health_command_execute(health_command: HealthCheckCommand):
    """Test health command execution."""
    with patch.object(health_command.logger, "info") as mock_info:
        result = health_command.execute({})
        assert result == 0
        assert mock_info.call_count == 2
        mock_info.assert_any_call("Running health checks...")
        mock_info.assert_any_call("Health checks completed successfully")

def test_health_command_help(health_command: HealthCheckCommand):
    """Test health command help text."""
    help_text = health_command.get_help()
    assert help_text == "Check system health and report any issues"

def test_health_command_usage(health_command: HealthCheckCommand):
    """Test health command usage text."""
    usage = health_command.get_usage()
    assert usage == "health:check [options]"

def test_health_command_examples(health_command: HealthCheckCommand):
    """Test health command examples."""
    examples = health_command.get_examples()
    assert len(examples) == 3
    assert "health:check" in examples
    assert "health:check --verbose" in examples
    assert "health:check --service api" in examples

def test_health_command_registration(registry: CommandRegistry):
    """Test health command registration."""
    registry.register(HealthCheckCommand)
    command = registry.get_command("health:check")
    assert command is not None
    assert command.__name__ == "HealthCheckCommand"

def test_health_command_execution(executor: CommandExecutor):
    """Test health command execution through executor."""
    executor.registry.register(HealthCheckCommand)
    with patch("logging.Logger.info") as mock_info:
        result = executor.execute("health:check", {})
        assert result == 0
        assert mock_info.call_count >= 2
        mock_info.assert_any_call("Running health checks...")
        mock_info.assert_any_call("Health checks completed successfully")

def test_health_command_validation(health_command: HealthCheckCommand):
    """Test health command argument validation."""
    assert health_command.validate({}) is True
    assert health_command.validate({"verbose": True}) is True
    assert health_command.validate({"service": "api"}) is True

def test_command_initialization(health_command):
    """Test command initialization."""
    assert isinstance(health_command.registry, MagicMock)
    assert set(health_command.checks.keys()) == {
        "services", "metrics", "logs", "errors"
    }

def test_create_command(health_command):
    """Test command creation."""
    command = health_command.create_command()
    assert isinstance(command, click.Command)
    assert command.name == "health"
    assert "check" in command.params
    assert "report" in command.params
    assert "format" in command.params
    assert "log-level" in command.params

def test_execute_all_healthy(health_command, mock_registry):
    """Test executing health checks with all services healthy."""
    # Mock service metrics and errors
    mock_service = MagicMock()
    mock_service.get_metrics.return_value = {
        "started_at": datetime.now().isoformat(),
        "total_calls": 10,
        "total_errors": 0
    }
    mock_service.get_errors.return_value = []
    
    mock_registry.get_service.return_value = mock_service
    
    result = health_command.execute()
    assert result["status"] == "healthy"
    assert "timestamp" in result
    assert len(result["checks"]) == 4
    
    for check in result["checks"].values():
        assert check["status"] == "healthy"

def test_execute_with_unhealthy_service(health_command, mock_registry):
    """Test executing health checks with unhealthy service."""
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
    
    result = health_command.execute()
    assert result["status"] == "unhealthy"
    assert "timestamp" in result
    assert result["checks"]["services"]["status"] == "unhealthy"

def test_execute_with_specific_checks(health_command):
    """Test executing specific health checks."""
    result = health_command.execute(checks=["services"])
    assert len(result["checks"]) == 1
    assert "services" in result["checks"]

def test_execute_with_report(health_command, mock_registry):
    """Test executing health checks with report generation."""
    # Mock service with mixed health status
    services = {
        "healthy_service": MagicMock(
            get_metrics=lambda: {"total_calls": 10, "total_errors": 0},
            get_errors=lambda: []
        ),
        "unhealthy_service": MagicMock(
            get_metrics=lambda: {"total_calls": 10, "total_errors": 2},
            get_errors=lambda: [{"error": "Test error"}]
        )
    }
    
    def get_service(name):
        return services.get(name)
    
    mock_registry.get_service.side_effect = get_service
    mock_registry.list_services.return_value = list(services.keys())
    
    result = health_command.execute(report=True)
    assert "report" in result
    assert "summary" in result["report"]
    assert "recommendations" in result["report"]

def test_check_services(health_command, mock_registry):
    """Test services health check."""
    # Mock services
    services = {
        "service1": MagicMock(
            get_metrics=lambda: {
                "started_at": datetime.now().isoformat(),
                "total_calls": 10,
                "total_errors": 0
            },
            get_errors=lambda: []
        ),
        "service2": MagicMock(
            get_metrics=lambda: {
                "started_at": datetime.now().isoformat(),
                "total_calls": 5,
                "total_errors": 1
            },
            get_errors=lambda: [{"error": "Test error"}]
        )
    }
    
    def get_service(name):
        return services.get(name)
    
    mock_registry.get_service.side_effect = get_service
    mock_registry.list_services.return_value = list(services.keys())
    
    result = health_command.check_services()
    assert result["healthy"] is False
    assert len(result["services"]) == 2
    assert result["services"]["service1"]["status"] == "healthy"
    assert result["services"]["service2"]["status"] == "unhealthy"

def test_check_metrics(health_command, mock_registry):
    """Test metrics health check."""
    # Mock metrics service
    metrics_service = MagicMock()
    metrics_service.collect.return_value = {
        "requests": {"total": 100},
        "errors": {"total": 0}
    }
    
    mock_registry.get_service.return_value = metrics_service
    
    result = health_command.check_metrics()
    assert result["healthy"] is True
    assert "metrics" in result

def test_check_logs(health_command, mock_registry):
    """Test logs health check."""
    # Mock logging service
    logging_service = MagicMock()
    logging_service.list_handlers.return_value = ["console", "file"]
    logging_service.get_records.return_value = [
        {"message": "Test log", "timestamp": datetime.now().isoformat()}
    ]
    
    mock_registry.get_service.return_value = logging_service
    
    result = health_command.check_logs()
    assert result["healthy"] is True
    assert "handlers" in result
    assert len(result["handlers"]) == 2

def test_check_errors(health_command, mock_registry):
    """Test errors health check."""
    # Mock registry errors
    mock_registry.get_all_errors.return_value = {
        "service1": [],
        "service2": [{"error": "Test error"}]
    }
    
    result = health_command.check_errors()
    assert result["healthy"] is False
    assert "errors" in result
    assert "service2" in result["errors"]

def test_generate_report(health_command):
    """Test report generation."""
    results = {
        "services": {
            "status": "unhealthy",
            "details": {
                "healthy": False,
                "services": {
                    "service1": {"status": "unhealthy", "error": "Test error"}
                }
            }
        },
        "metrics": {
            "status": "healthy",
            "details": {"healthy": True}
        }
    }
    
    report = health_command.generate_report(results)
    assert "summary" in report
    assert report["summary"]["total_checks"] == 2
    assert report["summary"]["healthy_checks"] == 1
    assert report["summary"]["unhealthy_checks"] == 1
    assert "recommendations" in report
    assert len(report["recommendations"]) > 0

def test_error_handling(health_command, mock_registry):
    """Test error handling during health checks."""
    # Mock service that raises an exception
    mock_service = MagicMock()
    mock_service.get_metrics.side_effect = Exception("Test error")
    mock_registry.get_service.return_value = mock_service
    
    result = health_command.execute()
    assert result["status"] == "unhealthy"
    assert "error" in result["checks"]["services"]

def test_command_exit_codes(health_command):
    """Test command exit codes."""
    runner = click.testing.CliRunner()
    command = health_command.create_command()
    
    # Test successful execution
    health_command.execute = MagicMock(
        return_value={"status": "healthy", "checks": {}}
    )
    result = runner.invoke(command)
    assert result.exit_code == 0
    
    # Test unhealthy status
    health_command.execute = MagicMock(
        return_value={"status": "unhealthy", "checks": {}}
    )
    result = runner.invoke(command)
    assert result.exit_code == 1
    
    # Test error
    health_command.execute = MagicMock(side_effect=Exception("Test error"))
    result = runner.invoke(command)
    assert result.exit_code == 2 