# Database Testing Examples

This document demonstrates our approach to database testing with practical examples.

## Basic Setup

### Connection Management
```python
from sqlalchemy import create_engine, pool
from contextlib import contextmanager

class DatabaseTest:
    def __init__(self):
        self.db_url = "sqlite:///./test.db"
        self.engine = create_engine(
            self.db_url,
            poolclass=pool.QueuePool,
            pool_size=5,
            max_overflow=10
        )
        
    @contextmanager
    def get_connection(self):
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()
```

### Test Data Management
```python
import uuid

class TestData:
    def __init__(self):
        self.test_run_id = str(uuid.uuid4())[:8]
        
    def get_unique_user(self):
        return {
            "username": f"test_user_{self.test_run_id}",
            "email": f"test_{self.test_run_id}@example.com",
            "password_hash": "test_hash"
        }
```

## ACID Test Examples

### Atomicity Test
```python
def test_atomicity(self):
    with self.get_connection() as conn:
        with conn.begin():
            try:
                # First operation
                conn.execute(text(
                    "INSERT INTO users (username, email) VALUES (:username, :email)"
                ), {"username": "user1", "email": "user1@test.com"})
                
                # Second operation (should fail)
                conn.execute(text(
                    "INSERT INTO users (username, email) VALUES (:username, :email)"
                ), {"username": "user1", "email": "user1@test.com"})
                
                assert False, "Should have raised unique constraint violation"
            except:
                pass
            
        # Verify nothing was committed
        result = conn.execute(text(
            "SELECT COUNT(*) FROM users WHERE username = :username"
        ), {"username": "user1"}).scalar()
        assert result == 0
```

### Consistency Test
```python
def test_consistency(self):
    with self.get_connection() as conn:
        with conn.begin():
            try:
                # Should fail due to NOT NULL constraint
                conn.execute(text(
                    "INSERT INTO users (username) VALUES (:username)"
                ), {"username": "test_user"})
                assert False, "Should have raised NOT NULL constraint violation"
            except:
                pass
```

### Isolation Test
```python
def test_isolation(self):
    # Transaction 1: Insert data
    with self.get_connection() as conn1:
        with conn1.begin():
            conn1.execute(text(
                "INSERT INTO users (username, email) VALUES (:username, :email)"
            ), {"username": "isolation_test", "email": "test@test.com"})
            
            # Transaction 2: Should not see uncommitted data
            with self.get_connection() as conn2:
                result = conn2.execute(text(
                    "SELECT COUNT(*) FROM users WHERE username = :username"
                ), {"username": "isolation_test"}).scalar()
                assert result == 0
```

### Durability Test
```python
def test_durability(self):
    # Insert data and commit
    with self.get_connection() as conn:
        with conn.begin():
            conn.execute(text(
                "INSERT INTO users (username, email) VALUES (:username, :email)"
            ), {"username": "durability_test", "email": "test@test.com"})
            
    # Verify data persists in new connection
    with self.get_connection() as conn:
        result = conn.execute(text(
            "SELECT COUNT(*) FROM users WHERE username = :username"
        ), {"username": "durability_test"}).scalar()
        assert result == 1
```

## Error Handling Examples

### Retry Mechanism
```python
def retry_operation(operation, max_retries=3, delay=1):
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(delay * (2 ** attempt))
```

### Cleanup Pattern
```python
def cleanup(self):
    try:
        # Dispose of connection pool
        if self.engine:
            self.engine.dispose()
            
        def remove_db():
            if os.path.exists("test.db"):
                os.remove("test.db")
                
        retry_operation(remove_db)
        return True
    except Exception as e:
        logging.error(f"Cleanup failed: {e}")
        return False
```

## Best Practices

1. Always use connection pooling
2. Use context managers for connections
3. Implement proper cleanup
4. Use unique test data
5. Handle constraints properly
6. Implement retry mechanisms
7. Log all operations
8. Use parameterized queries
9. Clean up before and after tests
10. Verify ACID properties

## Common Patterns

### Setup and Teardown
```python
def setup_method(self):
    self.engine = create_engine(self.db_url)
    self.create_tables()
    self.insert_test_data()
    
def teardown_method(self):
    self.cleanup()
```

### Transaction Wrapper
```python
@contextmanager
def transaction(self):
    with self.get_connection() as conn:
        with conn.begin():
            yield conn
```

### Test Data Factory
```python
def create_test_user(self):
    return {
        "username": f"user_{uuid.uuid4()}",
        "email": f"user_{uuid.uuid4()}@test.com",
        "password_hash": "test_hash"
    }
``` 