"""Unit tests for base command implementation."""

import pytest
from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from ..commands.base import BaseCommand

class TestCommand(BaseCommand):
    """Test command implementation."""
    
    def __init__(self):
        """Initialize test command."""
        super().__init__("test", "Test command for unit testing")
        
    def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute test command."""
        return {"status": "success", "args": args, "kwargs": kwargs}

class FailingCommand(BaseCommand):
    """Test command that fails execution."""
    
    def __init__(self):
        """Initialize failing command."""
        super().__init__("fail", "Test command that fails")
        
    def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute failing command."""
        raise ValueError("Command failed")

class ValidationCommand(BaseCommand):
    """Test command with validation."""
    
    def __init__(self):
        """Initialize validation command."""
        super().__init__("validate", "Test command with validation")
        
    def validate(self, *args: Any, **kwargs: Any) -> bool:
        """Validate command arguments."""
        return len(args) > 0 and "required" in kwargs
        
    def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute validation command."""
        return {"status": "success", "args": args, "kwargs": kwargs}

@pytest.fixture
def test_command() -> TestCommand:
    """Create test command instance."""
    return TestCommand()

@pytest.fixture
def failing_command() -> FailingCommand:
    """Create failing command instance."""
    return FailingCommand()

@pytest.fixture
def validation_command() -> ValidationCommand:
    """Create validation command instance."""
    return ValidationCommand()

def test_command_initialization(test_command):
    """Test command initialization."""
    assert test_command.name == "test"
    assert test_command.description == "Test command for unit testing"
    assert test_command._start_time is None
    assert test_command._end_time is None
    assert isinstance(test_command._execution_context, dict)

def test_command_execution(test_command):
    """Test command execution."""
    result = test_command.run("arg1", "arg2", kwarg1="value1")
    
    assert result["status"] == "success"
    assert result["args"] == ("arg1", "arg2")
    assert result["kwargs"] == {"kwarg1": "value1"}
    assert "metadata" in result
    assert result["metadata"]["command"] == "test"
    assert result["metadata"]["start_time"] is not None
    assert result["metadata"]["end_time"] is not None
    assert result["metadata"]["duration"] >= 0

def test_command_failure(failing_command):
    """Test command failure handling."""
    with pytest.raises(ValueError) as exc:
        failing_command.run()
    assert str(exc.value) == "Command failed"

def test_command_validation(validation_command):
    """Test command validation."""
    # Valid arguments
    result = validation_command.run("arg1", required=True)
    assert result["status"] == "success"
    
    # Invalid arguments
    with pytest.raises(ValueError) as exc:
        validation_command.run(required=True)
    assert "Validation failed" in str(exc.value)
    
    with pytest.raises(ValueError) as exc:
        validation_command.run("arg1")
    assert "Validation failed" in str(exc.value)

def test_command_timing(test_command):
    """Test command execution timing."""
    assert test_command.execution_time is None
    
    test_command.run()
    
    assert test_command.execution_time is not None
    assert test_command.execution_time >= 0

def test_command_context(test_command):
    """Test command execution context."""
    args = ("arg1", "arg2")
    kwargs = {"key": "value"}
    
    test_command.run(*args, **kwargs)
    context = test_command.get_execution_context()
    
    assert context["args"] == args
    assert context["kwargs"] == kwargs
    assert isinstance(context["start_time"], datetime)

def test_command_help(test_command):
    """Test command help information."""
    help_info = test_command.get_help()
    
    assert help_info["name"] == "test"
    assert help_info["description"] == "Test command for unit testing"
    assert "usage" in help_info

def test_command_logging(test_command):
    """Test command logging."""
    with patch.object(test_command.logger, 'info') as mock_info:
        with patch.object(test_command.logger, 'error') as mock_error:
            # Test successful execution logging
            test_command.run()
            assert mock_info.call_count == 2  # start and end logs
            assert mock_error.call_count == 0
            
            # Test failure logging
            failing_command = FailingCommand()
            with pytest.raises(ValueError):
                failing_command.run()
            assert mock_error.call_count == 1 