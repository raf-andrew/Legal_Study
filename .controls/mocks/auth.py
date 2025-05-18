"""Mock authentication service for testing."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

class MockAuthService:
    """Mock authentication service implementation for testing."""
    
    def __init__(
        self,
        name: str,
        token_expiry_minutes: int = 60,
        refresh_token_expiry_days: int = 7
    ):
        """Initialize mock auth service.
        
        Args:
            name: Service name
            token_expiry_minutes: Access token expiry in minutes
            refresh_token_expiry_days: Refresh token expiry in days
        """
        self.name = name
        self.token_expiry = timedelta(minutes=token_expiry_minutes)
        self.refresh_expiry = timedelta(days=refresh_token_expiry_days)
        self.logger = logging.getLogger(f"mock.auth.{name}")
        
        # Internal state
        self._users: Dict[str, Dict[str, Any]] = {}
        self._active_tokens: Dict[str, Dict[str, Any]] = {}
        self._refresh_tokens: Dict[str, Dict[str, Any]] = {}
        self._roles: Dict[str, Set[str]] = {}
        self._permissions: Dict[str, Set[str]] = {}
        self._is_healthy = True
        self._last_error: Optional[Exception] = None
        self._auth_count = 0
        self._error_count = 0
    
    async def authenticate(
        self,
        username: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Authentication result with tokens if successful
        """
        await asyncio.sleep(0.1)  # Simulate auth time
        self._auth_count += 1
        
        user = self._users.get(username)
        if not user or user["password"] != password:
            self._error_count += 1
            return None
        
        # Generate tokens
        access_token = f"mock_access_token_{username}_{datetime.now().timestamp()}"
        refresh_token = f"mock_refresh_token_{username}_{datetime.now().timestamp()}"
        
        # Store token info
        token_info = {
            "user_id": user["id"],
            "username": username,
            "expires_at": datetime.now() + self.token_expiry,
            "roles": list(self._roles.get(username, set())),
            "permissions": list(self._permissions.get(username, set()))
        }
        self._active_tokens[access_token] = token_info
        
        refresh_info = {
            "user_id": user["id"],
            "username": username,
            "access_token": access_token,
            "expires_at": datetime.now() + self.refresh_expiry
        }
        self._refresh_tokens[refresh_token] = refresh_info
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": int(self.token_expiry.total_seconds()),
            "token_type": "Bearer",
            "user": {
                "id": user["id"],
                "username": username,
                "roles": token_info["roles"],
                "permissions": token_info["permissions"]
            }
        }
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate access token.
        
        Args:
            token: Access token
            
        Returns:
            Token info if valid
        """
        await asyncio.sleep(0.05)  # Simulate validation time
        
        token_info = self._active_tokens.get(token)
        if not token_info:
            return None
        
        if datetime.now() > token_info["expires_at"]:
            del self._active_tokens[token]
            return None
        
        return token_info
    
    async def refresh_access_token(
        self,
        refresh_token: str
    ) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New authentication result if successful
        """
        await asyncio.sleep(0.1)  # Simulate refresh time
        
        refresh_info = self._refresh_tokens.get(refresh_token)
        if not refresh_info:
            return None
        
        if datetime.now() > refresh_info["expires_at"]:
            del self._refresh_tokens[refresh_token]
            return None
        
        # Invalidate old access token
        old_token = refresh_info["access_token"]
        if old_token in self._active_tokens:
            del self._active_tokens[old_token]
        
        # Generate new access token
        username = refresh_info["username"]
        return await self.authenticate(
            username,
            self._users[username]["password"]
        )
    
    def add_user(
        self,
        username: str,
        password: str,
        roles: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None
    ) -> str:
        """Add test user.
        
        Args:
            username: Username
            password: Password
            roles: User roles
            permissions: User permissions
            
        Returns:
            User ID
        """
        user_id = str(len(self._users) + 1)
        
        self._users[username] = {
            "id": user_id,
            "username": username,
            "password": password,
            "created_at": datetime.now().isoformat()
        }
        
        if roles:
            self._roles[username] = set(roles)
        
        if permissions:
            self._permissions[username] = set(permissions)
        
        self.logger.info(f"Added test user: {username}")
        return user_id
    
    def remove_user(self, username: str) -> bool:
        """Remove test user.
        
        Args:
            username: Username
            
        Returns:
            Whether user was removed
        """
        if username not in self._users:
            return False
        
        del self._users[username]
        self._roles.pop(username, None)
        self._permissions.pop(username, None)
        
        # Remove any active tokens
        for token, info in list(self._active_tokens.items()):
            if info["username"] == username:
                del self._active_tokens[token]
        
        for token, info in list(self._refresh_tokens.items()):
            if info["username"] == username:
                del self._refresh_tokens[token]
        
        self.logger.info(f"Removed test user: {username}")
        return True
    
    def add_role(self, username: str, role: str) -> bool:
        """Add role to user.
        
        Args:
            username: Username
            role: Role to add
            
        Returns:
            Whether role was added
        """
        if username not in self._users:
            return False
        
        if username not in self._roles:
            self._roles[username] = set()
        
        self._roles[username].add(role)
        return True
    
    def remove_role(self, username: str, role: str) -> bool:
        """Remove role from user.
        
        Args:
            username: Username
            role: Role to remove
            
        Returns:
            Whether role was removed
        """
        if username not in self._roles:
            return False
        
        self._roles[username].discard(role)
        return True
    
    def add_permission(self, username: str, permission: str) -> bool:
        """Add permission to user.
        
        Args:
            username: Username
            permission: Permission to add
            
        Returns:
            Whether permission was added
        """
        if username not in self._users:
            return False
        
        if username not in self._permissions:
            self._permissions[username] = set()
        
        self._permissions[username].add(permission)
        return True
    
    def remove_permission(self, username: str, permission: str) -> bool:
        """Remove permission from user.
        
        Args:
            username: Username
            permission: Permission to remove
            
        Returns:
            Whether permission was removed
        """
        if username not in self._permissions:
            return False
        
        self._permissions[username].discard(permission)
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get auth service metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            "total_users": len(self._users),
            "active_tokens": len(self._active_tokens),
            "refresh_tokens": len(self._refresh_tokens),
            "auth_count": self._auth_count,
            "error_count": self._error_count
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get auth service health status.
        
        Returns:
            Dictionary of health status
        """
        return {
            "name": self.name,
            "healthy": self._is_healthy,
            "last_error": str(self._last_error) if self._last_error else None,
            "error_count": self._error_count
        }
    
    def clear_data(self) -> None:
        """Clear all auth service data."""
        self._users.clear()
        self._active_tokens.clear()
        self._refresh_tokens.clear()
        self._roles.clear()
        self._permissions.clear()
        self.logger.info("Cleared all auth service data") 