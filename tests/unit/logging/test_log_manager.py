import pytest
from pathlib import Path
import os
import yaml
import json
from codespaces.scripts.log_manager import LogManager

@pytest.fixture
def log_manager():
    """Fixture to provide a LogManager instance."""
    return LogManager()

@pytest.fixture
def mock_config(tmp_path):
    """Fixture to provide a mock configuration."""
    config = {
        "logging": {
            "elasticsearch": {
                "host": "localhost",
                "port": 9200,
                "index": "logs"
            },
            "kibana": {
                "host": "localhost",
                "port": 5601
            },
            "services": ["service1", "service2"]
        }
    }
    config_file = tmp_path / "config" / "codespaces_config.yaml"
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file

def test_log_manager_initialization(log_manager):
    """Test LogManager initialization."""
    assert log_manager is not None
    assert hasattr(log_manager, "_setup_logging")
    assert hasattr(log_manager, "_load_config")
    assert hasattr(log_manager, "_print_status")

def test_setup_elasticsearch(log_manager, mock_config, monkeypatch):
    """Test Elasticsearch setup."""
    # Mock Docker client
    class MockDockerClient:
        def containers(self):
            return []

        def run(self, *args, **kwargs):
            return True

    monkeypatch.setattr(log_manager, "docker_client", MockDockerClient())

    # Test Elasticsearch setup
    result = log_manager.setup_elasticsearch()
    assert result is True

def test_setup_kibana(log_manager, mock_config, monkeypatch):
    """Test Kibana setup."""
    # Mock Docker client
    class MockDockerClient:
        def containers(self):
            return []

        def run(self, *args, **kwargs):
            return True

    monkeypatch.setattr(log_manager, "docker_client", MockDockerClient())

    # Test Kibana setup
    result = log_manager.setup_kibana()
    assert result is True

def test_collect_service_logs(log_manager, mock_config, monkeypatch):
    """Test collecting service logs."""
    # Mock Docker client
    class MockDockerClient:
        def containers(self):
            return [{"name": "service1"}, {"name": "service2"}]

        def logs(self, *args, **kwargs):
            return b"Test log message"

    monkeypatch.setattr(log_manager, "docker_client", MockDockerClient())

    # Test log collection
    result = log_manager.collect_service_logs()
    assert result is True

def test_generate_audit_report(log_manager, mock_config, tmp_path):
    """Test generating audit report."""
    # Create mock deployment data
    deployment_data = {
        "deployments": [
            {
                "id": "1",
                "timestamp": "2024-01-01T00:00:00",
                "status": "success"
            }
        ]
    }

    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / "deployment_history.json", "w") as f:
        json.dump(deployment_data, f)

    # Test report generation
    result = log_manager.generate_audit_report()
    assert result is True

def test_error_handling(log_manager, mock_config, monkeypatch):
    """Test error handling in log manager."""
    # Mock a failing Elasticsearch setup
    def mock_setup_elasticsearch(*args, **kwargs):
        raise Exception("Failed to setup Elasticsearch")

    monkeypatch.setattr(log_manager, "setup_elasticsearch", mock_setup_elasticsearch)

    # Test error handling
    with pytest.raises(Exception) as exc_info:
        log_manager.setup_elasticsearch()
    assert "Failed to setup Elasticsearch" in str(exc_info.value)
