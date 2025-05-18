#!/usr/bin/env python3
"""
Tests for the checklist initializer.
"""
import os
import pytest
from pathlib import Path
from scripts.init_checklist_items import ChecklistInitializer

@pytest.fixture
def temp_checklist_dir(tmp_path):
    """Create a temporary directory with sample checklist files."""
    checklist_dir = tmp_path / "checklists"
    checklist_dir.mkdir()

    # Create a sample checklist file
    checklist_file = checklist_dir / "test_checklist.md"
    checklist_file.write_text("""# Test Checklist

- [ ] First item
- [ ] Second item
- [x] Completed item
- [ ] Another item
""")

    return checklist_dir

@pytest.fixture
def initializer(temp_checklist_dir):
    """Create a ChecklistInitializer instance with the temporary directory."""
    return ChecklistInitializer(str(temp_checklist_dir))

def test_initialize_checklist_items(initializer, temp_checklist_dir):
    """Test initializing checklist items from a directory."""
    success = initializer.initialize_checklist_items()
    assert success

    # Verify that items were created
    items = initializer.tracker._load_checklist_items()
    assert len(items) == 4

    # Verify item properties
    first_item = items["TESTCLI-FIRSTITE"]
    assert first_item["description"] == "First item"
    assert first_item["status"] == "in_progress"
    assert first_item["test_coverage"] == 0.0
    assert first_item["test_results"] == []
    assert first_item["dependencies"] == []

def test_initialize_empty_directory(tmp_path):
    """Test initializing from an empty directory."""
    initializer = ChecklistInitializer(str(tmp_path))
    success = initializer.initialize_checklist_items()
    assert not success

def test_initialize_invalid_file(temp_checklist_dir):
    """Test initializing with an invalid checklist file."""
    invalid_file = temp_checklist_dir / "invalid.md"
    invalid_file.write_text("This is not a valid checklist")

    initializer = ChecklistInitializer(str(temp_checklist_dir))
    success = initializer.initialize_checklist_items()
    assert success  # Should still succeed, just skip invalid file

    items = initializer.tracker._load_checklist_items()
    assert len(items) == 4  # Only valid items should be included

def test_generate_item_id(initializer):
    """Test generating unique item IDs."""
    # Test with normal text
    id1 = initializer._generate_item_id("Test Checklist", "First item")
    assert id1 == "TESTCLI-FIRSTITE"

    # Test with special characters
    id2 = initializer._generate_item_id("Test-Checklist!", "Item with spaces")
    assert id2 == "TESTCLI-ITEMWIT"

    # Test with empty text
    id3 = initializer._generate_item_id("", "")
    assert id3 == "CLI-ITEM"

def test_parse_checklist_file(initializer, temp_checklist_dir):
    """Test parsing a checklist file."""
    checklist_file = temp_checklist_dir / "test_checklist.md"
    items = initializer._parse_checklist_file(checklist_file)

    assert len(items) == 4
    assert "TESTCLI-FIRSTITE" in items
    assert "TESTCLI-SECONDI" in items
    assert "TESTCLI-COMPLETE" in items
    assert "TESTCLI-ANOTHERI" in items

def test_parse_nonexistent_file(initializer):
    """Test parsing a nonexistent file."""
    items = initializer._parse_checklist_file(Path("nonexistent.md"))
    assert len(items) == 0
