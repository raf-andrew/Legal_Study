"""Mock cache service implementation."""
import logging
import time
from typing import Any, Dict, List, Optional, Set, Union
from datetime import datetime, timedelta
from ..base import BaseMockService

logger = logging.getLogger(__name__)

class CacheEntry:
    """Cache entry with expiration."""
    
    def __init__(self, key: str, value: Any, ttl: Optional[int] = None):
        self.key = key
        self.value = value
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=ttl) if ttl else None
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def access(self):
        """Record access."""
        self.access_count += 1
        self.last_accessed = datetime.now()

class MockCache(BaseMockService):
    """Mock cache service."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self._data: Dict[str, CacheEntry] = {}
        self._default_ttl = 3600  # 1 hour
        self._max_size = 1000
        self._eviction_policy = "lru"  # lru, lfu, or fifo

    def _start(self):
        """Start the mock cache service."""
        self._load_config()

    def _stop(self):
        """Stop the mock cache service."""
        self._data.clear()

    def _reset(self):
        """Reset the mock cache service."""
        super()._reset()
        self._data.clear()
        self._load_config()

    def _load_config(self):
        """Load configuration."""
        config = self.state.config
        self._default_ttl = config.get("default_ttl", 3600)
        self._max_size = config.get("max_size", 1000)
        self._eviction_policy = config.get("eviction_policy", "lru")

    def _evict(self):
        """Evict entries based on policy."""
        if len(self._data) < self._max_size:
            return
        
        if self._eviction_policy == "lru":
            # Remove least recently used
            key_to_remove = min(
                self._data.items(),
                key=lambda x: x[1].last_accessed
            )[0]
        elif self._eviction_policy == "lfu":
            # Remove least frequently used
            key_to_remove = min(
                self._data.items(),
                key=lambda x: x[1].access_count
            )[0]
        else:  # fifo
            # Remove oldest entry
            key_to_remove = min(
                self._data.items(),
                key=lambda x: x[1].created_at
            )[0]
        
        del self._data[key_to_remove]
        self.logger.info(f"Evicted key: {key_to_remove}")

    def _cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self._data.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._data[key]
            self.logger.info(f"Removed expired key: {key}")

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a cache entry."""
        try:
            self.state.record_call("set", (key,), {
                "value": value,
                "ttl": ttl
            })
            
            # Clean up expired entries
            self._cleanup_expired()
            
            # Check size and evict if necessary
            if len(self._data) >= self._max_size:
                self._evict()
            
            # Set entry
            ttl = ttl if ttl is not None else self._default_ttl
            self._data[key] = CacheEntry(key, value, ttl)
            
            return True
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "set",
                "key": key,
                "ttl": ttl
            })
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get a cache entry."""
        try:
            self.state.record_call("get", (key,), {
                "default": default
            })
            
            # Clean up expired entries
            self._cleanup_expired()
            
            # Get entry
            entry = self._data.get(key)
            if not entry:
                return default
            
            if entry.is_expired():
                del self._data[key]
                return default
            
            entry.access()
            return entry.value
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "get",
                "key": key
            })
            raise

    def delete(self, key: str) -> bool:
        """Delete a cache entry."""
        try:
            self.state.record_call("delete", (key,), {})
            
            if key in self._data:
                del self._data[key]
                return True
            return False
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "delete",
                "key": key
            })
            raise

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        try:
            self.state.record_call("exists", (key,), {})
            
            entry = self._data.get(key)
            if not entry:
                return False
            
            if entry.is_expired():
                del self._data[key]
                return False
            
            return True
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "exists",
                "key": key
            })
            raise

    def clear(self) -> bool:
        """Clear all entries."""
        try:
            self.state.record_call("clear", (), {})
            self._data.clear()
            return True
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "clear"
            })
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            self.state.record_call("get_stats", (), {})
            
            total_entries = len(self._data)
            expired_entries = sum(1 for entry in self._data.values() if entry.is_expired())
            total_size = total_entries
            hit_count = sum(entry.access_count for entry in self._data.values())
            
            return {
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "total_size": total_size,
                "max_size": self._max_size,
                "hit_count": hit_count,
                "eviction_policy": self._eviction_policy,
                "default_ttl": self._default_ttl
            }
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "get_stats"
            })
            raise

    def get_keys(self) -> List[str]:
        """Get all non-expired keys."""
        try:
            self.state.record_call("get_keys", (), {})
            
            # Clean up expired entries
            self._cleanup_expired()
            
            return list(self._data.keys())
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "get_keys"
            })
            raise

    def touch(self, key: str, ttl: Optional[int] = None) -> bool:
        """Update entry TTL."""
        try:
            self.state.record_call("touch", (key,), {"ttl": ttl})
            
            entry = self._data.get(key)
            if not entry:
                return False
            
            if entry.is_expired():
                del self._data[key]
                return False
            
            ttl = ttl if ttl is not None else self._default_ttl
            entry.expires_at = datetime.now() + timedelta(seconds=ttl)
            return True
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "touch",
                "key": key,
                "ttl": ttl
            })
            raise 