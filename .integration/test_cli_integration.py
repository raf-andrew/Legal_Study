import os
import sys
import pytest
import yaml
import json
from click.testing import CliRunner
from legal_study.console.cli import cli, check, version

@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()

@pytest.fixture
def config_file(tmp_path):
    """Create a temporary config file for testing."""
    config = {
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
    config_path = tmp_path / 'test_config.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    return str(config_path)

@pytest.fixture
def setup_test_environment(tmp_path):
    """Set up test environment with required directories and files."""
    # Create directories
    (tmp_path / '.controls').mkdir()
    (tmp_path / '.config').mkdir()
    (tmp_path / '.logs').mkdir()
    
    # Create config file
    config = {
        'test': 'configuration'
    }
    with open(tmp_path / '.config' / 'console.yaml', 'w') as f:
        yaml.dump(config, f)
    
    # Change to test directory
    original_dir = os.getcwd()
    os.chdir(str(tmp_path))
    yield str(tmp_path)
    os.chdir(original_dir)

def test_check_command_full_integration(runner, setup_test_environment, config_file):
    """Test the check command with full integration."""
    # Run check command with all options
    result = runner.invoke(check, [
        '--check', 'directories',
        '--check', 'configurations',
        '--report',
        '--log-level', 'DEBUG',
        '--config', config_file,
        '--output', 'json'
    ])
    
    assert result.exit_code == 0
    
    # Verify log file creation
    assert os.path.exists('.logs/console.log')
    
    # Verify JSON output
    try:
        output = json.loads(result.output)
        assert 'checks' in output
        assert 'directories' in output['checks']
        assert 'configurations' in output['checks']
    except json.JSONDecodeError:
        pytest.fail("Output is not valid JSON")

def test_check_command_directory_validation(runner, setup_test_environment):
    """Test directory validation in check command."""
    result = runner.invoke(check, ['--check', 'directories'])
    assert result.exit_code == 0
    assert '.controls' in result.output
    assert '.config' in result.output

def test_check_command_config_validation(runner, setup_test_environment):
    """Test configuration validation in check command."""
    result = runner.invoke(check, ['--check', 'configurations'])
    assert result.exit_code == 0
    assert 'console.yaml' in result.output

def test_check_command_with_missing_directory(runner, setup_test_environment):
    """Test check command with missing required directory."""
    # Remove required directory
    os.rmdir('.controls')
    
    result = runner.invoke(check, ['--check', 'directories'])
    assert result.exit_code == 1
    assert 'Error' in result.output

def test_check_command_with_invalid_config(runner, setup_test_environment):
    """Test check command with invalid configuration."""
    # Create invalid config file
    with open('.config/console.yaml', 'w') as f:
        f.write('invalid: yaml: content')
    
    result = runner.invoke(check, ['--check', 'configurations'])
    assert result.exit_code == 1
    assert 'Error' in result.output

def test_check_command_report_generation(runner, setup_test_environment):
    """Test report generation in check command."""
    result = runner.invoke(check, ['--report'])
    assert result.exit_code == 0
    
    # Verify report contains all sections
    assert 'Directories' in result.output
    assert 'Configurations' in result.output
    assert 'Summary' in result.output

def test_check_command_yaml_output(runner, setup_test_environment):
    """Test YAML output format in check command."""
    result = runner.invoke(check, ['--output', 'yaml'])
    assert result.exit_code == 0
    
    # Verify YAML output
    try:
        output = yaml.safe_load(result.output)
        assert 'checks' in output
    except yaml.YAMLError:
        pytest.fail("Output is not valid YAML") 