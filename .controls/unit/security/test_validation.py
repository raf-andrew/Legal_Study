"""Unit tests for security validation interface."""

import pytest
from datetime import datetime
from typing import Any, Dict, Set

from ...security.validation import (
    ValidationContext,
    ValidationResult,
    ValidationRule,
    ArgumentValidationRule,
    PermissionValidationRule,
    ValidationPipeline
)

@pytest.fixture
def validation_context() -> ValidationContext:
    """Create test validation context."""
    return ValidationContext(
        command_name="test_command",
        arguments={
            "arg1": "value1",
            "arg2": 42,
            "arg3": ["item1", "item2"]
        },
        user_id="test_user",
        roles={"user", "admin"},
        permissions={"read", "write"},
        environment={"env": "test"},
        metadata={"test": True}
    )

class TestValidationRule(ValidationRule):
    """Test validation rule implementation."""
    
    def __init__(self, should_pass: bool = True):
        """Initialize test rule."""
        super().__init__("test_rule", "Test validation rule")
        self.should_pass = should_pass
    
    def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate context."""
        if self.should_pass:
            return ValidationResult(is_valid=True)
        return ValidationResult(
            is_valid=False,
            errors=["Test validation error"]
        )

def test_validation_context_initialization(validation_context):
    """Test validation context initialization."""
    assert validation_context.command_name == "test_command"
    assert validation_context.arguments == {
        "arg1": "value1",
        "arg2": 42,
        "arg3": ["item1", "item2"]
    }
    assert validation_context.user_id == "test_user"
    assert validation_context.roles == {"user", "admin"}
    assert validation_context.permissions == {"read", "write"}
    assert validation_context.environment == {"env": "test"}
    assert validation_context.metadata == {"test": True}
    assert isinstance(validation_context.timestamp, datetime)

def test_validation_result_initialization():
    """Test validation result initialization."""
    # Test valid result
    result = ValidationResult(is_valid=True)
    assert result.is_valid
    assert not result.errors
    assert not result.warnings
    assert not result.metadata
    
    # Test invalid result
    result = ValidationResult(
        is_valid=False,
        errors=["Error 1"],
        warnings=["Warning 1"],
        metadata={"test": True}
    )
    assert not result.is_valid
    assert result.errors == ["Error 1"]
    assert result.warnings == ["Warning 1"]
    assert result.metadata == {"test": True}

def test_argument_validation_rule():
    """Test argument validation rule."""
    rule = ArgumentValidationRule(
        name="test_args",
        description="Test argument validation",
        required_args={"arg1", "arg2"},
        arg_types={"arg1": str, "arg2": int, "arg3": list},
        arg_constraints={
            "arg1": {"min_length": 3, "max_length": 10},
            "arg2": {"min": 0, "max": 100},
            "arg3": {"min_length": 1}
        }
    )
    
    # Test valid arguments
    context = ValidationContext(
        command_name="test",
        arguments={
            "arg1": "value1",
            "arg2": 42,
            "arg3": ["item1"]
        }
    )
    result = rule.validate(context)
    assert result.is_valid
    assert not result.errors
    
    # Test missing required argument
    context.arguments.pop("arg1")
    result = rule.validate(context)
    assert not result.is_valid
    assert "Missing required argument: arg1" in result.errors
    
    # Test invalid type
    context.arguments["arg2"] = "not_an_int"
    result = rule.validate(context)
    assert not result.is_valid
    assert any("Invalid type for argument arg2" in error for error in result.errors)
    
    # Test constraint violation
    context.arguments.update({
        "arg1": "a",  # too short
        "arg2": 200,  # too large
        "arg3": []    # empty list
    })
    result = rule.validate(context)
    assert not result.is_valid
    assert len(result.errors) == 3

def test_permission_validation_rule():
    """Test permission validation rule."""
    rule = PermissionValidationRule(
        name="test_perms",
        description="Test permission validation",
        required_permissions={"read", "write", "delete"},
        required_roles={"admin", "user"}
    )
    
    # Test valid permissions and roles
    context = ValidationContext(
        command_name="test",
        arguments={},
        roles={"admin", "user"},
        permissions={"read", "write", "delete"}
    )
    result = rule.validate(context)
    assert result.is_valid
    assert not result.errors
    
    # Test missing permissions
    context.permissions.remove("delete")
    result = rule.validate(context)
    assert not result.is_valid
    assert "Missing required permissions: delete" in result.errors
    
    # Test missing roles
    context.roles.remove("admin")
    result = rule.validate(context)
    assert not result.is_valid
    assert "Missing required roles: admin" in result.errors

def test_validation_pipeline():
    """Test validation pipeline."""
    pipeline = ValidationPipeline()
    
    # Add rules
    pipeline.add_rule(TestValidationRule(should_pass=True))
    pipeline.add_rule(TestValidationRule(should_pass=True))
    pipeline.add_rule(TestValidationRule(should_pass=False))
    
    # Test validation
    context = ValidationContext(
        command_name="test",
        arguments={}
    )
    result = pipeline.validate(context)
    
    assert not result.is_valid
    assert len(result.errors) == 1
    assert "Test validation error" in result.errors
    assert len(result.metadata) == 3
    
    # Verify metadata
    assert result.metadata["test_rule"]["is_valid"] is False
    assert "Test validation error" in result.metadata["test_rule"]["errors"]

def test_constraint_checking():
    """Test constraint checking."""
    rule = ArgumentValidationRule(
        name="test_constraints",
        description="Test constraint validation",
        required_args=set(),
        arg_types={},
        arg_constraints={
            "str_arg": {
                "min_length": 3,
                "max_length": 10,
                "pattern": r"^[a-z]+$"
            },
            "num_arg": {
                "min": 0,
                "max": 100
            },
            "enum_arg": {
                "enum": {"option1", "option2", "option3"}
            }
        }
    )
    
    # Test string constraints
    context = ValidationContext(
        command_name="test",
        arguments={"str_arg": "ab"}  # too short
    )
    result = rule.validate(context)
    assert not result.is_valid
    
    context.arguments["str_arg"] = "abcdefghijk"  # too long
    result = rule.validate(context)
    assert not result.is_valid
    
    context.arguments["str_arg"] = "ABC"  # invalid pattern
    result = rule.validate(context)
    assert not result.is_valid
    
    context.arguments["str_arg"] = "abc"  # valid
    result = rule.validate(context)
    assert result.is_valid
    
    # Test number constraints
    context.arguments = {"num_arg": -1}  # too small
    result = rule.validate(context)
    assert not result.is_valid
    
    context.arguments["num_arg"] = 101  # too large
    result = rule.validate(context)
    assert not result.is_valid
    
    context.arguments["num_arg"] = 50  # valid
    result = rule.validate(context)
    assert result.is_valid
    
    # Test enum constraints
    context.arguments = {"enum_arg": "invalid"}  # not in enum
    result = rule.validate(context)
    assert not result.is_valid
    
    context.arguments["enum_arg"] = "option1"  # valid
    result = rule.validate(context)
    assert result.is_valid 