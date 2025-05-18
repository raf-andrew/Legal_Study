"""Unit tests for command executor."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from ..commands.executor import CommandExecutor
from ..commands.registry import CommandRegistry
from ..commands.health import HealthCheckCommand

@pytest.fixture
def registry() -> CommandRegistry:
    """Create a command registry instance."""
    return CommandRegistry()

@pytest.fixture
def executor(registry: CommandRegistry) -> CommandExecutor:
    """Create a command executor instance."""
    return CommandExecutor(registry)

@pytest.fixture
def mock_command() -> MagicMock:
    """Create a mock command."""
    command = MagicMock()
    command.__name__ = "MockCommand"
    command.return_value.validate.return_value = True
    command.return_value.execute.return_value = 0
    command.return_value.get_help.return_value = "Mock help"
    command.return_value.get_usage.return_value = "mock [options]"
    command.return_value.get_examples.return_value = ["mock", "mock --verbose"]
    return command

def test_executor_initialization(executor: CommandExecutor):
    """Test executor initialization."""
    assert isinstance(executor.registry, CommandRegistry)
    assert executor.logger.name == "command.executor"

def test_execute_command(executor: CommandExecutor, mock_command: MagicMock):
    """Test executing a command."""
    executor.registry.register(mock_command)
    result = executor.execute(mock_command.__name__, {})
    assert result == 0
    mock_command.return_value.validate.assert_called_once()
    mock_command.return_value.execute.assert_called_once()

def test_execute_nonexistent_command(executor: CommandExecutor):
    """Test executing a non-existent command."""
    with patch.object(executor.logger, "error") as mock_error:
        result = executor.execute("nonexistent", {})
        assert result == 1
        mock_error.assert_called_once()

def test_execute_command_validation_failed(executor: CommandExecutor, mock_command: MagicMock):
    """Test executing a command with failed validation."""
    mock_command.return_value.validate.return_value = False
    executor.registry.register(mock_command)
    with patch.object(executor.logger, "error") as mock_error:
        result = executor.execute(mock_command.__name__, {})
        assert result == 1
        mock_error.assert_called_once()

def test_execute_command_exception(executor: CommandExecutor, mock_command: MagicMock):
    """Test executing a command that raises an exception."""
    mock_command.return_value.execute.side_effect = Exception("Test error")
    executor.registry.register(mock_command)
    with patch.object(executor.logger, "error") as mock_error:
        result = executor.execute(mock_command.__name__, {})
        assert result == 1
        mock_error.assert_called_once()

def test_get_command_help(executor: CommandExecutor, mock_command: MagicMock):
    """Test getting command help."""
    executor.registry.register(mock_command)
    help_text = executor.get_command_help(mock_command.__name__)
    assert help_text == "Mock help"

def test_get_command_usage(executor: CommandExecutor, mock_command: MagicMock):
    """Test getting command usage."""
    executor.registry.register(mock_command)
    usage = executor.get_command_usage(mock_command.__name__)
    assert usage == "mock [options]"

def test_get_command_examples(executor: CommandExecutor, mock_command: MagicMock):
    """Test getting command examples."""
    executor.registry.register(mock_command)
    examples = executor.get_command_examples(mock_command.__name__)
    assert len(examples) == 2
    assert "mock" in examples
    assert "mock --verbose" in examples

def test_get_command_help_not_found(executor: CommandExecutor):
    """Test getting help for non-existent command."""
    help_text = executor.get_command_help("nonexistent")
    assert help_text is None

def test_get_command_usage_not_found(executor: CommandExecutor):
    """Test getting usage for non-existent command."""
    usage = executor.get_command_usage("nonexistent")
    assert usage is None

def test_get_command_examples_not_found(executor: CommandExecutor):
    """Test getting examples for non-existent command."""
    examples = executor.get_command_examples("nonexistent")
    assert len(examples) == 0 