"""Unit tests for cache initialization command."""

import os
import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

from ..commands.init.cache import CacheInitCommand
from ..mocks.registry import MockServiceRegistry

@pytest.fixture
def mock_registry():
    """Create mock service registry."""
    registry = MagicMock(spec=MockServiceRegistry)
    registry.list_services.return_value = ["api", "database", "cache"]
    return registry

@pytest.fixture
def mock_cache_service():
    """Create mock cache service."""
    cache_service = MagicMock()
    
    # Configuration
    cache_service.apply_config.return_value = {"status": "success"}
    cache_service.apply_default_config.return_value = {"status": "success"}
    cache_service.get_config.return_value = {
        "max_size": "1GB",
        "eviction_policy": "LRU",
        "ttl": 3600
    }
    cache_service.reset_config.return_value = {"status": "success"}
    
    # Initialization
    cache_service.initialize.return_value = {"status": "success"}
    
    # Cache operations
    cache_service.clear.return_value = {"status": "success"}
    cache_service.get_stats.return_value = {
        "size": "100MB",
        "items": 1000,
        "hits": 5000,
        "misses": 1000
    }
    
    # Warm-up
    cache_service.get_warm_up_queries.return_value = [
        "query1",
        "query2"
    ]
    cache_service.execute_warm_up_query.return_value = {
        "status": "success",
        "cached": True
    }
    
    # Service operations
    cache_service.stop.return_value = {"status": "success"}
    
    return cache_service

@pytest.fixture
def cache_init(mock_registry):
    """Create cache initialization command instance."""
    return CacheInitCommand(mock_registry)

def test_cache_init_initialization(cache_init):
    """Test cache initialization command initialization."""
    assert cache_init.name == "init-cache"
    assert cache_init.description == "Initialize cache service and configuration"
    assert isinstance(cache_init.registry, MagicMock)

def test_cache_init_validation(cache_init):
    """Test cache initialization command validation."""
    assert cache_init.validate() is None
    assert cache_init.validate(config="config.json") is None
    assert cache_init.validate(warm_up=True) is None
    assert cache_init.validate(clear=True) is None
    assert cache_init.validate(config=123) == "Config file must be a string"
    assert cache_init.validate(warm_up="true") == "Warm-up flag must be a boolean"
    assert cache_init.validate(clear="true") == "Clear flag must be a boolean"

def test_cache_init_execution(cache_init, mock_registry, mock_cache_service):
    """Test cache initialization command execution."""
    mock_registry.get_service.return_value = mock_cache_service
    
    with patch("builtins.open", mock_open(read_data="test config")):
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = cache_init.execute(
                config="config.json",
                warm_up=True,
                clear=True
            )
    
    assert result["status"] == "success"
    assert result["setup"]["status"] == "success"
    assert result["clear"]["status"] == "success"
    assert result["warm_up"]["status"] == "success"

def test_cache_init_no_service(cache_init, mock_registry):
    """Test cache initialization without cache service."""
    mock_registry.get_service.return_value = None
    
    result = cache_init.execute()
    assert result["status"] == "error"
    assert "Cache service not available" in result["error"]

def test_cache_init_setup_error(cache_init, mock_registry, mock_cache_service):
    """Test cache initialization with setup error."""
    mock_cache_service.apply_config.side_effect = Exception("Setup error")
    mock_registry.get_service.return_value = mock_cache_service
    
    with patch("builtins.open", mock_open(read_data="test config")):
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = cache_init.execute(config="config.json")
    
    assert result["status"] == "error"
    assert result["setup"]["status"] == "error"
    assert "Setup error" in result["setup"]["error"]

def test_cache_init_clear_error(cache_init, mock_registry, mock_cache_service):
    """Test cache initialization with clear error."""
    mock_cache_service.clear.side_effect = Exception("Clear error")
    mock_registry.get_service.return_value = mock_cache_service
    
    result = cache_init.execute(clear=True)
    assert result["status"] == "error"
    assert result["clear"]["status"] == "error"
    assert "Clear error" in result["clear"]["error"]

def test_cache_init_warm_up_error(cache_init, mock_registry, mock_cache_service):
    """Test cache initialization with warm-up error."""
    mock_cache_service.execute_warm_up_query.side_effect = Exception("Warm-up error")
    mock_registry.get_service.return_value = mock_cache_service
    
    result = cache_init.execute(warm_up=True)
    assert result["status"] == "error"
    assert result["warm_up"]["status"] == "error"
    assert "Warm-up error" in result["warm_up"]["error"]

def test_cache_init_file_not_found(cache_init, mock_registry, mock_cache_service):
    """Test cache initialization with missing file."""
    mock_registry.get_service.return_value = mock_cache_service
    
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False
        result = cache_init.execute(config="missing.json")
    
    assert result["status"] == "error"
    assert result["setup"]["status"] == "error"
    assert "File not found" in result["setup"]["error"]

def test_cache_init_file_read_error(cache_init, mock_registry, mock_cache_service):
    """Test cache initialization with file read error."""
    mock_registry.get_service.return_value = mock_cache_service
    
    with patch("builtins.open") as mock_open:
        mock_open.side_effect = IOError("Read error")
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = cache_init.execute(config="config.json")
    
    assert result["status"] == "error"
    assert result["setup"]["status"] == "error"
    assert "Failed to read file" in result["setup"]["error"]

def test_cache_init_reset(cache_init, mock_registry, mock_cache_service):
    """Test cache initialization reset."""
    mock_registry.get_service.return_value = mock_cache_service
    
    result = cache_init.reset(mock_cache_service)
    assert result["status"] == "success"
    assert result["clear"]["status"] == "success"

def test_cache_init_reset_error(cache_init, mock_registry, mock_cache_service):
    """Test cache initialization reset with error."""
    mock_cache_service.reset_config.side_effect = Exception("Reset error")
    mock_registry.get_service.return_value = mock_cache_service
    
    result = cache_init.reset(mock_cache_service)
    assert result["status"] == "error"
    assert "Reset error" in result["error"] 