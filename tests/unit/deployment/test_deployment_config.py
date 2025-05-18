import pytest
from pathlib import Path
import os
import yaml
from codespaces.scripts.deployment_config import DeploymentConfig

@pytest.fixture
def deployment_config():
    """Fixture to provide a DeploymentConfig instance."""
    return DeploymentConfig()

@pytest.fixture
def mock_config(tmp_path):
    """Fixture to provide a mock configuration."""
    config = {
        "deployment": {
            "environments": {
                "local": {
                    "docker_compose": "docker-compose.local.yml",
                    "env_file": ".env.local"
                },
                "codespaces": {
                    "docker_compose": "docker-compose.codespaces.yml",
                    "env_file": ".env.codespaces"
                }
            },
            "services": {
                "web": {
                    "image": "web:latest",
                    "ports": ["8000:8000"],
                    "depends_on": ["db", "redis"]
                },
                "db": {
                    "image": "postgres:13",
                    "ports": ["5432:5432"],
                    "environment": {
                        "POSTGRES_DB": "app",
                        "POSTGRES_USER": "user",
                        "POSTGRES_PASSWORD": "password"
                    }
                },
                "redis": {
                    "image": "redis:6",
                    "ports": ["6379:6379"]
                }
            }
        }
    }
    config_file = tmp_path / "config" / "codespaces_config.yaml"
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file

def test_deployment_config_initialization(deployment_config):
    """Test DeploymentConfig initialization."""
    assert deployment_config is not None
    assert hasattr(deployment_config, "_load_config")
    assert hasattr(deployment_config, "get_environment_config")
    assert hasattr(deployment_config, "get_service_config")

def test_load_config(deployment_config, mock_config):
    """Test loading configuration."""
    config = deployment_config._load_config()
    assert config is not None
    assert "deployment" in config
    assert "environments" in config["deployment"]
    assert "services" in config["deployment"]

def test_get_environment_config(deployment_config, mock_config):
    """Test getting environment configuration."""
    # Test local environment
    local_config = deployment_config.get_environment_config("local")
    assert local_config is not None
    assert "docker_compose" in local_config
    assert "env_file" in local_config
    assert local_config["docker_compose"] == "docker-compose.local.yml"

    # Test codespaces environment
    codespaces_config = deployment_config.get_environment_config("codespaces")
    assert codespaces_config is not None
    assert "docker_compose" in codespaces_config
    assert "env_file" in codespaces_config
    assert codespaces_config["docker_compose"] == "docker-compose.codespaces.yml"

def test_get_service_config(deployment_config, mock_config):
    """Test getting service configuration."""
    # Test web service
    web_config = deployment_config.get_service_config("web")
    assert web_config is not None
    assert "image" in web_config
    assert "ports" in web_config
    assert "depends_on" in web_config
    assert web_config["image"] == "web:latest"

    # Test db service
    db_config = deployment_config.get_service_config("db")
    assert db_config is not None
    assert "image" in db_config
    assert "ports" in db_config
    assert "environment" in db_config
    assert db_config["image"] == "postgres:13"

def test_validate_config(deployment_config, mock_config):
    """Test validating configuration."""
    # Test valid config
    result = deployment_config.validate_config()
    assert result is True

    # Test invalid config
    invalid_config = {
        "deployment": {
            "environments": {},
            "services": {}
        }
    }
    with open(mock_config, "w") as f:
        yaml.dump(invalid_config, f)

    with pytest.raises(ValueError) as exc_info:
        deployment_config.validate_config()
    assert "Invalid configuration" in str(exc_info.value)

def test_error_handling(deployment_config, mock_config):
    """Test error handling in deployment config."""
    # Test missing config file
    os.remove(mock_config)

    with pytest.raises(FileNotFoundError) as exc_info:
        deployment_config._load_config()
    assert "Configuration file not found" in str(exc_info.value)

    # Test invalid YAML
    with open(mock_config, "w") as f:
        f.write("invalid: yaml: content: [")

    with pytest.raises(yaml.YAMLError) as exc_info:
        deployment_config._load_config()
    assert "Error parsing configuration file" in str(exc_info.value)
