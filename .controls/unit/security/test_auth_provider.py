"""Unit tests for authentication provider interface."""

import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ...security.auth.provider import (
    AuthenticationContext,
    AuthenticationProvider,
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError
)

class MockAuthProvider(AuthenticationProvider):
    """Mock authentication provider for testing."""
    
    def __init__(self):
        """Initialize mock provider."""
        self.valid_credentials = {
            "username": "test_user",
            "password": "test_pass"
        }
        self.valid_token = "valid.test.token"
        self.expired_token = "expired.test.token"
        self.revoked_tokens = set()
    
    def authenticate(self, **credentials: Any) -> AuthenticationContext:
        """Mock authentication implementation."""
        if (
            credentials.get("username") == self.valid_credentials["username"]
            and credentials.get("password") == self.valid_credentials["password"]
        ):
            return AuthenticationContext(
                user_id="test123",
                username=credentials["username"],
                roles=["user"],
                permissions=["read", "write"],
                authenticated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=1)
            )
        raise InvalidCredentialsError("Invalid credentials")
    
    def validate_token(self, token: str) -> AuthenticationContext:
        """Mock token validation implementation."""
        if token in self.revoked_tokens:
            raise AuthenticationError("Token has been revoked")
        
        if token == self.valid_token:
            return AuthenticationContext(
                user_id="test123",
                username="test_user",
                roles=["user"],
                permissions=["read", "write"],
                authenticated_at=datetime.now() - timedelta(minutes=30),
                expires_at=datetime.now() + timedelta(minutes=30)
            )
        elif token == self.expired_token:
            raise TokenExpiredError("Token has expired")
        else:
            raise AuthenticationError("Invalid token")
    
    def refresh_token(self, token: str) -> tuple[str, AuthenticationContext]:
        """Mock token refresh implementation."""
        if token in self.revoked_tokens:
            raise AuthenticationError("Token has been revoked")
        
        if token == self.valid_token:
            new_token = f"refreshed.{token}"
            context = AuthenticationContext(
                user_id="test123",
                username="test_user",
                roles=["user"],
                permissions=["read", "write"],
                authenticated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=1)
            )
            return new_token, context
        elif token == self.expired_token:
            raise TokenExpiredError("Cannot refresh expired token")
        else:
            raise AuthenticationError("Invalid token")
    
    def revoke_token(self, token: str) -> None:
        """Mock token revocation implementation."""
        if token not in [self.valid_token, self.expired_token]:
            raise AuthenticationError("Invalid token")
        self.revoked_tokens.add(token)

@pytest.fixture
def auth_provider() -> MockAuthProvider:
    """Create mock authentication provider."""
    return MockAuthProvider()

@pytest.fixture
def auth_context() -> AuthenticationContext:
    """Create test authentication context."""
    return AuthenticationContext(
        user_id="test123",
        username="test_user",
        roles=["user", "admin"],
        permissions=["read", "write", "delete"],
        authenticated_at=datetime.now(),
        expires_at=datetime.now() + timedelta(hours=1),
        metadata={"device": "test_device"}
    )

def test_auth_context_initialization(auth_context):
    """Test authentication context initialization."""
    assert auth_context.user_id == "test123"
    assert auth_context.username == "test_user"
    assert "user" in auth_context.roles
    assert "admin" in auth_context.roles
    assert "read" in auth_context.permissions
    assert "write" in auth_context.permissions
    assert "delete" in auth_context.permissions
    assert auth_context.metadata["device"] == "test_device"

def test_auth_context_expiration(auth_context):
    """Test authentication context expiration."""
    assert not auth_context.is_expired
    
    # Test expired context
    expired_context = AuthenticationContext(
        user_id="test123",
        username="test_user",
        roles=[],
        permissions=[],
        authenticated_at=datetime.now() - timedelta(hours=2),
        expires_at=datetime.now() - timedelta(hours=1)
    )
    assert expired_context.is_expired

def test_auth_context_role_check(auth_context):
    """Test authentication context role checking."""
    assert auth_context.has_role("user")
    assert auth_context.has_role("admin")
    assert not auth_context.has_role("superuser")

def test_auth_context_permission_check(auth_context):
    """Test authentication context permission checking."""
    assert auth_context.has_permission("read")
    assert auth_context.has_permission("write")
    assert auth_context.has_permission("delete")
    assert not auth_context.has_permission("execute")

def test_auth_context_to_dict(auth_context):
    """Test authentication context serialization."""
    data = auth_context.to_dict()
    assert data["user_id"] == "test123"
    assert data["username"] == "test_user"
    assert "user" in data["roles"]
    assert "admin" in data["roles"]
    assert "read" in data["permissions"]
    assert "write" in data["permissions"]
    assert "delete" in data["permissions"]
    assert "authenticated_at" in data
    assert "expires_at" in data
    assert data["metadata"]["device"] == "test_device"

def test_successful_authentication(auth_provider):
    """Test successful authentication."""
    context = auth_provider.authenticate(
        username="test_user",
        password="test_pass"
    )
    assert isinstance(context, AuthenticationContext)
    assert context.username == "test_user"
    assert "user" in context.roles
    assert "read" in context.permissions
    assert "write" in context.permissions

def test_failed_authentication(auth_provider):
    """Test failed authentication."""
    with pytest.raises(InvalidCredentialsError):
        auth_provider.authenticate(
            username="wrong_user",
            password="wrong_pass"
        )

def test_token_validation(auth_provider):
    """Test token validation."""
    context = auth_provider.validate_token(auth_provider.valid_token)
    assert isinstance(context, AuthenticationContext)
    assert context.username == "test_user"
    assert "user" in context.roles
    assert "read" in context.permissions
    assert "write" in context.permissions

def test_expired_token_validation(auth_provider):
    """Test expired token validation."""
    with pytest.raises(TokenExpiredError):
        auth_provider.validate_token(auth_provider.expired_token)

def test_invalid_token_validation(auth_provider):
    """Test invalid token validation."""
    with pytest.raises(AuthenticationError):
        auth_provider.validate_token("invalid.token")

def test_token_refresh(auth_provider):
    """Test token refresh."""
    new_token, context = auth_provider.refresh_token(auth_provider.valid_token)
    assert new_token.startswith("refreshed.")
    assert isinstance(context, AuthenticationContext)
    assert context.username == "test_user"
    assert not context.is_expired

def test_expired_token_refresh(auth_provider):
    """Test expired token refresh."""
    with pytest.raises(TokenExpiredError):
        auth_provider.refresh_token(auth_provider.expired_token)

def test_invalid_token_refresh(auth_provider):
    """Test invalid token refresh."""
    with pytest.raises(AuthenticationError):
        auth_provider.refresh_token("invalid.token")

def test_token_revocation(auth_provider):
    """Test token revocation."""
    auth_provider.revoke_token(auth_provider.valid_token)
    with pytest.raises(AuthenticationError):
        auth_provider.validate_token(auth_provider.valid_token)

def test_invalid_token_revocation(auth_provider):
    """Test invalid token revocation."""
    with pytest.raises(AuthenticationError):
        auth_provider.revoke_token("invalid.token") 