"""Authentication provider interface for command security."""

import abc
from typing import Any, Dict, Optional
from datetime import datetime

class AuthenticationError(Exception):
    """Base class for authentication errors."""
    pass

class InvalidCredentialsError(AuthenticationError):
    """Error raised when credentials are invalid."""
    pass

class TokenExpiredError(AuthenticationError):
    """Error raised when authentication token has expired."""
    pass

class AuthenticationContext:
    """Context object containing authentication information."""
    
    def __init__(
        self,
        user_id: str,
        username: str,
        roles: list[str],
        permissions: list[str],
        authenticated_at: datetime,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize authentication context.
        
        Args:
            user_id: Unique identifier for the user
            username: Username of the authenticated user
            roles: List of roles assigned to the user
            permissions: List of permissions granted to the user
            authenticated_at: Timestamp of authentication
            expires_at: Optional expiration timestamp
            metadata: Optional additional authentication metadata
        """
        self.user_id = user_id
        self.username = username
        self.roles = roles
        self.permissions = permissions
        self.authenticated_at = authenticated_at
        self.expires_at = expires_at
        self.metadata = metadata or {}
    
    @property
    def is_expired(self) -> bool:
        """Check if authentication has expired.
        
        Returns:
            True if authentication has expired, False otherwise
        """
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def has_role(self, role: str) -> bool:
        """Check if user has specified role.
        
        Args:
            role: Role to check for
            
        Returns:
            True if user has role, False otherwise
        """
        return role in self.roles
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specified permission.
        
        Args:
            permission: Permission to check for
            
        Returns:
            True if user has permission, False otherwise
        """
        return permission in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary.
        
        Returns:
            Dictionary representation of context
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "roles": self.roles,
            "permissions": self.permissions,
            "authenticated_at": self.authenticated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata
        }

class AuthenticationProvider(abc.ABC):
    """Base class for authentication providers."""
    
    @abc.abstractmethod
    def authenticate(self, **credentials: Any) -> AuthenticationContext:
        """Authenticate user with provided credentials.
        
        Args:
            **credentials: Authentication credentials
            
        Returns:
            Authentication context
            
        Raises:
            AuthenticationError: If authentication fails
        """
        raise NotImplementedError("Authentication providers must implement authenticate")
    
    @abc.abstractmethod
    def validate_token(self, token: str) -> AuthenticationContext:
        """Validate authentication token.
        
        Args:
            token: Authentication token to validate
            
        Returns:
            Authentication context
            
        Raises:
            AuthenticationError: If token is invalid
        """
        raise NotImplementedError("Authentication providers must implement validate_token")
    
    @abc.abstractmethod
    def refresh_token(self, token: str) -> tuple[str, AuthenticationContext]:
        """Refresh authentication token.
        
        Args:
            token: Authentication token to refresh
            
        Returns:
            Tuple of (new token, new authentication context)
            
        Raises:
            AuthenticationError: If token cannot be refreshed
        """
        raise NotImplementedError("Authentication providers must implement refresh_token")
    
    @abc.abstractmethod
    def revoke_token(self, token: str) -> None:
        """Revoke authentication token.
        
        Args:
            token: Authentication token to revoke
            
        Raises:
            AuthenticationError: If token cannot be revoked
        """
        raise NotImplementedError("Authentication providers must implement revoke_token") 