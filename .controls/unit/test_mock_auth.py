"""Unit tests for mock authentication service."""
import pytest
import yaml
import time
from typing import Dict, Any
from datetime import datetime, timedelta
from ..mocks.services.auth import MockAuthService, MockUser, MockToken

@pytest.fixture
def config() -> Dict[str, Any]:
    """Load test configuration."""
    with open(".config/mock.yaml") as f:
        config = yaml.safe_load(f)
    return config["auth"]

@pytest.fixture
def auth_service(config) -> MockAuthService:
    """Create mock authentication service instance."""
    return MockAuthService("test_auth", config)

def test_service_initialization(auth_service):
    """Test service initialization."""
    assert auth_service.name == "test_auth"
    assert auth_service._users == {}
    assert auth_service._tokens == {}
    assert auth_service._secret == "mock_secret"
    assert auth_service._token_expiry == timedelta(hours=1)

def test_service_start(auth_service):
    """Test service start."""
    auth_service.start()
    assert "test_user" in auth_service._users
    assert len(auth_service._tokens) > 0

def test_service_stop(auth_service):
    """Test service stop."""
    auth_service.start()
    assert len(auth_service._users) > 0
    assert len(auth_service._tokens) > 0
    
    auth_service.stop()
    assert len(auth_service._users) == 0
    assert len(auth_service._tokens) == 0

def test_service_reset(auth_service):
    """Test service reset."""
    auth_service.start()
    original_users = set(auth_service._users.keys())
    original_tokens = set(auth_service._tokens.keys())
    
    # Modify state
    auth_service._users.clear()
    auth_service._tokens.clear()
    
    # Reset
    auth_service.reset()
    assert set(auth_service._users.keys()) == original_users
    assert set(auth_service._tokens.keys()) == original_tokens

def test_create_user(auth_service):
    """Test creating a user."""
    user = auth_service.create_user("test", ["user"], True)
    
    assert isinstance(user, MockUser)
    assert user.username == "test"
    assert user.roles == {"user"}
    assert user.active is True
    assert user.login_count == 0
    assert user.failed_attempts == 0

def test_create_duplicate_user(auth_service):
    """Test creating a duplicate user."""
    auth_service.create_user("test", ["user"])
    
    with pytest.raises(ValueError):
        auth_service.create_user("test", ["user"])

def test_get_user(auth_service):
    """Test getting a user."""
    created_user = auth_service.create_user("test", ["user"])
    retrieved_user = auth_service.get_user("test")
    
    assert retrieved_user is created_user

def test_list_users(auth_service):
    """Test listing users."""
    auth_service.start()
    users = auth_service.list_users()
    
    assert "test_user" in users

def test_create_token(auth_service):
    """Test creating a token."""
    auth_service.create_user("test", ["user"])
    token = auth_service.create_token("test")
    
    assert token in auth_service._tokens
    token_obj = auth_service._tokens[token]
    assert token_obj.user == "test"
    assert token_obj.roles == {"user"}
    assert not token_obj.is_expired()

def test_create_token_inactive_user(auth_service):
    """Test creating a token for inactive user."""
    auth_service.create_user("test", ["user"], active=False)
    
    with pytest.raises(ValueError):
        auth_service.create_token("test")

def test_validate_token(auth_service):
    """Test validating a token."""
    auth_service.create_user("test", ["user"])
    token = auth_service.create_token("test")
    
    token_data = auth_service.validate_token(token)
    assert token_data["username"] == "test"
    assert token_data["roles"] == ["user"]

def test_validate_expired_token(auth_service):
    """Test validating an expired token."""
    auth_service.create_user("test", ["user"])
    token = auth_service.create_token("test", expires_in=timedelta(seconds=1))
    
    time.sleep(1.1)  # Wait for expiration
    with pytest.raises(ValueError):
        auth_service.validate_token(token)

def test_revoke_token(auth_service):
    """Test revoking a token."""
    auth_service.create_user("test", ["user"])
    token = auth_service.create_token("test")
    
    assert auth_service.revoke_token(token) is True
    with pytest.raises(ValueError):
        auth_service.validate_token(token)

def test_authenticate(auth_service):
    """Test authenticating a user."""
    auth_service.create_user("test", ["user"])
    token = auth_service.create_token("test")
    
    assert auth_service.authenticate("test", token) is True
    user = auth_service.get_user("test")
    assert user.login_count == 1
    assert user.failed_attempts == 0

def test_authenticate_wrong_user(auth_service):
    """Test authenticating with wrong user."""
    auth_service.create_user("test1", ["user"])
    auth_service.create_user("test2", ["user"])
    token = auth_service.create_token("test1")
    
    assert auth_service.authenticate("test2", token) is False
    user = auth_service.get_user("test2")
    assert user.login_count == 0
    assert user.failed_attempts == 1

def test_check_permission(auth_service):
    """Test checking permissions."""
    auth_service.create_user("test", ["user", "admin"])
    token = auth_service.create_token("test")
    
    assert auth_service.check_permission(token, ["user"]) is True
    assert auth_service.check_permission(token, ["admin"]) is True
    assert auth_service.check_permission(token, ["other"]) is False

def test_get_user_stats(auth_service):
    """Test getting user statistics."""
    auth_service.create_user("test", ["user"])
    token = auth_service.create_token("test")
    auth_service.authenticate("test", token)
    
    stats = auth_service.get_user_stats("test")
    assert stats["username"] == "test"
    assert stats["roles"] == ["user"]
    assert stats["active"] is True
    assert stats["login_count"] == 1
    assert stats["failed_attempts"] == 0

def test_get_token_stats(auth_service):
    """Test getting token statistics."""
    auth_service.create_user("test", ["user"])
    token = auth_service.create_token("test")
    auth_service.validate_token(token)
    
    stats = auth_service.get_token_stats(token)
    assert stats["user"] == "test"
    assert stats["roles"] == ["user"]
    assert stats["revoked"] is False
    assert stats["use_count"] == 1
    assert stats["is_valid"] is True

def test_metrics_recording(auth_service):
    """Test metrics recording."""
    auth_service.create_user("test", ["user"])
    token = auth_service.create_token("test")
    auth_service.validate_token(token)
    
    metrics = auth_service.get_metrics()
    assert metrics["total_calls"] == 2
    assert metrics["total_errors"] == 0

def test_error_recording(auth_service):
    """Test error recording."""
    with pytest.raises(ValueError):
        auth_service.validate_token("invalid")
    
    errors = auth_service.get_errors()
    assert len(errors) == 1
    assert errors[0]["error"] == "Invalid token"

def test_call_recording(auth_service):
    """Test call recording."""
    auth_service.create_user("test", ["user"])
    token = auth_service.create_token("test")
    auth_service.validate_token(token)
    
    calls = auth_service.get_calls()
    assert len(calls) == 2
    assert calls[0]["method"] == "create_token"
    assert calls[1]["method"] == "validate_token" 