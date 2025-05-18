import os
import sys
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from legal_study.console.cli import cli, check, version

@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()

@pytest.fixture
def mock_logger():
    """Mock the logger for testing."""
    with patch('legal_study.console.cli.logger') as mock:
        yield mock

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        'general': {
            'version': '1.0.0',
            'environment': 'test',
            'debug': True
        },
        'checks': {
            'enabled': ['directories', 'configurations'],
            'required': {
                'directories': ['.controls', '.config'],
                'configurations': ['console.yaml']
            }
        }
    }

def test_cli_version(runner):
    """Test the version command."""
    result = runner.invoke(version)
    assert result.exit_code == 0
    assert 'Legal Study Console v1.0.0' in result.output

def test_check_command_no_options(runner, mock_logger):
    """Test the check command with no options."""
    result = runner.invoke(check)
    assert result.exit_code == 0
    mock_logger.info.assert_called_once()

def test_check_command_with_specific_checks(runner, mock_logger):
    """Test the check command with specific checks."""
    result = runner.invoke(check, ['--check', 'directories'])
    assert result.exit_code == 0
    mock_logger.info.assert_called_once()

def test_check_command_with_report(runner, mock_logger):
    """Test the check command with report generation."""
    result = runner.invoke(check, ['--report'])
    assert result.exit_code == 0
    mock_logger.info.assert_called_once()

def test_check_command_with_custom_log_level(runner, mock_logger):
    """Test the check command with custom log level."""
    result = runner.invoke(check, ['--log-level', 'DEBUG'])
    assert result.exit_code == 0
    mock_logger.info.assert_called_once()

def test_check_command_with_config_file(runner, mock_logger, mock_config):
    """Test the check command with config file."""
    with patch('legal_study.console.cli.load_config', return_value=mock_config):
        result = runner.invoke(check, ['--config', 'test_config.yaml'])
        assert result.exit_code == 0
        mock_logger.info.assert_called_once()

def test_check_command_with_json_output(runner, mock_logger):
    """Test the check command with JSON output."""
    result = runner.invoke(check, ['--output', 'json'])
    assert result.exit_code == 0
    mock_logger.info.assert_called_once()

def test_check_command_with_yaml_output(runner, mock_logger):
    """Test the check command with YAML output."""
    result = runner.invoke(check, ['--output', 'yaml'])
    assert result.exit_code == 0
    mock_logger.info.assert_called_once()

def test_check_command_error_handling(runner, mock_logger):
    """Test the check command error handling."""
    with patch('legal_study.console.cli.check', side_effect=Exception('Test error')):
        result = runner.invoke(check)
        assert result.exit_code == 1
        mock_logger.error.assert_called_once_with('Error running health checks: Test error') 