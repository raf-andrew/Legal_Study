"""Role interface for role-based access control."""

import abc
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .permission import Permission, PermissionRegistry

@dataclass(frozen=True)
class Role:
    """Role definition."""
    
    name: str
    description: str
    permissions: Set[str]  # Permission names
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_roles: Set[str] = field(default_factory=set)  # Parent role names

    def __post_init__(self):
        """Validate role after initialization."""
        if not self.name:
            raise ValueError("Role name is required")
        if not self.permissions and not self.parent_roles:
            raise ValueError("Role must have permissions or parent roles")

    def has_permission(self, permission_name: str) -> bool:
        """Check if role has permission.
        
        Args:
            permission_name: Name of permission to check
            
        Returns:
            True if role has permission, False otherwise
        """
        return permission_name in self.permissions

    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary.
        
        Returns:
            Dictionary representation of role
        """
        return {
            "name": self.name,
            "description": self.description,
            "permissions": list(self.permissions),
            "parent_roles": list(self.parent_roles),
            "metadata": self.metadata
        }

class RoleRegistry(abc.ABC):
    """Interface for role registry."""
    
    @abc.abstractmethod
    def register(self, role: Role) -> None:
        """Register a role.
        
        Args:
            role: Role to register
            
        Raises:
            ValueError: If role is already registered
            ValueError: If parent role does not exist
        """
        raise NotImplementedError("Role registry must implement register")
    
    @abc.abstractmethod
    def unregister(self, name: str) -> None:
        """Unregister a role.
        
        Args:
            name: Name of role to unregister
            
        Raises:
            KeyError: If role is not registered
            ValueError: If role has dependent roles
        """
        raise NotImplementedError("Role registry must implement unregister")
    
    @abc.abstractmethod
    def get(self, name: str) -> Role:
        """Get a role.
        
        Args:
            name: Name of role to get
            
        Returns:
            Role instance
            
        Raises:
            KeyError: If role is not registered
        """
        raise NotImplementedError("Role registry must implement get")
    
    @abc.abstractmethod
    def list(self) -> List[Role]:
        """List all registered roles.
        
        Returns:
            List of registered roles
        """
        raise NotImplementedError("Role registry must implement list")
    
    @abc.abstractmethod
    def get_effective_permissions(self, role_name: str) -> Set[str]:
        """Get effective permissions for role including inherited permissions.
        
        Args:
            role_name: Name of role to get permissions for
            
        Returns:
            Set of permission names
            
        Raises:
            KeyError: If role is not registered
        """
        raise NotImplementedError("Role registry must implement get_effective_permissions")

class InMemoryRoleRegistry(RoleRegistry):
    """In-memory implementation of role registry."""
    
    def __init__(self, permission_registry: PermissionRegistry):
        """Initialize registry.
        
        Args:
            permission_registry: Permission registry for validation
        """
        self._roles: Dict[str, Role] = {}
        self._permission_registry = permission_registry
        self._dependent_roles: Dict[str, Set[str]] = {}  # role -> dependent roles
    
    def register(self, role: Role) -> None:
        """Register a role."""
        # Check for existing role
        if role.name in self._roles:
            raise ValueError(f"Role already registered: {role.name}")
        
        # Validate permissions
        for permission_name in role.permissions:
            try:
                self._permission_registry.get(permission_name)
            except KeyError:
                raise ValueError(f"Permission not found: {permission_name}")
        
        # Validate parent roles
        for parent_name in role.parent_roles:
            if parent_name not in self._roles:
                raise ValueError(f"Parent role not found: {parent_name}")
            
            # Update dependent roles
            if parent_name not in self._dependent_roles:
                self._dependent_roles[parent_name] = set()
            self._dependent_roles[parent_name].add(role.name)
        
        self._roles[role.name] = role
    
    def unregister(self, name: str) -> None:
        """Unregister a role."""
        if name not in self._roles:
            raise KeyError(f"Role not registered: {name}")
        
        # Check for dependent roles
        if name in self._dependent_roles and self._dependent_roles[name]:
            dependent_roles = ", ".join(self._dependent_roles[name])
            raise ValueError(
                f"Cannot unregister role with dependent roles: {dependent_roles}"
            )
        
        # Remove role from dependent roles tracking
        for dependents in self._dependent_roles.values():
            dependents.discard(name)
        if name in self._dependent_roles:
            del self._dependent_roles[name]
        
        del self._roles[name]
    
    def get(self, name: str) -> Role:
        """Get a role."""
        if name not in self._roles:
            raise KeyError(f"Role not registered: {name}")
        return self._roles[name]
    
    def list(self) -> List[Role]:
        """List all registered roles."""
        return list(self._roles.values())
    
    def get_effective_permissions(self, role_name: str) -> Set[str]:
        """Get effective permissions for role."""
        if role_name not in self._roles:
            raise KeyError(f"Role not registered: {role_name}")
        
        permissions = set()
        visited = set()
        
        def collect_permissions(name: str) -> None:
            """Recursively collect permissions from role and parents."""
            if name in visited:
                return
            visited.add(name)
            
            role = self._roles[name]
            permissions.update(role.permissions)
            
            for parent_name in role.parent_roles:
                collect_permissions(parent_name)
        
        collect_permissions(role_name)
        return permissions 