"""Integration tests for health check command."""
import pytest
import json
import yaml
from typing import Dict, Any
from click.testing import CliRunner
from ..commands.health.command import HealthCheckCommand
from ...mocks.registry import MockServiceRegistry
from ...mocks.services.api import MockAPIService
from ...mocks.services.database import MockDatabase
from ...mocks.services.cache import MockCache
from ...mocks.services.queue import MockQueueService
from ...mocks.services.auth import MockAuthService
from ...mocks.services.metrics import MockMetricsService
from ...mocks.services.logging import MockLoggingService

@pytest.fixture
def config() -> Dict[str, Any]:
    """Load test configuration."""
    with open(".config/mock.yaml") as f:
        return yaml.safe_load(f)

@pytest.fixture
def registry(config) -> MockServiceRegistry:
    """Create service registry."""
    registry = MockServiceRegistry()
    registry._config = config
    return registry

@pytest.fixture
def health_command(registry) -> HealthCheckCommand:
    """Create health check command instance."""
    command = HealthCheckCommand()
    command.registry = registry
    return command

@pytest.fixture
def cli_runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()

def test_health_check_all_services(health_command, cli_runner):
    """Test health check with all services."""
    command = health_command.create_command()
    result = cli_runner.invoke(command)
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "healthy"
    assert len(data["checks"]) == 4

def test_health_check_specific_service(health_command, cli_runner):
    """Test health check for specific service."""
    command = health_command.create_command()
    result = cli_runner.invoke(command, ["--check", "services"])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["checks"]) == 1
    assert "services" in data["checks"]

def test_health_check_with_report(health_command, cli_runner):
    """Test health check with detailed report."""
    command = health_command.create_command()
    result = cli_runner.invoke(command, ["--report"])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "report" in data
    assert "summary" in data["report"]
    assert "recommendations" in data["report"]

def test_health_check_different_formats(health_command, cli_runner):
    """Test health check with different output formats."""
    command = health_command.create_command()
    
    # Test JSON format
    result = cli_runner.invoke(command, ["--format", "json"])
    assert result.exit_code == 0
    assert json.loads(result.output)
    
    # Test YAML format
    result = cli_runner.invoke(command, ["--format", "yaml"])
    assert result.exit_code == 0
    data = yaml.safe_load(result.output)
    assert isinstance(data, dict)
    
    # Test text format
    result = cli_runner.invoke(command, ["--format", "text"])
    assert result.exit_code == 0
    assert isinstance(result.output, str)

def test_health_check_with_errors(health_command, cli_runner, registry):
    """Test health check with service errors."""
    # Create service with errors
    api_service = registry.create_service("api")
    api_service.start()
    
    # Simulate error
    api_service.state.record_error(
        Exception("Test error"),
        {"action": "test"}
    )
    
    command = health_command.create_command()
    result = cli_runner.invoke(command)
    
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["status"] == "unhealthy"
    assert data["checks"]["services"]["status"] == "unhealthy"

def test_health_check_metrics_collection(health_command, cli_runner, registry):
    """Test health check metrics collection."""
    # Create and configure metrics service
    metrics_service = registry.create_service("metrics")
    metrics_service.start()
    
    # Create some metrics
    counter = metrics_service.create_counter("requests", ["method"])
    counter.inc(labels={"method": "GET"})
    
    command = health_command.create_command()
    result = cli_runner.invoke(command, ["--check", "metrics"])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["checks"]["metrics"]["status"] == "healthy"
    assert "requests" in data["checks"]["metrics"]["details"]["metrics"]

def test_health_check_logging_system(health_command, cli_runner, registry):
    """Test health check logging system."""
    # Create and configure logging service
    logging_service = registry.create_service("logging")
    logging_service.start()
    
    # Add test log
    logging_service.log("INFO", "Test message")
    
    command = health_command.create_command()
    result = cli_runner.invoke(command, ["--check", "logs"])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["checks"]["logs"]["status"] == "healthy"
    assert len(data["checks"]["logs"]["details"]["handlers"]) > 0

def test_health_check_service_interactions(health_command, cli_runner, registry):
    """Test health check with service interactions."""
    # Create and start services
    api_service = registry.create_service("api")
    db_service = registry.create_service("database")
    cache_service = registry.create_service("cache")
    
    api_service.start()
    db_service.start()
    cache_service.start()
    
    # Simulate some service interactions
    api_service.handle_request("/health")
    db_service.insert("users", {"id": "1", "name": "test"})
    cache_service.set("key", "value")
    
    command = health_command.create_command()
    result = cli_runner.invoke(command, ["--report"])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    services = data["checks"]["services"]["details"]["services"]
    
    assert services["api"]["total_calls"] == 1
    assert services["database"]["total_calls"] == 1
    assert services["cache"]["total_calls"] == 1

def test_health_check_error_handling(health_command, cli_runner, registry):
    """Test health check error handling."""
    # Create service that will raise an exception
    metrics_service = registry.create_service("metrics")
    metrics_service.collect = lambda: (_ for _ in ()).throw(Exception("Test error"))
    metrics_service.start()
    
    command = health_command.create_command()
    result = cli_runner.invoke(command)
    
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["checks"]["metrics"]["status"] == "error"
    assert "error" in data["checks"]["metrics"]

def test_health_check_performance(health_command, cli_runner, registry):
    """Test health check performance with many services."""
    # Create multiple services
    services = [
        ("api", MockAPIService),
        ("database", MockDatabase),
        ("cache", MockCache),
        ("queue", MockQueueService),
        ("auth", MockAuthService),
        ("metrics", MockMetricsService),
        ("logging", MockLoggingService)
    ]
    
    for name, service_class in services:
        service = registry.create_service(name)
        service.start()
    
    command = health_command.create_command()
    result = cli_runner.invoke(command, ["--report"])
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data["checks"]["services"]["details"]["services"]) == len(services)

def test_health_check_concurrent_access(health_command, cli_runner, registry):
    """Test health check with concurrent service access."""
    import threading
    
    # Create services
    api_service = registry.create_service("api")
    cache_service = registry.create_service("cache")
    api_service.start()
    cache_service.start()
    
    # Simulate concurrent access
    def access_services():
        for _ in range(10):
            api_service.handle_request("/health")
            cache_service.set(f"key_{_}", "value")
    
    threads = [
        threading.Thread(target=access_services)
        for _ in range(5)
    ]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    command = health_command.create_command()
    result = cli_runner.invoke(command)
    
    assert result.exit_code == 0
    data = json.loads(result.output)
    services = data["checks"]["services"]["details"]["services"]
    
    assert services["api"]["total_calls"] == 50
    assert services["cache"]["total_calls"] == 50 