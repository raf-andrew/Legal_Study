import pytest
from pathlib import Path
import os
import json
from codespaces.scripts.self_healing import SelfHealing

@pytest.fixture
def self_healing():
    """Fixture to provide a SelfHealing instance."""
    return SelfHealing()

@pytest.fixture
def mock_config(tmp_path):
    """Fixture to provide a mock configuration."""
    config = {
        "self_healing": {
            "health_checks": {
                "interval": 300,
                "timeout": 30,
                "retries": 3
            },
            "services": {
                "service1": {
                    "health_endpoint": "/health",
                    "restart_command": "docker restart service1"
                },
                "service2": {
                    "health_endpoint": "/health",
                    "restart_command": "docker restart service2"
                }
            }
        }
    }
    config_file = tmp_path / "config" / "codespaces_config.yaml"
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file

def test_self_healing_initialization(self_healing):
    """Test SelfHealing initialization."""
    assert self_healing is not None
    assert hasattr(self_healing, "_setup_logging")
    assert hasattr(self_healing, "_load_config")
    assert hasattr(self_healing, "_print_status")

def test_check_service_health(self_healing, mock_config, monkeypatch):
    """Test checking service health."""
    # Mock requests.get
    def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.json = lambda: {"status": "healthy"}
        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    # Test health check
    result = self_healing.check_service_health("service1")
    assert result is True

def test_restart_service(self_healing, mock_config, monkeypatch):
    """Test restarting a service."""
    # Mock subprocess.run
    def mock_run(*args, **kwargs):
        class MockResult:
            def __init__(self):
                self.returncode = 0
                self.stdout = "Service restarted successfully"
        return MockResult()

    monkeypatch.setattr(subprocess, "run", mock_run)

    # Test service restart
    result = self_healing.restart_service("service1")
    assert result is True

def test_heal_service(self_healing, mock_config, monkeypatch):
    """Test healing a service."""
    # Mock health check and restart
    def mock_check_health(*args, **kwargs):
        return False

    def mock_restart(*args, **kwargs):
        return True

    monkeypatch.setattr(self_healing, "check_service_health", mock_check_health)
    monkeypatch.setattr(self_healing, "restart_service", mock_restart)

    # Test service healing
    result = self_healing.heal_service("service1")
    assert result is True

def test_run_health_checks(self_healing, mock_config, monkeypatch):
    """Test running health checks."""
    # Mock health check
    def mock_check_health(*args, **kwargs):
        return True

    monkeypatch.setattr(self_healing, "check_service_health", mock_check_health)

    # Test health checks
    result = self_healing.run_health_checks()
    assert result is True

def test_handle_service_failure(self_healing, mock_config, monkeypatch):
    """Test handling service failure."""
    # Mock healing
    def mock_heal_service(*args, **kwargs):
        return True

    monkeypatch.setattr(self_healing, "heal_service", mock_heal_service)

    # Test failure handling
    result = self_healing.handle_service_failure("service1")
    assert result is True

def test_error_handling(self_healing, mock_config, monkeypatch):
    """Test error handling in self-healing."""
    # Mock a failing health check
    def mock_check_health(*args, **kwargs):
        raise Exception("Failed to check health")

    monkeypatch.setattr(self_healing, "check_service_health", mock_check_health)

    # Test error handling
    with pytest.raises(Exception) as exc_info:
        self_healing.check_service_health("service1")
    assert "Failed to check health" in str(exc_info.value)
