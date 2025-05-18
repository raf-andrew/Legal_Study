"""Unit tests for command registry."""

import pytest
from typing import Any, Dict
from unittest.mock import patch, MagicMock

from ..commands.base import BaseCommand
from ..commands.registry import CommandRegistry
from ..commands.health import HealthCheckCommand

class TestCommand(BaseCommand):
    """Test command for registry testing."""
    
    def __init__(self):
        """Initialize test command."""
        super().__init__("test", "Test command")
        
    def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute test command."""
        return {"status": "success"}

class AnotherCommand(BaseCommand):
    """Another test command for registry testing."""
    
    def __init__(self):
        """Initialize another test command."""
        super().__init__("another", "Another test command")
        
    def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute another test command."""
        return {"status": "success"}

@pytest.fixture
def registry() -> CommandRegistry:
    """Create a command registry instance."""
    return CommandRegistry()

@pytest.fixture
def test_command_class() -> type:
    """Get test command class."""
    return TestCommand

@pytest.fixture
def another_command_class() -> type:
    """Get another test command class."""
    return AnotherCommand

@pytest.fixture
def mock_command() -> MagicMock:
    """Create a mock command."""
    command = MagicMock()
    command.__name__ = "MockCommand"
    command.return_value.get_help.return_value = "Mock help"
    command.return_value.get_usage.return_value = "mock [options]"
    command.return_value.get_examples.return_value = ["mock", "mock --verbose"]
    return command

def test_registry_initialization(registry: CommandRegistry):
    """Test registry initialization."""
    assert isinstance(registry._commands, dict)
    assert len(registry._commands) == 0
    assert registry.logger.name == "command.registry"

def test_command_registration(registry: CommandRegistry, mock_command: MagicMock):
    """Test command registration."""
    registry.register(mock_command)
    assert mock_command.__name__.lower() in registry._commands
    assert registry._commands[mock_command.__name__.lower()] == mock_command

def test_command_registration_duplicate(registry: CommandRegistry, mock_command: MagicMock):
    """Test duplicate command registration."""
    registry.register(mock_command)
    with patch.object(registry.logger, "warning") as mock_warning:
        registry.register(mock_command)
        mock_warning.assert_called_once()

def test_get_command(registry: CommandRegistry, mock_command: MagicMock):
    """Test getting a command."""
    registry.register(mock_command)
    command = registry.get_command(mock_command.__name__)
    assert command == mock_command

def test_get_command_not_found(registry: CommandRegistry):
    """Test getting a non-existent command."""
    command = registry.get_command("nonexistent")
    assert command is None

def test_list_commands(registry: CommandRegistry, mock_command: MagicMock):
    """Test listing commands."""
    registry.register(mock_command)
    commands = registry.list_commands()
    assert len(commands) == 1
    assert mock_command.__name__.lower() in commands

def test_unregister_command(registry: CommandRegistry, mock_command: MagicMock):
    """Test unregistering a command."""
    registry.register(mock_command)
    assert registry.unregister(mock_command.__name__) is True
    assert mock_command.__name__.lower() not in registry._commands

def test_unregister_nonexistent_command(registry: CommandRegistry):
    """Test unregistering a non-existent command."""
    assert registry.unregister("nonexistent") is False

def test_get_command_help(registry: CommandRegistry, mock_command: MagicMock):
    """Test getting command help."""
    registry.register(mock_command)
    help_text = registry.get_command_help(mock_command.__name__)
    assert help_text == "Mock help"

def test_get_command_usage(registry: CommandRegistry, mock_command: MagicMock):
    """Test getting command usage."""
    registry.register(mock_command)
    usage = registry.get_command_usage(mock_command.__name__)
    assert usage == "mock [options]"

def test_get_command_examples(registry: CommandRegistry, mock_command: MagicMock):
    """Test getting command examples."""
    registry.register(mock_command)
    examples = registry.get_command_examples(mock_command.__name__)
    assert len(examples) == 2
    assert "mock" in examples
    assert "mock --verbose" in examples

def test_get_command_help_not_found(registry: CommandRegistry):
    """Test getting help for non-existent command."""
    help_text = registry.get_command_help("nonexistent")
    assert help_text is None

def test_get_command_usage_not_found(registry: CommandRegistry):
    """Test getting usage for non-existent command."""
    usage = registry.get_command_usage("nonexistent")
    assert usage is None

def test_get_command_examples_not_found(registry: CommandRegistry):
    """Test getting examples for non-existent command."""
    examples = registry.get_command_examples("nonexistent")
    assert len(examples) == 0

def test_command_execution(registry, test_command_class):
    """Test command execution through registry."""
    registry.register(test_command_class)
    result = registry.execute("test")
    
    assert result["status"] == "success"
    assert "metadata" in result
    assert result["metadata"]["command"] == "test"

def test_execute_nonexistent_command(registry):
    """Test executing nonexistent command."""
    with pytest.raises(KeyError) as exc:
        registry.execute("nonexistent")
    assert "Command not registered" in str(exc.value)

def test_list_commands(registry, test_command_class, another_command_class):
    """Test listing registered commands."""
    registry.register(test_command_class)
    registry.register(another_command_class)
    
    commands = registry.list_commands()
    assert len(commands) == 2
    assert "test" in commands
    assert "another" in commands

def test_get_help(registry, test_command_class):
    """Test getting command help information."""
    registry.register(test_command_class)
    
    # Test specific command help
    help_info = registry.get_help("test")
    assert help_info["name"] == "test"
    assert help_info["description"] == "Test command"
    
    # Test all commands help
    all_help = registry.get_help()
    assert len(all_help) == 1
    assert "test" in all_help
    assert all_help["test"] == help_info

def test_get_help_nonexistent(registry):
    """Test getting help for nonexistent command."""
    with pytest.raises(KeyError) as exc:
        registry.get_help("nonexistent")
    assert "Command not registered" in str(exc.value)

def test_clear_registry(registry, test_command_class, another_command_class):
    """Test clearing command registry."""
    registry.register(test_command_class)
    registry.register(another_command_class)
    
    assert len(registry.list_commands()) == 2
    
    registry.clear()
    
    assert len(registry.list_commands()) == 0
    assert len(registry._instances) == 0

def test_command_instance_reuse(registry, test_command_class):
    """Test command instance reuse."""
    registry.register(test_command_class)
    
    command1 = registry.get_command("test")
    command2 = registry.get_command("test")
    
    assert command1 is command2  # Same instance

def test_registry_logging(registry, test_command_class):
    """Test registry logging."""
    with patch.object(registry.logger, 'info') as mock_info:
        # Test registration logging
        registry.register(test_command_class)
        assert mock_info.call_count == 1
        assert "Registering command" in mock_info.call_args_list[0][0][0]
        
        # Test execution logging
        registry.execute("test")
        assert mock_info.call_count == 2
        assert "Executing command" in mock_info.call_args_list[1][0][0]
        
        # Test unregistration logging
        registry.unregister("test")
        assert mock_info.call_count == 3
        assert "Unregistering command" in mock_info.call_args_list[2][0][0]
        
        # Test clear logging
        registry.clear()
        assert mock_info.call_count == 4
        assert "Clearing command registry" in mock_info.call_args_list[3][0][0] 