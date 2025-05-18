"""Unit tests for mock database service."""
import pytest
import yaml
from typing import Dict, Any
from datetime import datetime
from ..mocks.services.database import MockDatabase, MockTable

@pytest.fixture
def config() -> Dict[str, Any]:
    """Load test configuration."""
    with open(".config/mock.yaml") as f:
        config = yaml.safe_load(f)
    return config["database"]

@pytest.fixture
def db_service(config) -> MockDatabase:
    """Create mock database service instance."""
    return MockDatabase("test_db", config)

@pytest.fixture
def test_table() -> Dict[str, Any]:
    """Test table configuration."""
    return {
        "name": "test",
        "columns": [
            {"name": "id", "type": "string", "primary_key": True},
            {"name": "name", "type": "string", "unique": True},
            {"name": "value", "type": "string"},
            {"name": "created_at", "type": "datetime"}
        ]
    }

def test_service_initialization(db_service):
    """Test service initialization."""
    assert db_service.name == "test_db"
    assert db_service._tables == {}

def test_service_start(db_service):
    """Test service start."""
    db_service.start()
    assert "users" in db_service._tables
    assert "documents" in db_service._tables
    assert "comments" in db_service._tables

def test_service_stop(db_service):
    """Test service stop."""
    db_service.start()
    assert len(db_service._tables) > 0
    
    db_service.stop()
    assert len(db_service._tables) == 0

def test_service_reset(db_service):
    """Test service reset."""
    db_service.start()
    original_tables = set(db_service._tables.keys())
    
    # Modify state
    db_service._tables.clear()
    
    # Reset
    db_service.reset()
    assert set(db_service._tables.keys()) == original_tables

def test_create_table(db_service, test_table):
    """Test creating a table."""
    table = db_service.create_table(test_table["name"], test_table["columns"])
    
    assert isinstance(table, MockTable)
    assert table.name == test_table["name"]
    assert table.columns == test_table["columns"]
    assert table.data == []
    assert len(table.indexes) == 2  # id and name columns

def test_create_duplicate_table(db_service, test_table):
    """Test creating a duplicate table."""
    db_service.create_table(test_table["name"], test_table["columns"])
    
    with pytest.raises(ValueError):
        db_service.create_table(test_table["name"], test_table["columns"])

def test_get_table(db_service, test_table):
    """Test getting a table."""
    created_table = db_service.create_table(test_table["name"], test_table["columns"])
    retrieved_table = db_service.get_table(test_table["name"])
    
    assert retrieved_table is created_table

def test_list_tables(db_service):
    """Test listing tables."""
    db_service.start()
    tables = db_service.list_tables()
    
    assert "users" in tables
    assert "documents" in tables
    assert "comments" in tables

def test_insert_record(db_service, test_table):
    """Test inserting a record."""
    db_service.create_table(test_table["name"], test_table["columns"])
    
    record = {
        "id": "1",
        "name": "test",
        "value": "test value"
    }
    
    record_id = db_service.insert(test_table["name"], record)
    assert record_id == "1"
    
    table = db_service.get_table(test_table["name"])
    assert len(table.data) == 1
    assert table.data[0]["id"] == "1"
    assert table.data[0]["name"] == "test"
    assert table.data[0]["value"] == "test value"
    assert "created_at" in table.data[0]

def test_insert_duplicate_key(db_service, test_table):
    """Test inserting a record with duplicate key."""
    db_service.create_table(test_table["name"], test_table["columns"])
    
    record1 = {"id": "1", "name": "test1", "value": "value1"}
    record2 = {"id": "1", "name": "test2", "value": "value2"}
    
    db_service.insert(test_table["name"], record1)
    with pytest.raises(ValueError):
        db_service.insert(test_table["name"], record2)

def test_find_records(db_service, test_table):
    """Test finding records."""
    db_service.create_table(test_table["name"], test_table["columns"])
    
    records = [
        {"id": "1", "name": "test1", "value": "value1"},
        {"id": "2", "name": "test2", "value": "value1"},
        {"id": "3", "name": "test3", "value": "value2"}
    ]
    
    for record in records:
        db_service.insert(test_table["name"], record)
    
    results = db_service.find(test_table["name"], {"value": "value1"})
    assert len(results) == 2
    assert results[0]["id"] in ["1", "2"]
    assert results[1]["id"] in ["1", "2"]

def test_find_one_record(db_service, test_table):
    """Test finding one record."""
    db_service.create_table(test_table["name"], test_table["columns"])
    
    records = [
        {"id": "1", "name": "test1", "value": "value1"},
        {"id": "2", "name": "test2", "value": "value1"}
    ]
    
    for record in records:
        db_service.insert(test_table["name"], record)
    
    result = db_service.find_one(test_table["name"], {"value": "value1"})
    assert result is not None
    assert result["id"] in ["1", "2"]

def test_update_records(db_service, test_table):
    """Test updating records."""
    db_service.create_table(test_table["name"], test_table["columns"])
    
    records = [
        {"id": "1", "name": "test1", "value": "value1"},
        {"id": "2", "name": "test2", "value": "value1"},
        {"id": "3", "name": "test3", "value": "value2"}
    ]
    
    for record in records:
        db_service.insert(test_table["name"], record)
    
    count = db_service.update(
        test_table["name"],
        {"value": "value1"},
        {"value": "updated"}
    )
    
    assert count == 2
    results = db_service.find(test_table["name"], {"value": "updated"})
    assert len(results) == 2

def test_delete_records(db_service, test_table):
    """Test deleting records."""
    db_service.create_table(test_table["name"], test_table["columns"])
    
    records = [
        {"id": "1", "name": "test1", "value": "value1"},
        {"id": "2", "name": "test2", "value": "value1"},
        {"id": "3", "name": "test3", "value": "value2"}
    ]
    
    for record in records:
        db_service.insert(test_table["name"], record)
    
    count = db_service.delete(test_table["name"], {"value": "value1"})
    assert count == 2
    
    results = db_service.find(test_table["name"], {})
    assert len(results) == 1
    assert results[0]["id"] == "3"

def test_metrics_recording(db_service, test_table):
    """Test metrics recording."""
    db_service.create_table(test_table["name"], test_table["columns"])
    
    record = {"id": "1", "name": "test", "value": "test"}
    db_service.insert(test_table["name"], record)
    
    metrics = db_service.get_metrics()
    assert metrics["total_calls"] == 1
    assert metrics["total_errors"] == 0

def test_error_recording(db_service):
    """Test error recording."""
    with pytest.raises(ValueError):
        db_service.insert("nonexistent", {})
    
    errors = db_service.get_errors()
    assert len(errors) == 1
    assert errors[0]["error"] == "Table not found: nonexistent"

def test_call_recording(db_service, test_table):
    """Test call recording."""
    db_service.create_table(test_table["name"], test_table["columns"])
    
    record = {"id": "1", "name": "test", "value": "test"}
    db_service.insert(test_table["name"], record)
    
    calls = db_service.get_calls()
    assert len(calls) == 1
    assert calls[0]["method"] == "insert"
    assert calls[0]["args"] == (test_table["name"],) 