"""Unit tests for mock cache service."""
import pytest
import yaml
import time
from typing import Dict, Any
from datetime import datetime, timedelta
from ..mocks.services.cache import MockCache, CacheEntry

@pytest.fixture
def config() -> Dict[str, Any]:
    """Load test configuration."""
    with open(".config/mock.yaml") as f:
        config = yaml.safe_load(f)
    return config["cache"]

@pytest.fixture
def cache_service(config) -> MockCache:
    """Create mock cache service instance."""
    return MockCache("test_cache", config)

def test_service_initialization(cache_service):
    """Test service initialization."""
    assert cache_service.name == "test_cache"
    assert cache_service._data == {}
    assert cache_service._default_ttl == 3600
    assert cache_service._max_size == 1000
    assert cache_service._eviction_policy == "lru"

def test_service_start(cache_service):
    """Test service start."""
    cache_service.start()
    assert cache_service._default_ttl == 3600
    assert cache_service._max_size == 1000
    assert cache_service._eviction_policy == "lru"

def test_service_stop(cache_service):
    """Test service stop."""
    cache_service.set("key", "value")
    assert len(cache_service._data) == 1
    
    cache_service.stop()
    assert len(cache_service._data) == 0

def test_service_reset(cache_service):
    """Test service reset."""
    cache_service.set("key", "value")
    assert len(cache_service._data) == 1
    
    cache_service.reset()
    assert len(cache_service._data) == 0

def test_set_get(cache_service):
    """Test setting and getting cache entries."""
    cache_service.set("key", "value")
    assert cache_service.get("key") == "value"

def test_set_get_with_ttl(cache_service):
    """Test setting and getting cache entries with TTL."""
    cache_service.set("key", "value", ttl=1)
    assert cache_service.get("key") == "value"
    
    time.sleep(1.1)  # Wait for expiration
    assert cache_service.get("key") is None

def test_get_default(cache_service):
    """Test getting non-existent key with default value."""
    assert cache_service.get("nonexistent", "default") == "default"

def test_delete(cache_service):
    """Test deleting cache entries."""
    cache_service.set("key", "value")
    assert cache_service.delete("key") is True
    assert cache_service.get("key") is None
    assert cache_service.delete("nonexistent") is False

def test_exists(cache_service):
    """Test checking key existence."""
    cache_service.set("key", "value")
    assert cache_service.exists("key") is True
    assert cache_service.exists("nonexistent") is False

def test_exists_expired(cache_service):
    """Test checking existence of expired key."""
    cache_service.set("key", "value", ttl=1)
    assert cache_service.exists("key") is True
    
    time.sleep(1.1)  # Wait for expiration
    assert cache_service.exists("key") is False

def test_clear(cache_service):
    """Test clearing all entries."""
    cache_service.set("key1", "value1")
    cache_service.set("key2", "value2")
    assert len(cache_service._data) == 2
    
    assert cache_service.clear() is True
    assert len(cache_service._data) == 0

def test_get_stats(cache_service):
    """Test getting cache statistics."""
    cache_service.set("key1", "value1")
    cache_service.set("key2", "value2", ttl=1)
    cache_service.get("key1")
    cache_service.get("key1")
    
    time.sleep(1.1)  # Wait for key2 to expire
    
    stats = cache_service.get_stats()
    assert stats["total_entries"] == 2
    assert stats["expired_entries"] == 1
    assert stats["hit_count"] == 2
    assert stats["max_size"] == 1000
    assert stats["eviction_policy"] == "lru"
    assert stats["default_ttl"] == 3600

def test_get_keys(cache_service):
    """Test getting all non-expired keys."""
    cache_service.set("key1", "value1")
    cache_service.set("key2", "value2", ttl=1)
    assert set(cache_service.get_keys()) == {"key1", "key2"}
    
    time.sleep(1.1)  # Wait for key2 to expire
    assert set(cache_service.get_keys()) == {"key1"}

def test_touch(cache_service):
    """Test updating entry TTL."""
    cache_service.set("key", "value", ttl=2)
    time.sleep(1)  # Wait half the TTL
    
    assert cache_service.touch("key", ttl=2) is True
    time.sleep(1)  # Original TTL would have expired
    assert cache_service.get("key") == "value"
    
    time.sleep(1.1)  # New TTL expires
    assert cache_service.get("key") is None

def test_eviction_lru(cache_service):
    """Test LRU eviction policy."""
    cache_service._max_size = 2
    
    cache_service.set("key1", "value1")
    cache_service.set("key2", "value2")
    cache_service.get("key1")  # Access key1
    cache_service.set("key3", "value3")  # Should evict key2
    
    assert cache_service.get("key1") == "value1"
    assert cache_service.get("key2") is None
    assert cache_service.get("key3") == "value3"

def test_eviction_lfu(cache_service):
    """Test LFU eviction policy."""
    cache_service._max_size = 2
    cache_service._eviction_policy = "lfu"
    
    cache_service.set("key1", "value1")
    cache_service.set("key2", "value2")
    cache_service.get("key1")  # Access key1
    cache_service.get("key1")  # Access key1 again
    cache_service.set("key3", "value3")  # Should evict key2
    
    assert cache_service.get("key1") == "value1"
    assert cache_service.get("key2") is None
    assert cache_service.get("key3") == "value3"

def test_eviction_fifo(cache_service):
    """Test FIFO eviction policy."""
    cache_service._max_size = 2
    cache_service._eviction_policy = "fifo"
    
    cache_service.set("key1", "value1")
    cache_service.set("key2", "value2")
    cache_service.get("key1")  # Access shouldn't matter
    cache_service.set("key3", "value3")  # Should evict key1
    
    assert cache_service.get("key1") is None
    assert cache_service.get("key2") == "value2"
    assert cache_service.get("key3") == "value3"

def test_metrics_recording(cache_service):
    """Test metrics recording."""
    cache_service.set("key", "value")
    cache_service.get("key")
    
    metrics = cache_service.get_metrics()
    assert metrics["total_calls"] == 2
    assert metrics["total_errors"] == 0

def test_error_recording(cache_service):
    """Test error recording."""
    cache_service._max_size = -1  # Invalid size
    
    with pytest.raises(Exception):
        cache_service.set("key", "value")
    
    errors = cache_service.get_errors()
    assert len(errors) == 1

def test_call_recording(cache_service):
    """Test call recording."""
    cache_service.set("key", "value")
    cache_service.get("key")
    
    calls = cache_service.get_calls()
    assert len(calls) == 2
    assert calls[0]["method"] == "set"
    assert calls[1]["method"] == "get" 