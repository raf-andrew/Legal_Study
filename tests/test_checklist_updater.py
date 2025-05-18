#!/usr/bin/env python3
"""
Tests for the checklist updater.
"""
import os
import pytest
from pathlib import Path
from scripts.update_checklist_files import ChecklistUpdater
from scripts.test_tracker import TestTracker

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
def test_tracker(tmp_path):
    """Create a TestTracker instance with sample data."""
    tracker = TestTracker()

    # Add sample checklist items
    items = {
        "TESTCLI-FIRSTITE": {
            "id": "TESTCLI-FIRSTITE",
            "description": "First item",
            "status": "in_progress",
            "test_coverage": 100.0,
            "last_updated": "2024-03-20",
            "test_results": [],
            "dependencies": []
        },
        "TESTCLI-SECONDI": {
            "id": "TESTCLI-SECONDI",
            "description": "Second item",
            "status": "in_progress",
            "test_coverage": 50.0,
            "last_updated": "2024-03-20",
            "test_results": [],
            "dependencies": []
        },
        "TESTCLI-COMPLETE": {
            "id": "TESTCLI-COMPLETE",
            "description": "Completed item",
            "status": "completed",
            "test_coverage": 100.0,
            "last_updated": "2024-03-20",
            "test_results": [],
            "dependencies": []
        },
        "TESTCLI-ANOTHERI": {
            "id": "TESTCLI-ANOTHERI",
            "description": "Another item",
            "status": "in_progress",
            "test_coverage": 0.0,
            "last_updated": "2024-03-20",
            "test_results": [],
            "dependencies": []
        }
    }

    tracker._save_checklist_items(items)
    return tracker

@pytest.fixture
def updater(temp_checklist_dir, test_tracker):
    """Create a ChecklistUpdater instance with the temporary directory."""
    return ChecklistUpdater(str(temp_checklist_dir))

def test_update_checklist_files(updater, temp_checklist_dir):
    """Test updating checklist files based on test results."""
    success = updater.update_checklist_files()
    assert success

    # Verify that the checklist file was updated
    checklist_file = temp_checklist_dir / "test_checklist.md"
    content = checklist_file.read_text()

    # Check that items were updated correctly
    assert "- [x] First item" in content  # 100% coverage
    assert "- [ ] Second item" in content  # 50% coverage
    assert "- [x] Completed item" in content  # 100% coverage
    assert "- [ ] Another item" in content  # 0% coverage

def test_update_empty_directory(tmp_path):
    """Test updating from an empty directory."""
    updater = ChecklistUpdater(str(tmp_path))
    success = updater.update_checklist_files()
    assert not success

def test_update_with_no_items(temp_checklist_dir):
    """Test updating with no checklist items."""
    updater = ChecklistUpdater(str(temp_checklist_dir))
    success = updater.update_checklist_files()
    assert not success

def test_group_items_by_checklist(updater, test_tracker):
    """Test grouping items by checklist file."""
    items = test_tracker._load_checklist_items()
    checklist_items = updater._group_items_by_checklist(items)

    assert len(checklist_items) == 1
    assert len(checklist_items[list(checklist_items.keys())[0]]) == 4

def test_get_checklist_name(updater, temp_checklist_dir):
    """Test getting checklist name from a file."""
    checklist_file = temp_checklist_dir / "test_checklist.md"
    name = updater._get_checklist_name(checklist_file)
    assert name == "TESTCLI"

def test_update_item_in_content(updater):
    """Test updating an item in the content."""
    content = """# Test Checklist

- [ ] First item
- [ ] Second item
"""

    item = {
        "id": "TESTCLI-FIRSTITE",
        "description": "First item",
        "test_coverage": 100.0
    }

    updated_content = updater._update_item_in_content(content, item)
    assert "- [x] First item" in updated_content
    assert "- [ ] Second item" in updated_content

def test_update_nonexistent_item(updater):
    """Test updating a nonexistent item."""
    content = """# Test Checklist

- [ ] First item
"""

    item = {
        "id": "TESTCLI-NONEXIST",
        "description": "Nonexistent item",
        "test_coverage": 100.0
    }

    updated_content = updater._update_item_in_content(content, item)
    assert content == updated_content  # Content should be unchanged
