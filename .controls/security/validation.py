"""Security validation interface for command execution."""

import abc
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Type, Union
from datetime import datetime

@dataclass
class ValidationContext:
    """Context for validation execution."""
    
    command_name: str
    arguments: Dict[str, Any]
    user_id: Optional[str] = None
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    environment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ValidationResult:
    """Result of validation execution."""
    
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ValidationRule(abc.ABC):
    """Base class for validation rules."""
    
    def __init__(self, name: str, description: str):
        """Initialize validation rule.
        
        Args:
            name: Rule name
            description: Rule description
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"validation.rule.{name}")
    
    @abc.abstractmethod
    def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate context against rule.
        
        Args:
            context: Validation context
            
        Returns:
            Validation result
        """
        raise NotImplementedError("Validation rules must implement validate")

class ArgumentValidationRule(ValidationRule):
    """Rule for validating command arguments."""
    
    def __init__(
        self,
        name: str,
        description: str,
        required_args: Set[str],
        arg_types: Dict[str, Type],
        arg_constraints: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """Initialize argument validation rule.
        
        Args:
            name: Rule name
            description: Rule description
            required_args: Set of required argument names
            arg_types: Mapping of argument names to expected types
            arg_constraints: Optional mapping of argument names to constraints
        """
        super().__init__(name, description)
        self.required_args = required_args
        self.arg_types = arg_types
        self.arg_constraints = arg_constraints or {}
    
    def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate command arguments."""
        errors = []
        warnings = []
        
        # Check required arguments
        for arg_name in self.required_args:
            if arg_name not in context.arguments:
                errors.append(f"Missing required argument: {arg_name}")
        
        # Check argument types
        for arg_name, arg_value in context.arguments.items():
            if arg_name in self.arg_types:
                expected_type = self.arg_types[arg_name]
                if not isinstance(arg_value, expected_type):
                    errors.append(
                        f"Invalid type for argument {arg_name}: "
                        f"expected {expected_type.__name__}, "
                        f"got {type(arg_value).__name__}"
                    )
        
        # Check argument constraints
        for arg_name, constraints in self.arg_constraints.items():
            if arg_name in context.arguments:
                arg_value = context.arguments[arg_name]
                for constraint_name, constraint_value in constraints.items():
                    if not self._check_constraint(
                        arg_value,
                        constraint_name,
                        constraint_value
                    ):
                        errors.append(
                            f"Constraint violation for argument {arg_name}: "
                            f"{constraint_name} = {constraint_value}"
                        )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _check_constraint(
        self,
        value: Any,
        constraint_name: str,
        constraint_value: Any
    ) -> bool:
        """Check if value satisfies constraint.
        
        Args:
            value: Value to check
            constraint_name: Name of constraint
            constraint_value: Constraint value
            
        Returns:
            True if constraint is satisfied, False otherwise
        """
        if constraint_name == "min":
            return value >= constraint_value
        elif constraint_name == "max":
            return value <= constraint_value
        elif constraint_name == "min_length":
            return len(value) >= constraint_value
        elif constraint_name == "max_length":
            return len(value) <= constraint_value
        elif constraint_name == "pattern":
            import re
            return bool(re.match(constraint_value, str(value)))
        elif constraint_name == "enum":
            return value in constraint_value
        else:
            self.logger.warning(f"Unknown constraint: {constraint_name}")
            return True

class PermissionValidationRule(ValidationRule):
    """Rule for validating command permissions."""
    
    def __init__(
        self,
        name: str,
        description: str,
        required_permissions: Set[str],
        required_roles: Optional[Set[str]] = None
    ):
        """Initialize permission validation rule.
        
        Args:
            name: Rule name
            description: Rule description
            required_permissions: Set of required permission names
            required_roles: Optional set of required role names
        """
        super().__init__(name, description)
        self.required_permissions = required_permissions
        self.required_roles = required_roles or set()
    
    def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate command permissions."""
        errors = []
        warnings = []
        
        # Check required permissions
        missing_permissions = self.required_permissions - context.permissions
        if missing_permissions:
            errors.append(
                f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        
        # Check required roles
        if self.required_roles:
            missing_roles = self.required_roles - context.roles
            if missing_roles:
                errors.append(
                    f"Missing required roles: {', '.join(missing_roles)}"
                )
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

class ValidationPipeline:
    """Pipeline for executing multiple validation rules."""
    
    def __init__(self):
        """Initialize validation pipeline."""
        self.rules: List[ValidationRule] = []
        self.logger = logging.getLogger("validation.pipeline")
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add validation rule to pipeline.
        
        Args:
            rule: Validation rule to add
        """
        self.rules.append(rule)
    
    def validate(self, context: ValidationContext) -> ValidationResult:
        """Execute validation pipeline.
        
        Args:
            context: Validation context
            
        Returns:
            Combined validation result
        """
        all_errors = []
        all_warnings = []
        metadata = {}
        
        for rule in self.rules:
            self.logger.debug(f"Executing validation rule: {rule.name}")
            result = rule.validate(context)
            
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            metadata[rule.name] = {
                "is_valid": result.is_valid,
                "errors": result.errors,
                "warnings": result.warnings
            }
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings,
            metadata=metadata
        ) 