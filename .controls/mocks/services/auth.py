"""Mock authentication service implementation."""
import logging
import jwt
import time
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from ..base import BaseMockService

logger = logging.getLogger(__name__)

class MockUser:
    """Mock user."""
    
    def __init__(self, username: str, roles: List[str], active: bool = True):
        self.username = username
        self.roles = set(roles)
        self.active = active
        self.created_at = datetime.now()
        self.last_login = None
        self.login_count = 0
        self.failed_attempts = 0

    def login(self):
        """Record successful login."""
        self.last_login = datetime.now()
        self.login_count += 1
        self.failed_attempts = 0

    def fail_login(self):
        """Record failed login attempt."""
        self.failed_attempts += 1

class MockToken:
    """Mock authentication token."""
    
    def __init__(self, token: str, user: str, roles: List[str], expires_at: datetime):
        self.token = token
        self.user = user
        self.roles = set(roles)
        self.created_at = datetime.now()
        self.expires_at = expires_at
        self.revoked = False
        self.last_used = None
        self.use_count = 0

    def use(self):
        """Record token usage."""
        self.last_used = datetime.now()
        self.use_count += 1

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now() > self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid."""
        return not self.revoked and not self.is_expired()

class MockAuthService(BaseMockService):
    """Mock authentication service."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self._users: Dict[str, MockUser] = {}
        self._tokens: Dict[str, MockToken] = {}
        self._secret = "mock_secret"
        self._token_expiry = timedelta(hours=1)

    def _start(self):
        """Start the mock authentication service."""
        self._load_users()
        self._load_tokens()

    def _stop(self):
        """Stop the mock authentication service."""
        self._users.clear()
        self._tokens.clear()

    def _reset(self):
        """Reset the mock authentication service."""
        super()._reset()
        self._users.clear()
        self._tokens.clear()
        self._load_users()
        self._load_tokens()

    def _load_users(self):
        """Load users from configuration."""
        users = self.state.config.get("users", [])
        for user_config in users:
            self.create_user(
                user_config["username"],
                user_config.get("roles", []),
                user_config.get("active", True)
            )

    def _load_tokens(self):
        """Load tokens from configuration."""
        tokens = self.state.config.get("tokens", [])
        for token_config in tokens:
            expires_at = datetime.fromisoformat(token_config["expires_at"])
            self._tokens[token_config["token"]] = MockToken(
                token_config["token"],
                token_config["user"],
                token_config.get("roles", []),
                expires_at
            )

    def create_user(self, username: str, roles: List[str], active: bool = True) -> MockUser:
        """Create a user."""
        if username in self._users:
            raise ValueError(f"User already exists: {username}")
        
        user = MockUser(username, roles, active)
        self._users[username] = user
        self.logger.info(f"Created user: {username}")
        return user

    def get_user(self, username: str) -> Optional[MockUser]:
        """Get a user."""
        return self._users.get(username)

    def list_users(self) -> List[str]:
        """List users."""
        return list(self._users.keys())

    def create_token(self, username: str, roles: Optional[List[str]] = None,
                    expires_in: Optional[timedelta] = None) -> str:
        """Create an authentication token."""
        try:
            user = self.get_user(username)
            if not user:
                raise ValueError(f"User not found: {username}")
            
            if not user.active:
                raise ValueError(f"User is not active: {username}")
            
            roles = list(roles) if roles is not None else list(user.roles)
            expires_in = expires_in if expires_in is not None else self._token_expiry
            expires_at = datetime.now() + expires_in
            
            payload = {
                "sub": username,
                "roles": roles,
                "exp": int(expires_at.timestamp())
            }
            
            token = jwt.encode(payload, self._secret, algorithm="HS256")
            self._tokens[token] = MockToken(token, username, roles, expires_at)
            
            self.state.record_call("create_token", (username,), {
                "roles": roles,
                "expires_in": expires_in
            })
            
            return token
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "create_token",
                "username": username
            })
            raise

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate an authentication token."""
        try:
            self.state.record_call("validate_token", (token,), {})
            
            token_obj = self._tokens.get(token)
            if not token_obj:
                raise ValueError("Invalid token")
            
            if not token_obj.is_valid():
                raise ValueError("Token is expired or revoked")
            
            user = self.get_user(token_obj.user)
            if not user or not user.active:
                raise ValueError("User is not active")
            
            token_obj.use()
            return {
                "username": token_obj.user,
                "roles": list(token_obj.roles),
                "expires_at": token_obj.expires_at.isoformat()
            }
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "validate_token",
                "token": token
            })
            raise

    def revoke_token(self, token: str) -> bool:
        """Revoke an authentication token."""
        try:
            self.state.record_call("revoke_token", (token,), {})
            
            token_obj = self._tokens.get(token)
            if not token_obj:
                return False
            
            token_obj.revoked = True
            return True
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "revoke_token",
                "token": token
            })
            raise

    def authenticate(self, username: str, token: str) -> bool:
        """Authenticate a user with a token."""
        try:
            self.state.record_call("authenticate", (username, token), {})
            
            user = self.get_user(username)
            if not user:
                return False
            
            if not user.active:
                user.fail_login()
                return False
            
            try:
                token_data = self.validate_token(token)
                if token_data["username"] != username:
                    user.fail_login()
                    return False
                
                user.login()
                return True
                
            except Exception:
                user.fail_login()
                return False
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "authenticate",
                "username": username,
                "token": token
            })
            raise

    def check_permission(self, token: str, required_roles: List[str]) -> bool:
        """Check if token has required roles."""
        try:
            self.state.record_call("check_permission", (token,), {
                "required_roles": required_roles
            })
            
            token_data = self.validate_token(token)
            user_roles = set(token_data["roles"])
            required_roles = set(required_roles)
            
            return bool(user_roles & required_roles)
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "check_permission",
                "token": token,
                "required_roles": required_roles
            })
            raise

    def get_user_stats(self, username: str) -> Dict[str, Any]:
        """Get user statistics."""
        try:
            self.state.record_call("get_user_stats", (username,), {})
            
            user = self.get_user(username)
            if not user:
                raise ValueError(f"User not found: {username}")
            
            return {
                "username": user.username,
                "roles": list(user.roles),
                "active": user.active,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "login_count": user.login_count,
                "failed_attempts": user.failed_attempts
            }
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "get_user_stats",
                "username": username
            })
            raise

    def get_token_stats(self, token: str) -> Dict[str, Any]:
        """Get token statistics."""
        try:
            self.state.record_call("get_token_stats", (token,), {})
            
            token_obj = self._tokens.get(token)
            if not token_obj:
                raise ValueError("Invalid token")
            
            return {
                "user": token_obj.user,
                "roles": list(token_obj.roles),
                "created_at": token_obj.created_at.isoformat(),
                "expires_at": token_obj.expires_at.isoformat(),
                "revoked": token_obj.revoked,
                "last_used": token_obj.last_used.isoformat() if token_obj.last_used else None,
                "use_count": token_obj.use_count,
                "is_valid": token_obj.is_valid()
            }
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "get_token_stats",
                "token": token
            })
            raise 