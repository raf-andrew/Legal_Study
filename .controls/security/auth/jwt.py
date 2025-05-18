"""JWT authentication provider implementation."""

import jwt
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from .provider import (
    AuthenticationContext,
    AuthenticationProvider,
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError
)

class JWTAuthenticationProvider(AuthenticationProvider):
    """JWT-based authentication provider."""
    
    def __init__(
        self,
        secret_key: str,
        token_expiry: timedelta = timedelta(hours=1),
        refresh_expiry: timedelta = timedelta(days=7),
        algorithm: str = "HS256"
    ):
        """Initialize JWT authentication provider.
        
        Args:
            secret_key: Secret key for JWT signing
            token_expiry: Access token expiry time
            refresh_expiry: Refresh token expiry time
            algorithm: JWT signing algorithm
        """
        self.secret_key = secret_key
        self.token_expiry = token_expiry
        self.refresh_expiry = refresh_expiry
        self.algorithm = algorithm
        self.logger = logging.getLogger("auth.jwt")
        self.revoked_tokens = set()
    
    def _create_token(
        self,
        user_id: str,
        username: str,
        roles: list[str],
        permissions: list[str],
        expiry: timedelta,
        token_type: str = "access",
        **claims: Any
    ) -> str:
        """Create a JWT token.
        
        Args:
            user_id: User identifier
            username: Username
            roles: User roles
            permissions: User permissions
            expiry: Token expiry time
            token_type: Type of token (access or refresh)
            **claims: Additional claims to include in token
            
        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        expires = now + expiry
        
        payload = {
            "sub": user_id,
            "username": username,
            "roles": roles,
            "permissions": permissions,
            "type": token_type,
            "iat": now,
            "exp": expires,
            **claims
        }
        
        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm
        )
    
    def _verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload
            
        Raises:
            TokenExpiredError: If token has expired
            AuthenticationError: If token is invalid
        """
        if token in self.revoked_tokens:
            raise AuthenticationError("Token has been revoked")
        
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    def authenticate(self, **credentials: Any) -> Tuple[str, str, AuthenticationContext]:
        """Authenticate user and generate tokens.
        
        Args:
            **credentials: Authentication credentials
            
        Returns:
            Tuple of (access token, refresh token, authentication context)
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        # This would typically validate credentials against a database
        # For now, we'll just use a mock validation
        username = credentials.get("username")
        password = credentials.get("password")
        
        if not username or not password:
            raise InvalidCredentialsError("Username and password required")
        
        # Mock user data - in reality, this would come from a database
        user_data = {
            "user_id": "user123",
            "username": username,
            "roles": ["user"],
            "permissions": ["read", "write"]
        }
        
        # Create tokens
        access_token = self._create_token(
            user_data["user_id"],
            user_data["username"],
            user_data["roles"],
            user_data["permissions"],
            self.token_expiry,
            "access"
        )
        
        refresh_token = self._create_token(
            user_data["user_id"],
            user_data["username"],
            user_data["roles"],
            user_data["permissions"],
            self.refresh_expiry,
            "refresh"
        )
        
        # Create authentication context
        context = AuthenticationContext(
            user_id=user_data["user_id"],
            username=user_data["username"],
            roles=user_data["roles"],
            permissions=user_data["permissions"],
            authenticated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.token_expiry
        )
        
        return access_token, refresh_token, context
    
    def validate_token(self, token: str) -> AuthenticationContext:
        """Validate a JWT token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Authentication context
            
        Raises:
            TokenExpiredError: If token has expired
            AuthenticationError: If token is invalid
        """
        payload = self._verify_token(token)
        
        if payload["type"] != "access":
            raise AuthenticationError("Invalid token type")
        
        return AuthenticationContext(
            user_id=payload["sub"],
            username=payload["username"],
            roles=payload["roles"],
            permissions=payload["permissions"],
            authenticated_at=datetime.utcfromtimestamp(payload["iat"]),
            expires_at=datetime.utcfromtimestamp(payload["exp"])
        )
    
    def refresh_token(self, refresh_token: str) -> Tuple[str, AuthenticationContext]:
        """Refresh an access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Tuple of (new access token, new authentication context)
            
        Raises:
            TokenExpiredError: If refresh token has expired
            AuthenticationError: If refresh token is invalid
        """
        payload = self._verify_token(refresh_token)
        
        if payload["type"] != "refresh":
            raise AuthenticationError("Invalid token type")
        
        # Create new access token
        access_token = self._create_token(
            payload["sub"],
            payload["username"],
            payload["roles"],
            payload["permissions"],
            self.token_expiry,
            "access"
        )
        
        # Create new authentication context
        context = AuthenticationContext(
            user_id=payload["sub"],
            username=payload["username"],
            roles=payload["roles"],
            permissions=payload["permissions"],
            authenticated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.token_expiry
        )
        
        return access_token, context
    
    def revoke_token(self, token: str) -> None:
        """Revoke a JWT token.
        
        Args:
            token: JWT token to revoke
            
        Raises:
            AuthenticationError: If token is invalid
        """
        try:
            # Verify token is valid before revoking
            self._verify_token(token)
            self.revoked_tokens.add(token)
            self.logger.info(f"Token revoked: {token[:10]}...")
        except (TokenExpiredError, AuthenticationError) as e:
            self.logger.error(f"Failed to revoke token: {str(e)}")
            raise 