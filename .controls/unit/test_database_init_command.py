"""Unit tests for database initialization command."""

import os
import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime

from ..commands.init.database import DatabaseInitCommand
from ..mocks.registry import MockServiceRegistry

@pytest.fixture
def mock_registry():
    """Create mock service registry."""
    registry = MagicMock(spec=MockServiceRegistry)
    registry.list_services.return_value = ["api", "database", "cache"]
    return registry

@pytest.fixture
def mock_db_service():
    """Create mock database service."""
    db_service = MagicMock()
    
    # Database existence
    db_service.database_exists.return_value = False
    
    # Schema initialization
    db_service.create_database.return_value = {"status": "success"}
    db_service.execute_schema.return_value = {"status": "success"}
    db_service.execute_default_schema.return_value = {"status": "success"}
    
    # Data initialization
    db_service.load_data.return_value = {"status": "success", "records": 100}
    db_service.load_default_data.return_value = {"status": "success", "records": 50}
    
    # Migrations
    db_service.list_pending_migrations.return_value = ["001_init", "002_users"]
    db_service.run_migration.return_value = {"status": "success"}
    db_service.rollback_migrations.return_value = {"status": "success"}
    
    # Database operations
    db_service.drop_database.return_value = {"status": "success"}
    
    return db_service

@pytest.fixture
def database_init(mock_registry):
    """Create database initialization command instance."""
    return DatabaseInitCommand(mock_registry)

def test_database_init_initialization(database_init):
    """Test database initialization command initialization."""
    assert database_init.name == "init-database"
    assert database_init.description == "Initialize database schema and data"
    assert isinstance(database_init.registry, MagicMock)

def test_database_init_validation(database_init):
    """Test database initialization command validation."""
    assert database_init.validate() is None
    assert database_init.validate(schema="schema.sql") is None
    assert database_init.validate(data="data.sql") is None
    assert database_init.validate(force=True) is None
    assert database_init.validate(schema=123) == "Schema must be a string"
    assert database_init.validate(data=123) == "Data file must be a string"
    assert database_init.validate(force="true") == "Force flag must be a boolean"

def test_database_init_execution(database_init, mock_registry, mock_db_service):
    """Test database initialization command execution."""
    mock_registry.get_service.return_value = mock_db_service
    
    with patch("builtins.open", mock_open(read_data="test data")):
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = database_init.execute(
                schema="schema.sql",
                data="data.sql"
            )
    
    assert result["status"] == "success"
    assert result["schema"]["status"] == "success"
    assert result["data"]["status"] == "success"
    assert result["migrations"]["status"] == "success"

def test_database_init_no_service(database_init, mock_registry):
    """Test database initialization without database service."""
    mock_registry.get_service.return_value = None
    
    result = database_init.execute()
    assert result["status"] == "error"
    assert "Database service not available" in result["error"]

def test_database_init_existing_database(database_init, mock_registry, mock_db_service):
    """Test database initialization with existing database."""
    mock_db_service.database_exists.return_value = True
    mock_registry.get_service.return_value = mock_db_service
    
    result = database_init.execute()
    assert result["status"] == "error"
    assert "Database already exists" in result["error"]

def test_database_init_force(database_init, mock_registry, mock_db_service):
    """Test forced database initialization."""
    mock_db_service.database_exists.return_value = True
    mock_registry.get_service.return_value = mock_db_service
    
    result = database_init.execute(force=True)
    assert result["status"] == "success"

def test_database_init_schema_error(database_init, mock_registry, mock_db_service):
    """Test database initialization with schema error."""
    mock_db_service.execute_schema.side_effect = Exception("Schema error")
    mock_registry.get_service.return_value = mock_db_service
    
    with patch("builtins.open", mock_open(read_data="test data")):
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = database_init.execute(schema="schema.sql")
    
    assert result["status"] == "error"
    assert result["schema"]["status"] == "error"
    assert "Schema error" in result["schema"]["error"]

def test_database_init_data_error(database_init, mock_registry, mock_db_service):
    """Test database initialization with data error."""
    mock_db_service.load_data.side_effect = Exception("Data error")
    mock_registry.get_service.return_value = mock_db_service
    
    with patch("builtins.open", mock_open(read_data="test data")):
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = database_init.execute(data="data.sql")
    
    assert result["status"] == "error"
    assert result["data"]["status"] == "error"
    assert "Data error" in result["data"]["error"]

def test_database_init_migration_error(database_init, mock_registry, mock_db_service):
    """Test database initialization with migration error."""
    mock_db_service.run_migration.side_effect = Exception("Migration error")
    mock_registry.get_service.return_value = mock_db_service
    
    result = database_init.execute()
    assert result["status"] == "error"
    assert result["migrations"]["status"] == "error"
    assert any(
        "Migration error" in migration["error"]
        for migration in result["migrations"]["migrations"]
    )

def test_database_init_file_not_found(database_init, mock_registry, mock_db_service):
    """Test database initialization with missing file."""
    mock_registry.get_service.return_value = mock_db_service
    
    with patch("os.path.exists") as mock_exists:
        mock_exists.return_value = False
        result = database_init.execute(schema="missing.sql")
    
    assert result["status"] == "error"
    assert result["schema"]["status"] == "error"
    assert "File not found" in result["schema"]["error"]

def test_database_init_file_read_error(database_init, mock_registry, mock_db_service):
    """Test database initialization with file read error."""
    mock_registry.get_service.return_value = mock_db_service
    
    with patch("builtins.open") as mock_open:
        mock_open.side_effect = IOError("Read error")
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            result = database_init.execute(schema="schema.sql")
    
    assert result["status"] == "error"
    assert result["schema"]["status"] == "error"
    assert "Failed to read file" in result["schema"]["error"]

def test_database_init_rollback(database_init, mock_registry, mock_db_service):
    """Test database initialization rollback."""
    mock_registry.get_service.return_value = mock_db_service
    
    result = database_init.rollback(mock_db_service)
    assert result["status"] == "success"
    assert "migrations" in result

def test_database_init_rollback_error(database_init, mock_registry, mock_db_service):
    """Test database initialization rollback with error."""
    mock_db_service.rollback_migrations.side_effect = Exception("Rollback error")
    mock_registry.get_service.return_value = mock_db_service
    
    result = database_init.rollback(mock_db_service)
    assert result["status"] == "error"
    assert "Rollback error" in result["error"] 