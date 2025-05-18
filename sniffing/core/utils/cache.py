"""
Result caching for sniffing operations.
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("cache")

class ResultCache:
    """Cache for sniffing results."""

    def __init__(self, ttl: int = 3600):
        """Initialize result cache.

        Args:
            ttl: Time to live for cache entries in seconds
        """
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_dir = Path("reports") / "cache"
        self._setup_storage()
        self._load_cache()

    def _setup_storage(self) -> None:
        """Set up cache storage directory."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        except Exception as e:
            logger.error(f"Error setting up cache storage: {e}")
            raise

    def _load_cache(self) -> None:
        """Load cache from disk."""
        try:
            # Load all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, "r") as f:
                        cache_data = json.load(f)
                        self.cache.update(cache_data)

                except Exception as e:
                    logger.error(f"Error loading cache file {cache_file}: {e}")

            # Clean expired entries
            self._clean_expired()

        except Exception as e:
            logger.error(f"Error loading cache: {e}")

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result.

        Args:
            key: Cache key

        Returns:
            Cached result or None if not found or expired
        """
        try:
            # Check if key exists
            if key not in self.cache:
                return None

            # Get cache entry
            entry = self.cache[key]

            # Check if expired
            if time.time() - entry["timestamp"] > self.ttl:
                del self.cache[key]
                self._save_cache()
                return None

            return entry["result"]

        except Exception as e:
            logger.error(f"Error getting cache entry {key}: {e}")
            return None

    def set(self, key: str, result: Dict[str, Any]) -> None:
        """Set cache entry.

        Args:
            key: Cache key
            result: Result to cache
        """
        try:
            # Create cache entry
            self.cache[key] = {
                "timestamp": time.time(),
                "result": result
            }

            # Save cache
            self._save_cache()

        except Exception as e:
            logger.error(f"Error setting cache entry {key}: {e}")

    def delete(self, key: str) -> None:
        """Delete cache entry.

        Args:
            key: Cache key
        """
        try:
            if key in self.cache:
                del self.cache[key]
                self._save_cache()

        except Exception as e:
            logger.error(f"Error deleting cache entry {key}: {e}")

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            self.cache.clear()
            self._save_cache()

        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def _clean_expired(self) -> None:
        """Clean expired cache entries."""
        try:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if current_time - entry["timestamp"] > self.ttl
            ]

            for key in expired_keys:
                del self.cache[key]

            if expired_keys:
                self._save_cache()

        except Exception as e:
            logger.error(f"Error cleaning expired entries: {e}")

    def _save_cache(self) -> None:
        """Save cache to disk."""
        try:
            # Create cache file
            cache_file = self.cache_dir / f"cache_{datetime.now().strftime('%Y%m%d')}.json"

            # Save cache
            with open(cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)

            # Clean old cache files
            self._clean_old_cache_files()

        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def _clean_old_cache_files(self) -> None:
        """Clean old cache files."""
        try:
            # Keep only last 7 days of cache files
            cache_files = sorted(self.cache_dir.glob("*.json"))
            if len(cache_files) > 7:
                for old_file in cache_files[:-7]:
                    old_file.unlink()

        except Exception as e:
            logger.error(f"Error cleaning old cache files: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary of cache statistics
        """
        try:
            current_time = time.time()
            total_entries = len(self.cache)
            expired_entries = sum(
                1 for entry in self.cache.values()
                if current_time - entry["timestamp"] > self.ttl
            )
            active_entries = total_entries - expired_entries

            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "ttl": self.ttl
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
