"""Unit tests for security health check."""

import os
import jwt
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any

from ..commands.health.checks.security import SecurityCheck
from ...mocks.registry import MockServiceRegistry

@pytest.fixture
def mock_registry() -> MagicMock:
    """Create mock service registry."""
    registry = MagicMock(spec=MockServiceRegistry)
    registry.list_services.return_value = ["api", "database", "cache"]
    return registry

@pytest.fixture
def security_check(mock_registry) -> SecurityCheck:
    """Create security check instance."""
    return SecurityCheck(mock_registry)

@pytest.fixture
def mock_auth_service() -> MagicMock:
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

def test_security_check_initialization(security_check):
    """Test security check initialization."""
    assert security_check.name == "security"
    assert isinstance(security_check.registry, MagicMock)

def test_security_check_all_secure(security_check, mock_registry, mock_auth_service):
    """Test security check with all components secure."""
    # Mock services
    mock_service = MagicMock()
    mock_service.get_security_config.return_value = {"encryption": True}
    mock_service.check_security.return_value = {"secure": True}
    
    def get_service(name):
        return mock_auth_service if name == "auth" else mock_service
    
    mock_registry.get_service.side_effect = get_service
    
    # Mock environment variables
    with patch.dict(os.environ, {
        "SSL_CERT_FILE": "cert.pem",
        "SSL_KEY_FILE": "key.pem",
        "JWT_SECRET": "secret"
    }):
        # Mock SSL context
        with patch("ssl.create_default_context") as mock_context:
            with patch("ssl.PEM_cert_to_DER_cert") as mock_pem_to_der:
                with patch("ssl.DER_cert_to_PEM_cert") as mock_der_to_pem:
                    result = security_check.execute()
    
    assert result["status"] == "healthy"
    assert result["details"]["healthy"] is True
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

def test_check_authentication(security_check, mock_auth_service):
    """Test authentication check."""
    result = security_check._check_authentication(mock_auth_service)
    assert result["healthy"] is True
    assert "methods" in result
    assert len(result["methods"]) == 2
    assert all(
        method["status"] == "active"
        for method in result["methods"].values()
    )

def test_check_authentication_not_running(security_check, mock_auth_service):
    """Test authentication check with service not running."""
    mock_auth_service.is_running.return_value = False
    
    result = security_check._check_authentication(mock_auth_service)
    assert result["healthy"] is False
    assert "Authentication service not running" in result["error"]

def test_check_authorization(security_check, mock_auth_service):
    """Test authorization check."""
    result = security_check._check_authorization(mock_auth_service)
    assert result["rbac_enabled"] is True
    assert "roles" in result
    assert len(result["roles"]) == 2
    assert all(
        role["status"] == "active"
        for role in result["roles"].values()
    )

def test_check_authorization_rbac_disabled(security_check, mock_auth_service):
    """Test authorization check with RBAC disabled."""
    mock_auth_service.is_rbac_enabled.return_value = False
    
    result = security_check._check_authorization(mock_auth_service)
    assert result["rbac_enabled"] is False
    assert "RBAC not enabled" in result["error"]

def test_check_ssl(security_check):
    """Test SSL check."""
    with patch.dict(os.environ, {
        "SSL_CERT_FILE": "cert.pem",
        "SSL_KEY_FILE": "key.pem"
    }):
        with patch("ssl.create_default_context") as mock_context:
            with patch("ssl.PEM_cert_to_DER_cert") as mock_pem_to_der:
                with patch("ssl.DER_cert_to_PEM_cert") as mock_der_to_pem:
                    result = security_check._check_ssl()
    
    assert result["healthy"] is True
    assert result["certificate"]["valid"] is True

def test_check_ssl_not_configured(security_check):
    """Test SSL check without configuration."""
    with patch.dict(os.environ, {}, clear=True):
        result = security_check._check_ssl()
    
    assert result["healthy"] is False
    assert "SSL certificate not configured" in result["error"]

def test_check_tokens(security_check, mock_auth_service):
    """Test token check."""
    with patch.dict(os.environ, {"JWT_SECRET": "secret"}):
        with patch("jwt.decode") as mock_decode:
            result = security_check._check_tokens(mock_auth_service)
    
    assert result["healthy"] is True
    assert result["jwt_configured"] is True
    assert result["token_validation"] is True

def test_check_tokens_not_configured(security_check, mock_auth_service):
    """Test token check without configuration."""
    with patch.dict(os.environ, {}, clear=True):
        result = security_check._check_tokens(mock_auth_service)
    
    assert result["healthy"] is False
    assert "JWT secret not configured" in result["error"]

def test_check_service_security(security_check, mock_registry):
    """Test service security check."""
    # Mock services
    mock_service = MagicMock()
    mock_service.get_security_config.return_value = {"encryption": True}
    mock_service.check_security.return_value = {"secure": True}
    mock_registry.get_service.return_value = mock_service
    
    result = security_check._check_service_security()
    assert result["healthy"] is True
    assert "services" in result
    assert all(
        service["status"] == "secure"
        for service in result["services"].values()
    )

def test_get_security_report(security_check, mock_registry, mock_auth_service):
    """Test security report generation."""
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
                        report = security_check.get_security_report()
    
    assert report["status"] == "secure"
    assert report["total_issues"] == 0
    assert all(count == 0 for count in report["issues"].values())

def test_get_service_security(security_check, mock_registry):
    """Test getting service security status."""
    # Mock service
    mock_service = MagicMock()
    mock_service.get_security_config.return_value = {"encryption": True}
    mock_service.check_security.return_value = {"secure": True}
    mock_registry.get_service.return_value = mock_service
    
    result = security_check.get_service_security("api")
    assert result["status"] == "secure"
    assert "config" in result
    assert "details" in result 