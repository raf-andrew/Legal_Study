"""Unit tests for health check registry."""

import pytest
from typing import Dict, List, Set

from ..commands.health.base import (
    HealthCheck,
    HealthCheckResult,
    HealthCheckDependencyError
)
from ..commands.health.registry import HealthCheckRegistry
from .test_health_check import TestHealthCheck

@pytest.fixture
def registry() -> HealthCheckRegistry:
    """Create health check registry."""
    return HealthCheckRegistry()

@pytest.fixture
def test_checks() -> List[TestHealthCheck]:
    """Create test health checks."""
    return [
        TestHealthCheck(name="check1", check_type="service"),
        TestHealthCheck(name="check2", check_type="service"),
        TestHealthCheck(name="check3", check_type="database", should_pass=False),
        TestHealthCheck(name="check4", check_type="database"),
        TestHealthCheck(name="check5", check_type="api")
    ]

def test_registry_initialization(registry):
    """Test registry initialization."""
    assert isinstance(registry._checks, dict)
    assert len(registry._checks) == 0
    assert isinstance(registry.logger, logging.Logger)

def test_check_registration(registry, test_checks):
    """Test check registration."""
    # Register checks
    for check in test_checks:
        registry.register(check)
        assert check.name in registry._checks
    
    # Try to register duplicate
    with pytest.raises(ValueError) as exc:
        registry.register(test_checks[0])
    assert "already registered" in str(exc.value)

def test_check_unregistration(registry, test_checks):
    """Test check unregistration."""
    # Register checks
    for check in test_checks:
        registry.register(check)
    
    # Unregister check
    registry.unregister(test_checks[0].name)
    assert test_checks[0].name not in registry._checks
    
    # Try to unregister non-existent check
    with pytest.raises(KeyError) as exc:
        registry.unregister("non_existent")
    assert "not registered" in str(exc.value)

def test_check_unregistration_with_dependencies(registry, test_checks):
    """Test check unregistration with dependencies."""
    # Register checks with dependency
    registry.register(test_checks[0])  # check1
    registry.register(test_checks[1])  # check2
    test_checks[1].add_dependency(test_checks[0].name)
    
    # Try to unregister dependency
    with pytest.raises(ValueError) as exc:
        registry.unregister(test_checks[0].name)
    assert "Cannot unregister check with dependencies" in str(exc.value)

def test_get_check(registry, test_checks):
    """Test getting registered check."""
    # Register check
    registry.register(test_checks[0])
    
    # Get check
    check = registry.get_check(test_checks[0].name)
    assert check == test_checks[0]
    
    # Try to get non-existent check
    with pytest.raises(KeyError) as exc:
        registry.get_check("non_existent")
    assert "not registered" in str(exc.value)

def test_list_checks(registry, test_checks):
    """Test listing registered checks."""
    # Register checks
    for check in test_checks:
        registry.register(check)
    
    # List all checks
    checks = registry.list_checks()
    assert len(checks) == len(test_checks)
    assert all(isinstance(check, HealthCheck) for check in checks)
    
    # List checks by type
    service_checks = registry.list_checks("service")
    assert len(service_checks) == 2
    assert all(check.check_type == "service" for check in service_checks)
    
    database_checks = registry.list_checks("database")
    assert len(database_checks) == 2
    assert all(check.check_type == "database" for check in database_checks)

def test_get_dependent_checks(registry, test_checks):
    """Test getting dependent checks."""
    # Register checks with dependencies
    registry.register(test_checks[0])  # check1
    registry.register(test_checks[1])  # check2
    registry.register(test_checks[2])  # check3
    
    test_checks[1].add_dependency(test_checks[0].name)
    test_checks[2].add_dependency(test_checks[0].name)
    
    # Get dependent checks
    dependents = registry._get_dependent_checks(test_checks[0].name)
    assert len(dependents) == 2
    assert test_checks[1].name in dependents
    assert test_checks[2].name in dependents

@pytest.mark.asyncio
async def test_run_check(registry, test_checks):
    """Test running single check."""
    # Register check
    registry.register(test_checks[0])
    
    # Run check
    result = await registry.run_check(test_checks[0].name)
    assert isinstance(result, HealthCheckResult)
    assert result.is_healthy

@pytest.mark.asyncio
async def test_run_check_with_dependencies(registry, test_checks):
    """Test running check with dependencies."""
    # Register checks with dependency
    registry.register(test_checks[0])  # check1 (healthy)
    registry.register(test_checks[1])  # check2 (depends on check1)
    test_checks[1].add_dependency(test_checks[0].name)
    
    # Run check with healthy dependency
    result = await registry.run_check(test_checks[1].name)
    assert result.is_healthy
    
    # Register failing dependency
    registry.unregister(test_checks[0].name)
    registry.register(test_checks[2])  # check3 (unhealthy)
    test_checks[1].add_dependency(test_checks[2].name)
    
    # Run check with failing dependency
    with pytest.raises(HealthCheckDependencyError) as exc:
        await registry.run_check(test_checks[1].name)
    assert "Dependency check failed" in str(exc.value)

@pytest.mark.asyncio
async def test_run_all_checks(registry, test_checks):
    """Test running all checks."""
    # Register checks
    for check in test_checks:
        registry.register(check)
    
    # Run all checks
    results = await registry.run_all_checks()
    assert len(results) == len(test_checks)
    assert all(isinstance(result, HealthCheckResult) for result in results.values())
    
    # Verify results
    assert results[test_checks[0].name].is_healthy  # check1 (healthy)
    assert results[test_checks[1].name].is_healthy  # check2 (healthy)
    assert not results[test_checks[2].name].is_healthy  # check3 (unhealthy)
    assert results[test_checks[3].name].is_healthy  # check4 (healthy)
    assert results[test_checks[4].name].is_healthy  # check5 (healthy)
    
    # Run checks by type
    service_results = await registry.run_all_checks("service")
    assert len(service_results) == 2
    assert all(result.is_healthy for result in service_results.values())
    
    database_results = await registry.run_all_checks("database")
    assert len(database_results) == 2
    assert not all(result.is_healthy for result in database_results.values()) 