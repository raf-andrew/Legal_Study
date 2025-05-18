"""Unit tests for JWT authentication provider."""

import jwt
import pytest
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ...security.auth.jwt import JWTAuthenticationProvider
from ...security.auth.provider import (
    AuthenticationContext,
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError
)

@pytest.fixture
def secret_key() -> str:
    """Get test secret key."""
    return "test_secret_key_123"

@pytest.fixture
def auth_provider(secret_key) -> JWTAuthenticationProvider:
    """Create JWT authentication provider."""
    return JWTAuthenticationProvider(
        secret_key=secret_key,
        token_expiry=timedelta(hours=1),
        refresh_expiry=timedelta(days=7)
    )

@pytest.fixture
def valid_credentials() -> Dict[str, str]:
    """Get valid test credentials."""
    return {
        "username": "test_user",
        "password": "test_pass"
    }

def test_provider_initialization(auth_provider, secret_key):
    """Test provider initialization."""
    assert auth_provider.secret_key == secret_key
    assert auth_provider.token_expiry == timedelta(hours=1)
    assert auth_provider.refresh_expiry == timedelta(days=7)
    assert auth_provider.algorithm == "HS256"
    assert isinstance(auth_provider.revoked_tokens, set)

def test_create_token(auth_provider):
    """Test token creation."""
    token = auth_provider._create_token(
        user_id="test123",
        username="test_user",
        roles=["user"],
        permissions=["read"],
        expiry=timedelta(hours=1),
        token_type="access"
    )
    
    # Decode and verify token
    payload = jwt.decode(
        token,
        auth_provider.secret_key,
        algorithms=[auth_provider.algorithm]
    )
    
    assert payload["sub"] == "test123"
    assert payload["username"] == "test_user"
    assert payload["roles"] == ["user"]
    assert payload["permissions"] == ["read"]
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload

def test_verify_valid_token(auth_provider):
    """Test valid token verification."""
    token = auth_provider._create_token(
        user_id="test123",
        username="test_user",
        roles=["user"],
        permissions=["read"],
        expiry=timedelta(hours=1)
    )
    
    payload = auth_provider._verify_token(token)
    assert payload["sub"] == "test123"
    assert payload["username"] == "test_user"

def test_verify_expired_token(auth_provider):
    """Test expired token verification."""
    token = auth_provider._create_token(
        user_id="test123",
        username="test_user",
        roles=["user"],
        permissions=["read"],
        expiry=timedelta(seconds=-1)  # Expired
    )
    
    with pytest.raises(TokenExpiredError):
        auth_provider._verify_token(token)

def test_verify_invalid_token(auth_provider):
    """Test invalid token verification."""
    with pytest.raises(AuthenticationError):
        auth_provider._verify_token("invalid.token")

def test_successful_authentication(auth_provider, valid_credentials):
    """Test successful authentication."""
    access_token, refresh_token, context = auth_provider.authenticate(**valid_credentials)
    
    # Verify tokens
    access_payload = jwt.decode(
        access_token,
        auth_provider.secret_key,
        algorithms=[auth_provider.algorithm]
    )
    refresh_payload = jwt.decode(
        refresh_token,
        auth_provider.secret_key,
        algorithms=[auth_provider.algorithm]
    )
    
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"
    
    # Verify context
    assert isinstance(context, AuthenticationContext)
    assert context.username == valid_credentials["username"]
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

def test_validate_access_token(auth_provider, valid_credentials):
    """Test access token validation."""
    access_token, _, _ = auth_provider.authenticate(**valid_credentials)
    context = auth_provider.validate_token(access_token)
    
    assert isinstance(context, AuthenticationContext)
    assert context.username == valid_credentials["username"]
    assert "user" in context.roles
    assert "read" in context.permissions
    assert "write" in context.permissions

def test_validate_refresh_token(auth_provider, valid_credentials):
    """Test refresh token validation."""
    _, refresh_token, _ = auth_provider.authenticate(**valid_credentials)
    
    with pytest.raises(AuthenticationError) as exc:
        auth_provider.validate_token(refresh_token)
    assert "Invalid token type" in str(exc.value)

def test_refresh_token_flow(auth_provider, valid_credentials):
    """Test token refresh flow."""
    # Get initial tokens
    _, refresh_token, _ = auth_provider.authenticate(**valid_credentials)
    
    # Refresh access token
    new_access_token, context = auth_provider.refresh_token(refresh_token)
    
    # Verify new access token
    new_context = auth_provider.validate_token(new_access_token)
    assert new_context.username == valid_credentials["username"]
    assert not new_context.is_expired

def test_refresh_with_access_token(auth_provider, valid_credentials):
    """Test refresh with access token."""
    access_token, _, _ = auth_provider.authenticate(**valid_credentials)
    
    with pytest.raises(AuthenticationError) as exc:
        auth_provider.refresh_token(access_token)
    assert "Invalid token type" in str(exc.value)

def test_token_revocation(auth_provider, valid_credentials):
    """Test token revocation."""
    access_token, _, _ = auth_provider.authenticate(**valid_credentials)
    
    # Revoke token
    auth_provider.revoke_token(access_token)
    
    # Attempt to use revoked token
    with pytest.raises(AuthenticationError) as exc:
        auth_provider.validate_token(access_token)
    assert "Token has been revoked" in str(exc.value)

def test_revoke_invalid_token(auth_provider):
    """Test revoking invalid token."""
    with pytest.raises(AuthenticationError):
        auth_provider.revoke_token("invalid.token")

def test_token_expiry_times(auth_provider, valid_credentials):
    """Test token expiry times."""
    access_token, refresh_token, _ = auth_provider.authenticate(**valid_credentials)
    
    # Verify access token expiry
    access_payload = jwt.decode(
        access_token,
        auth_provider.secret_key,
        algorithms=[auth_provider.algorithm]
    )
    access_exp = datetime.utcfromtimestamp(access_payload["exp"])
    assert access_exp > datetime.utcnow()
    assert access_exp <= datetime.utcnow() + auth_provider.token_expiry
    
    # Verify refresh token expiry
    refresh_payload = jwt.decode(
        refresh_token,
        auth_provider.secret_key,
        algorithms=[auth_provider.algorithm]
    )
    refresh_exp = datetime.utcfromtimestamp(refresh_payload["exp"])
    assert refresh_exp > datetime.utcnow()
    assert refresh_exp <= datetime.utcnow() + auth_provider.refresh_expiry 