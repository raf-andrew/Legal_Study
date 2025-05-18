"""Unit tests for role interface."""

import pytest
from typing import Any, Dict, Set

from ...security.rbac.role import Role, RoleRegistry, InMemoryRoleRegistry
from ...security.rbac.permission import Permission, InMemoryPermissionRegistry

@pytest.fixture
def test_permission() -> Permission:
    """Create test permission."""
    return Permission(
        name="test_permission",
        description="Test permission",
        resource="test_resource",
        actions={"read", "write"}
    )

@pytest.fixture
def another_permission() -> Permission:
    """Create another test permission."""
    return Permission(
        name="another_permission",
        description="Another test permission",
        resource="test_resource",
        actions={"delete"}
    )

@pytest.fixture
def permission_registry(test_permission, another_permission) -> InMemoryPermissionRegistry:
    """Create permission registry with test permissions."""
    registry = InMemoryPermissionRegistry()
    registry.register(test_permission)
    registry.register(another_permission)
    return registry

@pytest.fixture
def test_role() -> Role:
    """Create test role."""
    return Role(
        name="test_role",
        description="Test role",
        permissions={"test_permission"},
        metadata={"department": "test"}
    )

@pytest.fixture
def parent_role() -> Role:
    """Create parent role."""
    return Role(
        name="parent_role",
        description="Parent role",
        permissions={"another_permission"}
    )

@pytest.fixture
def child_role(parent_role) -> Role:
    """Create child role."""
    return Role(
        name="child_role",
        description="Child role",
        permissions={"test_permission"},
        parent_roles={parent_role.name}
    )

@pytest.fixture
def role_registry(permission_registry) -> RoleRegistry:
    """Create role registry."""
    return InMemoryRoleRegistry(permission_registry)

def test_role_initialization(test_role):
    """Test role initialization."""
    assert test_role.name == "test_role"
    assert test_role.description == "Test role"
    assert test_role.permissions == {"test_permission"}
    assert test_role.metadata == {"department": "test"}
    assert not test_role.parent_roles

def test_role_initialization_validation():
    """Test role initialization validation."""
    # Test missing name
    with pytest.raises(ValueError) as exc:
        Role(
            name="",
            description="Test",
            permissions={"test"}
        )
    assert "Role name is required" in str(exc.value)
    
    # Test missing permissions and parent roles
    with pytest.raises(ValueError) as exc:
        Role(
            name="test",
            description="Test",
            permissions=set()
        )
    assert "Role must have permissions or parent roles" in str(exc.value)

def test_role_has_permission(test_role):
    """Test role permission checking."""
    assert test_role.has_permission("test_permission")
    assert not test_role.has_permission("non_existent")

def test_role_to_dict(test_role):
    """Test role serialization."""
    data = test_role.to_dict()
    assert data["name"] == "test_role"
    assert data["description"] == "Test role"
    assert data["permissions"] == ["test_permission"]
    assert data["parent_roles"] == []
    assert data["metadata"] == {"department": "test"}

def test_registry_registration(role_registry, test_role):
    """Test role registration."""
    role_registry.register(test_role)
    assert test_role.name in role_registry._roles
    
    # Test duplicate registration
    with pytest.raises(ValueError) as exc:
        role_registry.register(test_role)
    assert "Role already registered" in str(exc.value)

def test_registry_registration_invalid_permission(role_registry):
    """Test role registration with invalid permission."""
    invalid_role = Role(
        name="invalid",
        description="Invalid",
        permissions={"non_existent"}
    )
    
    with pytest.raises(ValueError) as exc:
        role_registry.register(invalid_role)
    assert "Permission not found" in str(exc.value)

def test_registry_registration_invalid_parent(role_registry, test_role):
    """Test role registration with invalid parent role."""
    invalid_role = Role(
        name="invalid",
        description="Invalid",
        permissions={"test_permission"},
        parent_roles={"non_existent"}
    )
    
    with pytest.raises(ValueError) as exc:
        role_registry.register(invalid_role)
    assert "Parent role not found" in str(exc.value)

def test_registry_unregistration(role_registry, test_role):
    """Test role unregistration."""
    role_registry.register(test_role)
    role_registry.unregister(test_role.name)
    assert test_role.name not in role_registry._roles
    
    # Test unregistering non-existent role
    with pytest.raises(KeyError) as exc:
        role_registry.unregister("non_existent")
    assert "Role not registered" in str(exc.value)

def test_registry_unregistration_with_dependents(
    role_registry,
    parent_role,
    child_role
):
    """Test role unregistration with dependent roles."""
    role_registry.register(parent_role)
    role_registry.register(child_role)
    
    with pytest.raises(ValueError) as exc:
        role_registry.unregister(parent_role.name)
    assert "Cannot unregister role with dependent roles" in str(exc.value)

def test_registry_get_role(role_registry, test_role):
    """Test getting role from registry."""
    role_registry.register(test_role)
    retrieved = role_registry.get(test_role.name)
    assert retrieved == test_role
    
    # Test getting non-existent role
    with pytest.raises(KeyError) as exc:
        role_registry.get("non_existent")
    assert "Role not registered" in str(exc.value)

def test_registry_list_roles(role_registry, test_role, parent_role):
    """Test listing roles from registry."""
    # Test empty registry
    assert len(role_registry.list()) == 0
    
    # Test single role
    role_registry.register(test_role)
    roles = role_registry.list()
    assert len(roles) == 1
    assert test_role in roles
    
    # Test multiple roles
    role_registry.register(parent_role)
    roles = role_registry.list()
    assert len(roles) == 2
    assert test_role in roles
    assert parent_role in roles

def test_registry_get_effective_permissions(
    role_registry,
    parent_role,
    child_role
):
    """Test getting effective permissions."""
    role_registry.register(parent_role)
    role_registry.register(child_role)
    
    # Test child role permissions
    permissions = role_registry.get_effective_permissions(child_role.name)
    assert permissions == {"test_permission", "another_permission"}
    
    # Test parent role permissions
    permissions = role_registry.get_effective_permissions(parent_role.name)
    assert permissions == {"another_permission"}
    
    # Test non-existent role
    with pytest.raises(KeyError) as exc:
        role_registry.get_effective_permissions("non_existent")
    assert "Role not registered" in str(exc.value)

def test_registry_circular_inheritance(role_registry):
    """Test handling of circular role inheritance."""
    # Create roles with circular dependency
    role1 = Role(
        name="role1",
        description="Role 1",
        permissions={"test_permission"},
        parent_roles={"role2"}
    )
    role2 = Role(
        name="role2",
        description="Role 2",
        permissions={"another_permission"},
        parent_roles={"role1"}
    )
    
    # First role should register
    role_registry.register(role1)
    
    # Second role should fail due to circular dependency
    with pytest.raises(ValueError) as exc:
        role_registry.register(role2)
    assert "Parent role not found" in str(exc.value) 