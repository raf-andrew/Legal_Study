import pytest
from pathlib import Path
import os
import yaml
from codespaces.scripts.environment_switch import EnvironmentSwitch

@pytest.fixture
def env_switch():
    """Fixture to provide an EnvironmentSwitch instance."""
    return EnvironmentSwitch()

@pytest.fixture
def mock_config(tmp_path):
    """Fixture to provide a mock configuration."""
    config = {
        "environment": {
            "local": {
                "env_file": ".env.local",
                "compose_file": "docker-compose.local.yml"
            },
            "codespaces": {
                "env_file": ".env.codespaces",
                "compose_file": "docker-compose.codespaces.yml"
            }
        }
    }
    config_file = tmp_path / "config" / "codespaces_config.yaml"
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file

def test_environment_switch_initialization(env_switch):
    """Test EnvironmentSwitch initialization."""
    assert env_switch is not None
    assert hasattr(env_switch, "_setup_logging")
    assert hasattr(env_switch, "_load_config")
    assert hasattr(env_switch, "_print_status")

def test_load_config(env_switch, mock_config):
    """Test configuration loading."""
    config = env_switch._load_config()
    assert config is not None
    assert "environment" in config
    assert "local" in config["environment"]
    assert "codespaces" in config["environment"]

def test_switch_to_local(env_switch, mock_config, monkeypatch):
    """Test switching to local environment."""
    # Mock the necessary methods
    def mock_stop_services(*args, **kwargs):
        return True

    def mock_start_local_services(*args, **kwargs):
        return True

    monkeypatch.setattr(env_switch, "stop_services", mock_stop_services)
    monkeypatch.setattr(env_switch, "start_local_services", mock_start_local_services)

    # Test the switch
    result = env_switch.switch_to_local()
    assert result is True

def test_switch_to_codespaces(env_switch, mock_config, monkeypatch):
    """Test switching to Codespaces environment."""
    # Mock the necessary methods
    def mock_stop_services(*args, **kwargs):
        return True

    def mock_start_codespace_services(*args, **kwargs):
        return True

    monkeypatch.setattr(env_switch, "stop_services", mock_stop_services)
    monkeypatch.setattr(env_switch, "start_codespace_services", mock_start_codespace_services)

    # Test the switch
    result = env_switch.switch_to_codespaces()
    assert result is True

def test_error_handling(env_switch, mock_config, monkeypatch):
    """Test error handling in environment switching."""
    # Mock a failing service stop
    def mock_stop_services(*args, **kwargs):
        raise Exception("Failed to stop services")

    monkeypatch.setattr(env_switch, "stop_services", mock_stop_services)

    # Test error handling
    with pytest.raises(Exception) as exc_info:
        env_switch.switch_to_local()
    assert "Failed to stop services" in str(exc_info.value)
