#!/usr/bin/env python3
"""
Tests for the test tracking system.
"""
import os
import json
import pytest
from datetime import datetime
from pathlib import Path
from scripts.test_tracker import TestTracker, TestResult, ChecklistItem

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary test data directory."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir

@pytest.fixture
def tracker(test_data_dir):
    """Create a TestTracker instance with temporary data directory."""
    return TestTracker(str(test_data_dir))

@pytest.fixture
def sample_test_result():
    """Create a sample test result."""
    return TestResult(
        test_name="test_checklist_validation",
        status="passed",
        coverage=100.0,
        timestamp=datetime.now().isoformat(),
        details={"duration": 1.5, "assertions": 10},
        checklist_items=["CLI-001", "CLI-002"]
    )

@pytest.fixture
def sample_checklist_item():
    """Create a sample checklist item."""
    return ChecklistItem(
        id="CLI-001",
        description="Validate checklist format",
        status="in_progress",
        test_coverage=0.0,
        last_updated=datetime.now().isoformat(),
        test_results=[],
        dependencies=[]
    )

def test_record_test_result(tracker, sample_test_result):
    """Test recording a test result."""
    # Record test result
    success = tracker.record_test_result(sample_test_result)
    assert success

    # Verify test result was saved
    test_results = tracker._load_test_results()
    assert sample_test_result.test_name in test_results
    assert test_results[sample_test_result.test_name]["status"] == "passed"
    assert test_results[sample_test_result.test_name]["coverage"] == 100.0

def test_get_checklist_status(tracker, sample_test_result, sample_checklist_item):
    """Test getting checklist item status."""
    # Initialize checklist item
    checklist_items = {sample_checklist_item.id: {
        "id": sample_checklist_item.id,
        "description": sample_checklist_item.description,
        "status": sample_checklist_item.status,
        "test_coverage": sample_checklist_item.test_coverage,
        "last_updated": sample_checklist_item.last_updated,
        "test_results": sample_checklist_item.test_results,
        "dependencies": sample_checklist_item.dependencies
    }}
    tracker._save_checklist_items(checklist_items)

    # Record test result
    tracker.record_test_result(sample_test_result)

    # Get checklist status
    status = tracker.get_checklist_status(sample_checklist_item.id)
    assert status is not None
    assert status["status"] == "completed"
    assert status["test_coverage"] == 100.0
    assert sample_test_result.test_name in status["test_results"]

def test_get_test_coverage(tracker, sample_test_result, sample_checklist_item):
    """Test getting test coverage for a checklist item."""
    # Initialize checklist item
    checklist_items = {sample_checklist_item.id: {
        "id": sample_checklist_item.id,
        "description": sample_checklist_item.description,
        "status": sample_checklist_item.status,
        "test_coverage": sample_checklist_item.test_coverage,
        "last_updated": sample_checklist_item.last_updated,
        "test_results": sample_checklist_item.test_results,
        "dependencies": sample_checklist_item.dependencies
    }}
    tracker._save_checklist_items(checklist_items)

    # Record test result
    tracker.record_test_result(sample_test_result)

    # Get test coverage
    coverage = tracker.get_test_coverage(sample_checklist_item.id)
    assert coverage == 100.0

def test_is_item_completed(tracker, sample_test_result, sample_checklist_item):
    """Test checking if a checklist item is completed."""
    # Initialize checklist item
    checklist_items = {sample_checklist_item.id: {
        "id": sample_checklist_item.id,
        "description": sample_checklist_item.description,
        "status": sample_checklist_item.status,
        "test_coverage": sample_checklist_item.test_coverage,
        "last_updated": sample_checklist_item.last_updated,
        "test_results": sample_checklist_item.test_results,
        "dependencies": sample_checklist_item.dependencies
    }}
    tracker._save_checklist_items(checklist_items)

    # Record test result
    tracker.record_test_result(sample_test_result)

    # Check completion status
    assert tracker.is_item_completed(sample_checklist_item.id)

def test_get_incomplete_items(tracker, sample_test_result, sample_checklist_item):
    """Test getting incomplete checklist items."""
    # Initialize checklist items
    checklist_items = {
        sample_checklist_item.id: {
            "id": sample_checklist_item.id,
            "description": sample_checklist_item.description,
            "status": sample_checklist_item.status,
            "test_coverage": sample_checklist_item.test_coverage,
            "last_updated": sample_checklist_item.last_updated,
            "test_results": sample_checklist_item.test_results,
            "dependencies": sample_checklist_item.dependencies
        },
        "CLI-002": {
            "id": "CLI-002",
            "description": "Another checklist item",
            "status": "in_progress",
            "test_coverage": 50.0,
            "last_updated": datetime.now().isoformat(),
            "test_results": [],
            "dependencies": []
        }
    }
    tracker._save_checklist_items(checklist_items)

    # Record test result
    tracker.record_test_result(sample_test_result)

    # Get incomplete items
    incomplete_items = tracker.get_incomplete_items()
    assert len(incomplete_items) == 1
    assert incomplete_items[0]["id"] == "CLI-002"
    assert incomplete_items[0]["test_coverage"] == 50.0

def test_invalid_test_result(tracker):
    """Test handling invalid test result."""
    # Create invalid test result (missing required fields)
    invalid_result = TestResult(
        test_name="invalid_test",
        status="failed",
        coverage=-1.0,  # Invalid coverage
        timestamp=datetime.now().isoformat(),
        details={},
        checklist_items=[]
    )

    # Try to record invalid result
    success = tracker.record_test_result(invalid_result)
    assert not success

def test_missing_checklist_item(tracker, sample_test_result):
    """Test handling test result for non-existent checklist item."""
    # Record test result for non-existent checklist item
    success = tracker.record_test_result(sample_test_result)
    assert success  # Should still record the test result

    # Verify checklist item wasn't created
    status = tracker.get_checklist_status(sample_test_result.checklist_items[0])
    assert status is None
