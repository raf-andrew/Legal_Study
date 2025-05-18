#!/usr/bin/env python3
"""
Tests for checklist automation system.
"""
import os
import pytest
from pathlib import Path
from scripts.validate_checklists import ChecklistValidator
from scripts.update_checklists import ChecklistUpdater

@pytest.fixture
def checklist_dir(tmp_path):
    """Create a temporary checklist directory with test files."""
    checklist_dir = tmp_path / "checklists"
    checklist_dir.mkdir()

    # Create a valid checklist
    valid_checklist = checklist_dir / "valid_checklist.md"
    valid_checklist.write_text("""# Valid Checklist

## Test Framework
- [ ] Test framework setup
- [ ] Test utilities
- [ ] Test documentation

## Test Cases
- [ ] Unit tests
- [ ] Integration tests
- [ ] E2E tests

## Test Data
- [ ] Test data setup
- [ ] Test data cleanup
""")

    # Create an invalid checklist
    invalid_checklist = checklist_dir / "invalid_checklist.md"
    invalid_checklist.write_text("""Invalid Checklist
No sections or checkboxes
""")

    return checklist_dir

def test_checklist_validator_format(checklist_dir):
    """Test checklist format validation."""
    validator = ChecklistValidator()
    validator.checklist_dir = checklist_dir

    results = validator.validate_all_checklists()

    assert "valid_checklist.md" not in results
    assert "invalid_checklist.md" in results
    assert "Invalid checklist format" in results["invalid_checklist.md"]

def test_checklist_validator_content(checklist_dir):
    """Test checklist content validation."""
    validator = ChecklistValidator()
    validator.checklist_dir = checklist_dir

    # Add a checklist missing required sections
    incomplete_checklist = checklist_dir / "incomplete_checklist.md"
    incomplete_checklist.write_text("""# Incomplete Checklist

## Test Framework
- [ ] Test framework setup
""")

    results = validator.validate_all_checklists()

    assert "incomplete_checklist.md" in results
    assert any("Missing required section" in error for error in results["incomplete_checklist.md"])

def test_checklist_updater(checklist_dir, monkeypatch):
    """Test checklist updater."""
    # Mock GitHub token and repository
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "test/repo")

    updater = ChecklistUpdater()
    updater.checklist_dir = checklist_dir

    # Test updating checklists
    results = updater.update_all_checklists()

    assert len(results) > 0
    assert all(isinstance(success, bool) for success in results.values())

def test_checklist_updater_no_github(checklist_dir, monkeypatch):
    """Test checklist updater without GitHub credentials."""
    # Remove GitHub token
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)

    updater = ChecklistUpdater()
    updater.checklist_dir = checklist_dir

    # Test updating checklists without GitHub
    results = updater.update_all_checklists()

    assert len(results) > 0
    assert all(isinstance(success, bool) for success in results.values())

def test_checklist_updater_checkbox_update(checklist_dir):
    """Test checkbox update functionality."""
    updater = ChecklistUpdater()

    # Create test content
    content = """# Test Checklist
- [ ] Task 1
- [ ] Task 2
- [x] Task 3
"""

    # Test updating checkboxes
    test_results = {
        "Task 1": True,
        "Task 2": False,
        "Task 3": True
    }

    updated_content = updater._update_checkboxes(content, test_results)

    assert "- [x] Task 1" in updated_content
    assert "- [ ] Task 2" in updated_content
    assert "- [x] Task 3" in updated_content
