"""Tests for key rotation utility."""

import pytest
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from app.core.key_rotation import KeyRotation

@pytest.fixture
def test_key_file(tmp_path):
    """Create a temporary key file."""
    return str(tmp_path / "test_keys.json")

@pytest.fixture
def key_rotation(test_key_file):
    """Create a key rotation instance."""
    return KeyRotation(test_key_file)

def test_generate_key(key_rotation):
    """Test key generation."""
    key = key_rotation.generate_key()
    assert isinstance(key, str)
    assert len(key) >= 32

def test_key_rotation(key_rotation):
    """Test key rotation."""
    # Initial rotation
    current1, previous1 = key_rotation.rotate_key("test_key")
    assert current1 is not None
    assert previous1 is None
    
    # Second rotation
    current2, previous2 = key_rotation.rotate_key("test_key")
    assert current2 is not None
    assert current2 != current1
    assert previous2 == current1

def test_key_storage(test_key_file, key_rotation):
    """Test key storage."""
    # Generate and store key
    key_rotation.rotate_key("test_key")
    
    # Check file exists
    assert Path(test_key_file).exists()
    
    # Check file content
    with open(test_key_file) as f:
        data = json.load(f)
    assert "test_key" in data
    assert "current" in data["test_key"]
    assert "previous" in data["test_key"]
    assert "rotated_at" in data["test_key"]
    assert "expires_at" in data["test_key"]

def test_key_expiration(test_key_file):
    """Test key expiration."""
    # Create key with short expiration
    rotation = KeyRotation(test_key_file)
    current, _ = rotation.rotate_key("test_key", expiry_days=0)
    
    # Wait for expiration
    assert rotation.should_rotate("test_key")
    
    # Rotate and verify
    new_current = rotation.rotate_if_needed("test_key")
    assert new_current != current

def test_get_key(key_rotation):
    """Test key retrieval."""
    # Generate key
    current, _ = key_rotation.rotate_key("test_key")
    
    # Get current key
    retrieved = key_rotation.get_key("test_key")
    assert retrieved == current
    
    # Get both keys
    current_key, previous_key = key_rotation.get_key("test_key", include_previous=True)
    assert current_key == current
    assert previous_key is None

def test_multiple_keys(key_rotation):
    """Test handling multiple keys."""
    # Generate two keys
    key1, _ = key_rotation.rotate_key("key1")
    key2, _ = key_rotation.rotate_key("key2")
    
    # Verify they're different
    assert key1 != key2
    
    # Rotate first key
    new_key1, old_key1 = key_rotation.rotate_key("key1")
    assert new_key1 != key1
    assert old_key1 == key1
    
    # Verify second key unchanged
    current_key2 = key_rotation.get_key("key2")
    assert current_key2 == key2

def test_key_rotation_error_handling(key_rotation, caplog):
    """Test error handling in key rotation."""
    # Test with invalid key name
    assert key_rotation.get_key("nonexistent") is None
    
    # Test with invalid file path
    invalid_rotation = KeyRotation("/invalid/path/keys.json")
    invalid_rotation.rotate_key("test_key")
    assert "Failed to save keys" in caplog.text

def test_automatic_rotation(key_rotation):
    """Test automatic key rotation."""
    # Create initial key
    initial_key = key_rotation.rotate_if_needed("test_key")
    assert initial_key is not None
    
    # Should not rotate if not needed
    current_key = key_rotation.rotate_if_needed("test_key")
    assert current_key == initial_key
    
    # Force expiration
    key_rotation.current_keys["test_key"]["expires_at"] = (
        datetime.utcnow() - timedelta(days=1)
    ).isoformat()
    
    # Should rotate
    new_key = key_rotation.rotate_if_needed("test_key")
    assert new_key != initial_key 