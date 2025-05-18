import os
import sys
import pytest
import yaml
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from ..commands.console.health import HealthCheckCommand

@pytest.fixture
def command():
    """Create health check command."""
    return HealthCheckCommand()

@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()

@pytest.fixture
def mock_filesystem(tmp_path):
    """Set up mock filesystem."""
    # Create required directories
    (tmp_path / ".controls").mkdir()
    (tmp_path / ".config").mkdir()
    (tmp_path / ".logs").mkdir()
    (tmp_path / ".test").mkdir()
    (tmp_path / ".docs").mkdir()
    
    # Create configuration files
    config = {
        "test": "configuration"
    }
    
    config_files = [
        ".config/console.yaml",
        ".config/security.yaml",
        ".config/monitoring.yaml"
    ]
    
    for config_file in config_files:
        config_path = tmp_path / config_file
        config_path.parent.mkdir(exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(config, f)
    
    # Change to test directory
    original_dir = os.getcwd()
    os.chdir(str(tmp_path))
    yield str(tmp_path)
    os.chdir(original_dir)

def test_command_creation(command):
    """Test command creation."""
    assert command.name == "health"
    assert command.description == "Run health checks"
    assert len(command.checks) == 5

def test_check_directories_healthy(command, mock_filesystem):
    """Test directory checks with all directories present."""
    result = command.check_directories()
    assert result["healthy"] is True
    assert len(result["checked"]) == 5
    assert len(result["missing"]) == 0

def test_check_directories_unhealthy(command, mock_filesystem, tmp_path):
    """Test directory checks with missing directories."""
    # Remove a directory
    os.rmdir(tmp_path / ".controls")
    
    result = command.check_directories()
    assert result["healthy"] is False
    assert len(result["checked"]) == 4
    assert len(result["missing"]) == 1
    assert ".controls" in result["missing"]

def test_check_configurations_healthy(command, mock_filesystem):
    """Test configuration checks with all files present."""
    result = command.check_configurations()
    assert result["healthy"] is True
    assert len(result["checked"]) == 3
    assert len(result["missing"]) == 0
    assert len(result["invalid"]) == 0

def test_check_configurations_missing(command, mock_filesystem, tmp_path):
    """Test configuration checks with missing files."""
    # Remove a configuration file
    os.remove(tmp_path / ".config" / "console.yaml")
    
    result = command.check_configurations()
    assert result["healthy"] is False
    assert len(result["checked"]) == 2
    assert len(result["missing"]) == 1
    assert ".config/console.yaml" in result["missing"]

def test_check_configurations_invalid(command, mock_filesystem, tmp_path):
    """Test configuration checks with invalid files."""
    # Create invalid YAML file
    with open(tmp_path / ".config" / "console.yaml", "w") as f:
        f.write("invalid: yaml: content:")
    
    result = command.check_configurations()
    assert result["healthy"] is False
    assert len(result["checked"]) == 2
    assert len(result["invalid"]) == 1
    assert result["invalid"][0]["file"] == ".config/console.yaml"

def test_execute_all_checks(command, mock_filesystem):
    """Test executing all checks."""
    result = command.execute()
    assert result["status"] == "healthy"
    assert len(result["checks"]) == 5
    assert all(check["status"] == "healthy" for check in result["checks"].values())
    assert "metrics" in result

def test_execute_specific_checks(command, mock_filesystem):
    """Test executing specific checks."""
    result = command.execute(checks=["directories", "configurations"])
    assert result["status"] == "healthy"
    assert len(result["checks"]) == 2
    assert "directories" in result["checks"]
    assert "configurations" in result["checks"]

def test_execute_with_report(command, mock_filesystem):
    """Test executing checks with report generation."""
    result = command.execute(report=True)
    assert "report" in result["checks"]
    assert "summary" in result["checks"]["report"]
    assert "recommendations" in result["checks"]["report"]

def test_command_line_interface(command, runner, mock_filesystem):
    """Test command line interface."""
    click_command = command.create_command()
    result = runner.invoke(click_command, ["--check", "directories", "--report"])
    assert result.exit_code == 0
    assert "directories" in result.output
    assert "report" in result.output

def test_error_handling(command, runner, mock_filesystem):
    """Test error handling."""
    with patch.object(command, "check_directories", side_effect=Exception("Test error")):
        result = runner.invoke(command.create_command(), ["--check", "directories"])
        assert result.exit_code == 1
        assert "error" in result.output
        assert "Test error" in result.output

def test_metrics_recording(command, mock_filesystem):
    """Test metrics recording."""
    result = command.execute()
    metrics = result["metrics"]
    assert "command_start" in metrics
    assert "command_end" in metrics
    assert "duration" in metrics

def test_recommendations_generation(command, mock_filesystem, tmp_path):
    """Test recommendations generation."""
    # Create unhealthy state
    os.rmdir(tmp_path / ".controls")
    os.remove(tmp_path / ".config" / "console.yaml")
    
    result = command.execute(report=True)
    recommendations = result["checks"]["report"]["recommendations"]
    assert len(recommendations) > 0
    assert any("Create missing directory: .controls" in r for r in recommendations)
    assert any("Create missing configuration file: .config/console.yaml" in r for r in recommendations) 