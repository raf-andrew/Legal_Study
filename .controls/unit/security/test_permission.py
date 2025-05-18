"""Unit tests for permission interface."""

import pytest
from typing import Any, Dict, Set

from ...security.rbac.permission import (
    Permission,
    PermissionRegistry,
    InMemoryPermissionRegistry
)

@pytest.fixture
def test_permission() -> Permission:
    """Create test permission."""
    return Permission(
        name="test_permission",
        description="Test permission",
        resource="test_resource",
        actions={"read", "write"},
        conditions={"owner": "test_user"}
    )

@pytest.fixture
def test_permission_no_conditions() -> Permission:
    """Create test permission without conditions."""
    return Permission(
        name="test_permission_no_conditions",
        description="Test permission without conditions",
        resource="test_resource",
        actions={"read", "write"}
    )

@pytest.fixture
def permission_registry() -> PermissionRegistry:
    """Create permission registry."""
    return InMemoryPermissionRegistry()

def test_permission_initialization(test_permission):
    """Test permission initialization."""
    assert test_permission.name == "test_permission"
    assert test_permission.description == "Test permission"
    assert test_permission.resource == "test_resource"
    assert test_permission.actions == {"read", "write"}
    assert test_permission.conditions == {"owner": "test_user"}

def test_permission_initialization_validation():
    """Test permission initialization validation."""
    # Test missing name
    with pytest.raises(ValueError) as exc:
        Permission(
            name="",
            description="Test",
            resource="test",
            actions={"read"}
        )
    assert "Permission name is required" in str(exc.value)
    
    # Test missing resource
    with pytest.raises(ValueError) as exc:
        Permission(
            name="test",
            description="Test",
            resource="",
            actions={"read"}
        )
    assert "Permission resource is required" in str(exc.value)
    
    # Test missing actions
    with pytest.raises(ValueError) as exc:
        Permission(
            name="test",
            description="Test",
            resource="test",
            actions=set()
        )
    assert "Permission actions are required" in str(exc.value)

def test_permission_allows_with_conditions(test_permission):
    """Test permission action checking with conditions."""
    # Test allowed action with matching conditions
    assert test_permission.allows("read", owner="test_user")
    assert test_permission.allows("write", owner="test_user")
    
    # Test allowed action with non-matching conditions
    assert not test_permission.allows("read", owner="other_user")
    assert not test_permission.allows("write", owner="other_user")
    
    # Test disallowed action
    assert not test_permission.allows("delete", owner="test_user")

def test_permission_allows_without_conditions(test_permission_no_conditions):
    """Test permission action checking without conditions."""
    # Test allowed actions
    assert test_permission_no_conditions.allows("read")
    assert test_permission_no_conditions.allows("write")
    
    # Test disallowed action
    assert not test_permission_no_conditions.allows("delete")
    
    # Test with unnecessary context
    assert test_permission_no_conditions.allows("read", owner="test_user")

def test_permission_condition_evaluation(test_permission):
    """Test permission condition evaluation."""
    # Test matching conditions
    assert test_permission._evaluate_conditions({"owner": "test_user"})
    
    # Test non-matching conditions
    assert not test_permission._evaluate_conditions({"owner": "other_user"})
    
    # Test missing condition
    assert not test_permission._evaluate_conditions({})
    
    # Test extra conditions
    assert test_permission._evaluate_conditions({
        "owner": "test_user",
        "extra": "value"
    })

def test_permission_to_dict(test_permission):
    """Test permission serialization."""
    data = test_permission.to_dict()
    assert data["name"] == "test_permission"
    assert data["description"] == "Test permission"
    assert data["resource"] == "test_resource"
    assert set(data["actions"]) == {"read", "write"}
    assert data["conditions"] == {"owner": "test_user"}

def test_registry_registration(permission_registry, test_permission):
    """Test permission registration."""
    permission_registry.register(test_permission)
    assert test_permission.name in permission_registry._permissions
    
    # Test duplicate registration
    with pytest.raises(ValueError) as exc:
        permission_registry.register(test_permission)
    assert "Permission already registered" in str(exc.value)

def test_registry_unregistration(permission_registry, test_permission):
    """Test permission unregistration."""
    permission_registry.register(test_permission)
    permission_registry.unregister(test_permission.name)
    assert test_permission.name not in permission_registry._permissions
    
    # Test unregistering non-existent permission
    with pytest.raises(KeyError) as exc:
        permission_registry.unregister("non_existent")
    assert "Permission not registered" in str(exc.value)

def test_registry_get_permission(permission_registry, test_permission):
    """Test getting permission from registry."""
    permission_registry.register(test_permission)
    retrieved = permission_registry.get(test_permission.name)
    assert retrieved == test_permission
    
    # Test getting non-existent permission
    with pytest.raises(KeyError) as exc:
        permission_registry.get("non_existent")
    assert "Permission not registered" in str(exc.value)

def test_registry_list_permissions(
    permission_registry,
    test_permission,
    test_permission_no_conditions
):
    """Test listing permissions from registry."""
    # Test empty registry
    assert len(permission_registry.list()) == 0
    
    # Test single permission
    permission_registry.register(test_permission)
    permissions = permission_registry.list()
    assert len(permissions) == 1
    assert test_permission in permissions
    
    # Test multiple permissions
    permission_registry.register(test_permission_no_conditions)
    permissions = permission_registry.list()
    assert len(permissions) == 2
    assert test_permission in permissions
    assert test_permission_no_conditions in permissions 