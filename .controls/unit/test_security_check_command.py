"""Unit tests for security health check command."""

import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from ..commands.health.checks.security import SecurityCheck
from ..mocks.registry import MockServiceRegistry

@pytest.fixture
def mock_registry():
    """Create mock service registry."""
    registry = MagicMock(spec=MockServiceRegistry)
    registry.list_services.return_value = ["api", "database", "cache"]
    return registry

@pytest.fixture
def mock_auth_service():
    """Create mock authentication service."""
    auth_service = MagicMock()
    auth_service.is_running.return_value = True
    auth_service.list_auth_methods.return_value = ["jwt", "basic"]
    auth_service.check_auth_method.return_value = {"status": "ok"}
    auth_service.is_rbac_enabled.return_value = True
    auth_service.list_roles.return_value = ["admin", "user"]
    auth_service.get_role_permissions.return_value = ["read", "write"]
    auth_service.generate_token.return_value = "test.token.123"
    return auth_service

@pytest.fixture
def security_check(mock_registry):
    """Create security check instance."""
    return SecurityCheck(mock_registry)

def test_security_check_initialization(security_check):
    """Test security check initialization."""
    assert security_check.name == "security"
    assert security_check.description == "Check security configuration and status"
    assert isinstance(security_check.registry, MagicMock)

def test_security_check_validation(security_check):
    """Test security check validation."""
    assert security_check.validate() is None
    assert security_check.validate(services=["api"]) is None
    assert security_check.validate(services="api") == "Services must be a list"

def test_security_check_execution(security_check, mock_registry, mock_auth_service):
    """Test security check execution."""
    # Mock services
    mock_service = MagicMock()
    mock_service.get_security_config.return_value = {"encryption": True}
    mock_service.check_security.return_value = {"secure": True}
    
    def get_service(name):
        return mock_auth_service if name == "auth" else mock_service
    
    mock_registry.get_service.side_effect = get_service
    
    # Mock environment
    with patch.dict(os.environ, {
        "SSL_CERT_FILE": "cert.pem",
        "SSL_KEY_FILE": "key.pem",
        "JWT_SECRET": "secret"
    }):
        # Mock SSL
        with patch("ssl.create_default_context"):
            with patch("ssl.PEM_cert_to_DER_cert"):
                with patch("ssl.DER_cert_to_PEM_cert"):
                    # Mock JWT
                    with patch("jwt.decode"):
                        result = security_check.execute()
    
    assert result["status"] == "healthy"
    assert "timestamp" in result
    assert result["details"]["authentication"]["healthy"] is True
    assert result["details"]["ssl"]["healthy"] is True
    assert result["details"]["tokens"]["healthy"] is True
    assert result["details"]["services"]["healthy"] is True

def test_security_check_no_auth_service(security_check, mock_registry):
    """Test security check without authentication service."""
    mock_registry.get_service.return_value = None
    
    result = security_check.execute()
    assert result["status"] == "error"
    assert "Authentication service not available" in result["error"]

def test_security_check_auth_not_running(security_check, mock_registry, mock_auth_service):
    """Test security check with authentication service not running."""
    mock_auth_service.is_running.return_value = False
    mock_registry.get_service.return_value = mock_auth_service
    
    result = security_check.execute()
    assert result["status"] == "unhealthy"
    assert result["details"]["authentication"]["healthy"] is False

def test_security_check_ssl_not_configured(security_check, mock_registry, mock_auth_service):
    """Test security check without SSL configuration."""
    mock_registry.get_service.return_value = mock_auth_service
    
    with patch.dict(os.environ, {}, clear=True):
        result = security_check.execute()
    
    assert result["status"] == "unhealthy"
    assert result["details"]["ssl"]["healthy"] is False
    assert "SSL certificate not configured" in result["details"]["ssl"]["error"]

def test_security_check_jwt_not_configured(security_check, mock_registry, mock_auth_service):
    """Test security check without JWT configuration."""
    mock_registry.get_service.return_value = mock_auth_service
    
    with patch.dict(os.environ, {
        "SSL_CERT_FILE": "cert.pem",
        "SSL_KEY_FILE": "key.pem"
    }):
        result = security_check.execute()
    
    assert result["status"] == "unhealthy"
    assert result["details"]["tokens"]["healthy"] is False
    assert "JWT secret not configured" in result["details"]["tokens"]["error"]

def test_security_check_service_error(security_check, mock_registry, mock_auth_service):
    """Test security check with service error."""
    # Mock services
    mock_service = MagicMock()
    mock_service.get_security_config.side_effect = Exception("Service error")
    
    def get_service(name):
        return mock_auth_service if name == "auth" else mock_service
    
    mock_registry.get_service.side_effect = get_service
    
    # Mock environment
    with patch.dict(os.environ, {
        "SSL_CERT_FILE": "cert.pem",
        "SSL_KEY_FILE": "key.pem",
        "JWT_SECRET": "secret"
    }):
        result = security_check.execute()
    
    assert result["status"] == "unhealthy"
    assert result["details"]["services"]["healthy"] is False
    assert any(
        service["status"] == "error"
        for service in result["details"]["services"]["services"].values()
    ) 