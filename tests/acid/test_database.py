import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
import sqlite3
import os

client = TestClient(app)

@pytest.fixture
def test_db():
    """Create a test database."""
    db_path = "test.db"
    conn = sqlite3.connect(db_path)
    yield conn
    conn.close()
    os.remove(db_path)

@pytest.mark.acid
def test_atomicity(test_db):
    """Test atomicity of database transactions."""
    cursor = test_db.cursor()
    
    # Create test table
    cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
    
    try:
        # Start transaction
        cursor.execute("BEGIN")
        
        # Insert data
        cursor.execute("INSERT INTO test (value) VALUES (?)", ("test1",))
        cursor.execute("INSERT INTO test (value) VALUES (?)", ("test2",))
        
        # Simulate error
        raise Exception("Test error")
        
        # Commit (should not reach here)
        test_db.commit()
    except Exception:
        # Rollback on error
        test_db.rollback()
    
    # Verify no data was inserted
    cursor.execute("SELECT COUNT(*) FROM test")
    assert cursor.fetchone()[0] == 0

@pytest.mark.acid
def test_consistency(test_db):
    """Test consistency of database operations."""
    cursor = test_db.cursor()
    
    # Create test table with constraints
    cursor.execute("""
        CREATE TABLE test (
            id INTEGER PRIMARY KEY,
            value TEXT NOT NULL,
            CHECK (length(value) > 0)
        )
    """)
    
    # Test valid insert
    cursor.execute("INSERT INTO test (value) VALUES (?)", ("valid",))
    test_db.commit()
    
    # Test invalid insert (should fail)
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO test (value) VALUES (?)", ("",))
        test_db.commit()

@pytest.mark.acid
def test_isolation(test_db):
    """Test isolation of concurrent transactions."""
    cursor1 = test_db.cursor()
    cursor2 = test_db.cursor()
    
    # Create test table
    cursor1.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
    cursor1.execute("INSERT INTO test (value) VALUES (?)", ("initial",))
    test_db.commit()
    
    # Start transaction 1
    cursor1.execute("BEGIN")
    cursor1.execute("UPDATE test SET value = ? WHERE id = ?", ("updated1", 1))
    
    # Start transaction 2
    cursor2.execute("BEGIN")
    cursor2.execute("SELECT value FROM test WHERE id = ?", (1,))
    assert cursor2.fetchone()[0] == "initial"  # Should see old value
    
    # Commit transaction 1
    test_db.commit()
    
    # Verify transaction 2 still sees old value
    cursor2.execute("SELECT value FROM test WHERE id = ?", (1,))
    assert cursor2.fetchone()[0] == "initial"
    
    # Commit transaction 2
    test_db.commit()
    
    # Verify final state
    cursor1.execute("SELECT value FROM test WHERE id = ?", (1,))
    assert cursor1.fetchone()[0] == "updated1"

@pytest.mark.acid
def test_durability(test_db):
    """Test durability of committed transactions."""
    cursor = test_db.cursor()
    
    # Create test table
    cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
    
    # Insert and commit data
    cursor.execute("INSERT INTO test (value) VALUES (?)", ("test",))
    test_db.commit()
    
    # Close and reopen database
    test_db.close()
    test_db = sqlite3.connect("test.db")
    cursor = test_db.cursor()
    
    # Verify data persists
    cursor.execute("SELECT value FROM test WHERE id = ?", (1,))
    assert cursor.fetchone()[0] == "test" 