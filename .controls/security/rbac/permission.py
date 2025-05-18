"""Permission interface for role-based access control."""

import abc
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

@dataclass(frozen=True)
class Permission:
    """Permission definition."""
    
    name: str
    description: str
    resource: str
    actions: Set[str]
    conditions: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate permission after initialization."""
        if not self.name:
            raise ValueError("Permission name is required")
        if not self.resource:
            raise ValueError("Permission resource is required")
        if not self.actions:
            raise ValueError("Permission actions are required")

    def allows(self, action: str, **context: Any) -> bool:
        """Check if permission allows action.
        
        Args:
            action: Action to check
            **context: Additional context for condition evaluation
            
        Returns:
            True if action is allowed, False otherwise
        """
        if action not in self.actions:
            return False
            
        if not self.conditions:
            return True
            
        return self._evaluate_conditions(context)
    
    def _evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """Evaluate permission conditions.
        
        Args:
            context: Context for condition evaluation
            
        Returns:
            True if conditions are met, False otherwise
        """
        if not self.conditions:
            return True
            
        # Simple condition evaluation - in real implementation,
        # this would be more sophisticated
        for key, value in self.conditions.items():
            if key not in context or context[key] != value:
                return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert permission to dictionary.
        
        Returns:
            Dictionary representation of permission
        """
        return {
            "name": self.name,
            "description": self.description,
            "resource": self.resource,
            "actions": list(self.actions),
            "conditions": self.conditions
        }

class PermissionRegistry(abc.ABC):
    """Interface for permission registry."""
    
    @abc.abstractmethod
    def register(self, permission: Permission) -> None:
        """Register a permission.
        
        Args:
            permission: Permission to register
            
        Raises:
            ValueError: If permission is already registered
        """
        raise NotImplementedError("Permission registry must implement register")
    
    @abc.abstractmethod
    def unregister(self, name: str) -> None:
        """Unregister a permission.
        
        Args:
            name: Name of permission to unregister
            
        Raises:
            KeyError: If permission is not registered
        """
        raise NotImplementedError("Permission registry must implement unregister")
    
    @abc.abstractmethod
    def get(self, name: str) -> Permission:
        """Get a permission.
        
        Args:
            name: Name of permission to get
            
        Returns:
            Permission instance
            
        Raises:
            KeyError: If permission is not registered
        """
        raise NotImplementedError("Permission registry must implement get")
    
    @abc.abstractmethod
    def list(self) -> List[Permission]:
        """List all registered permissions.
        
        Returns:
            List of registered permissions
        """
        raise NotImplementedError("Permission registry must implement list")

class InMemoryPermissionRegistry(PermissionRegistry):
    """In-memory implementation of permission registry."""
    
    def __init__(self):
        """Initialize registry."""
        self._permissions: Dict[str, Permission] = {}
    
    def register(self, permission: Permission) -> None:
        """Register a permission."""
        if permission.name in self._permissions:
            raise ValueError(f"Permission already registered: {permission.name}")
        self._permissions[permission.name] = permission
    
    def unregister(self, name: str) -> None:
        """Unregister a permission."""
        if name not in self._permissions:
            raise KeyError(f"Permission not registered: {name}")
        del self._permissions[name]
    
    def get(self, name: str) -> Permission:
        """Get a permission."""
        if name not in self._permissions:
            raise KeyError(f"Permission not registered: {name}")
        return self._permissions[name]
    
    def list(self) -> List[Permission]:
        """List all registered permissions."""
        return list(self._permissions.values()) 