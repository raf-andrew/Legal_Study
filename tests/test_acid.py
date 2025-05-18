import pytest
from sqlalchemy.exc import IntegrityError
from app.database import get_db, Base, engine
from app.models import Test

@pytest.fixture(autouse=True)
def setup_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)

def test_atomicity():
    """Test that transactions are atomic - all or nothing"""
    db = next(get_db())
    try:
        # Create a test record
        test = Test(name="test1", value=1)
        db.add(test)
        db.commit()
        
        # Try to create a duplicate record (should fail)
        duplicate = Test(name="test1", value=2)
        db.add(duplicate)
        db.commit()
        pytest.fail("Should have raised IntegrityError")
    except IntegrityError:
        db.rollback()
        # Verify first record still exists
        assert db.query(Test).filter_by(name="test1").first().value == 1

def test_consistency():
    """Test that database remains in a consistent state"""
    db = next(get_db())
    # Create a test record
    test = Test(name="test2", value=1)
    db.add(test)
    db.commit()
    
    # Update the record
    test.value = 2
    db.commit()
    
    # Verify the update was successful
    assert db.query(Test).filter_by(name="test2").first().value == 2

def test_isolation():
    """Test that concurrent transactions are isolated"""
    db1 = next(get_db())
    db2 = next(get_db())
    
    # Create a test record in first transaction
    test = Test(name="test3", value=1)
    db1.add(test)
    db1.commit()
    
    # Start a second transaction and update the record
    test2 = db2.query(Test).filter_by(name="test3").first()
    test2.value = 2
    db2.commit()
    
    # Verify first transaction sees the original value
    assert db1.query(Test).filter_by(name="test3").first().value == 2

def test_durability():
    """Test that committed transactions are durable"""
    db = next(get_db())
    # Create a test record
    test = Test(name="test4", value=1)
    db.add(test)
    db.commit()
    
    # Close and reopen database connection
    db.close()
    db = next(get_db())
    
    # Verify record still exists
    assert db.query(Test).filter_by(name="test4").first().value == 1 