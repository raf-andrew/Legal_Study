import pytest
from pathlib import Path
import os
import yaml
from codespaces.scripts.deployment_validation import DeploymentValidation

@pytest.fixture
def deployment_validation():
    """Fixture to provide a DeploymentValidation instance."""
    return DeploymentValidation()

@pytest.fixture
def mock_config(tmp_path):
    """Fixture to provide a mock configuration."""
    config = {
        "validation": {
            "requirements": {
                "disk_space": "10GB",
                "memory": "4GB",
                "cpu_cores": 2
            },
            "services": {
                "web": {
                    "ports": [8000],
                    "health_endpoint": "/health",
                    "dependencies": ["db", "redis"]
                },
                "db": {
                    "ports": [5432],
                    "health_endpoint": "/health",
                    "dependencies": []
                },
                "redis": {
                    "ports": [6379],
                    "health_endpoint": "/health",
                    "dependencies": []
                }
            }
        }
    }
    config_file = tmp_path / "config" / "codespaces_config.yaml"
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file

def test_deployment_validation_initialization(deployment_validation):
    """Test DeploymentValidation initialization."""
    assert deployment_validation is not None
    assert hasattr(deployment_validation, "_load_config")
    assert hasattr(deployment_validation, "validate_requirements")
    assert hasattr(deployment_validation, "validate_services")

def test_validate_requirements(deployment_validation, mock_config, monkeypatch):
    """Test validating system requirements."""
    # Mock system checks
    def mock_check_disk_space(*args, **kwargs):
        return {"total": "100GB", "free": "50GB"}

    def mock_check_memory(*args, **kwargs):
        return {"total": "8GB", "free": "4GB"}

    def mock_check_cpu(*args, **kwargs):
        return 4

    monkeypatch.setattr(deployment_validation, "_check_disk_space", mock_check_disk_space)
    monkeypatch.setattr(deployment_validation, "_check_memory", mock_check_memory)
    monkeypatch.setattr(deployment_validation, "_check_cpu", mock_check_cpu)

    # Test requirements validation
    result = deployment_validation.validate_requirements()
    assert result is True

def test_validate_services(deployment_validation, mock_config, monkeypatch):
    """Test validating services."""
    # Mock service checks
    def mock_check_port(*args, **kwargs):
        return True

    def mock_check_health(*args, **kwargs):
        return True

    def mock_check_dependencies(*args, **kwargs):
        return True

    monkeypatch.setattr(deployment_validation, "_check_port", mock_check_port)
    monkeypatch.setattr(deployment_validation, "_check_health", mock_check_health)
    monkeypatch.setattr(deployment_validation, "_check_dependencies", mock_check_dependencies)

    # Test services validation
    result = deployment_validation.validate_services()
    assert result is True

def test_check_port(deployment_validation, mock_config, monkeypatch):
    """Test checking port availability."""
    # Mock socket
    def mock_socket(*args, **kwargs):
        class MockSocket:
            def __init__(self):
                pass

            def bind(self, *args, **kwargs):
                return True

            def close(self):
                pass

        return MockSocket()

    monkeypatch.setattr("socket.socket", mock_socket)

    # Test port check
    result = deployment_validation._check_port(8000)
    assert result is True

def test_check_health(deployment_validation, mock_config, monkeypatch):
    """Test checking service health."""
    # Mock requests
    def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200
                self.json = lambda: {"status": "healthy"}

        return MockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    # Test health check
    result = deployment_validation._check_health("web", "/health")
    assert result is True

def test_check_dependencies(deployment_validation, mock_config, monkeypatch):
    """Test checking service dependencies."""
    # Mock Docker client
    class MockDockerClient:
        def containers(self):
            return [
                {"name": "db", "status": "running"},
                {"name": "redis", "status": "running"}
            ]

    monkeypatch.setattr(deployment_validation, "docker_client", MockDockerClient())

    # Test dependencies check
    result = deployment_validation._check_dependencies("web", ["db", "redis"])
    assert result is True

def test_error_handling(deployment_validation, mock_config, monkeypatch):
    """Test error handling in deployment validation."""
    # Test insufficient disk space
    def mock_check_disk_space(*args, **kwargs):
        return {"total": "100GB", "free": "5GB"}

    monkeypatch.setattr(deployment_validation, "_check_disk_space", mock_check_disk_space)

    with pytest.raises(ValueError) as exc_info:
        deployment_validation.validate_requirements()
    assert "Insufficient disk space" in str(exc_info.value)

    # Test service health check failure
    def mock_check_health(*args, **kwargs):
        raise Exception("Service health check failed")

    monkeypatch.setattr(deployment_validation, "_check_health", mock_check_health)

    with pytest.raises(Exception) as exc_info:
        deployment_validation.validate_services()
    assert "Service health check failed" in str(exc_info.value)
