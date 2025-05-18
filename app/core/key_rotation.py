"""Key rotation utility for security enhancement."""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class KeyRotation:
    """Handle key rotation for security."""
    
    def __init__(self, key_file: str = ".security/keys.json"):
        """Initialize key rotation.
        
        Args:
            key_file: Path to key storage file
        """
        self.key_file = Path(key_file)
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        self.current_keys: Dict[str, Dict] = {}
        self.load_keys()
        
    def generate_key(self) -> str:
        """Generate a new secure key.
        
        Returns:
            Secure random key
        """
        return secrets.token_urlsafe(32)
        
    def load_keys(self) -> None:
        """Load keys from storage."""
        import json
        
        if self.key_file.exists():
            try:
                with open(self.key_file) as f:
                    self.current_keys = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load keys: {e}")
                self.current_keys = {}
                
    def save_keys(self) -> None:
        """Save keys to storage."""
        import json
        
        try:
            with open(self.key_file, 'w') as f:
                json.dump(self.current_keys, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save keys: {e}")
            
    def rotate_key(self, key_name: str, expiry_days: int = 30) -> Tuple[str, str]:
        """Rotate a key.
        
        Args:
            key_name: Name of the key to rotate
            expiry_days: Days until key expires
            
        Returns:
            Tuple of (current key, previous key)
        """
        now = datetime.utcnow()
        new_key = self.generate_key()
        
        # Store new key
        self.current_keys[key_name] = {
            'current': new_key,
            'previous': self.current_keys.get(key_name, {}).get('current'),
            'rotated_at': now.isoformat(),
            'expires_at': (now + timedelta(days=expiry_days)).isoformat()
        }
        
        self.save_keys()
        return new_key, self.current_keys[key_name]['previous']
        
    def get_key(self, key_name: str, include_previous: bool = False) -> Optional[str]:
        """Get a key by name.
        
        Args:
            key_name: Name of the key to get
            include_previous: Whether to include previous key
            
        Returns:
            Current key or None if not found
        """
        if key_name not in self.current_keys:
            return None
            
        if include_previous:
            return (
                self.current_keys[key_name]['current'],
                self.current_keys[key_name]['previous']
            )
        return self.current_keys[key_name]['current']
        
    def should_rotate(self, key_name: str) -> bool:
        """Check if a key should be rotated.
        
        Args:
            key_name: Name of the key to check
            
        Returns:
            True if key should be rotated
        """
        if key_name not in self.current_keys:
            return True
            
        key_data = self.current_keys[key_name]
        expires_at = datetime.fromisoformat(key_data['expires_at'])
        return datetime.utcnow() >= expires_at
        
    def rotate_if_needed(self, key_name: str, expiry_days: int = 30) -> str:
        """Rotate a key if needed.
        
        Args:
            key_name: Name of the key to check
            expiry_days: Days until key expires
            
        Returns:
            Current key
        """
        if self.should_rotate(key_name):
            current, _ = self.rotate_key(key_name, expiry_days)
            return current
        return self.get_key(key_name) 