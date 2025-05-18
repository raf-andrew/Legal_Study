# Database Cleanup Prompt

## Context
When working with database tests, proper cleanup is essential to prevent resource leaks and ensure test isolation.

## Key Components

### Connection Management
```python
@contextmanager
def get_connection():
    """Context manager for database connections"""
    if not self.engine:
        self.engine = create_engine(
            self.db_url,
            poolclass=pool.QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
        
    conn = self.engine.connect()
    try:
        yield conn
    finally:
        conn.close()
```

### Retry Mechanism
```python
def retry_operation(operation, max_retries=3, delay=1):
    """Retry an operation with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = delay * (2 ** attempt)
            logging.warning(f"Operation failed, retrying in {wait_time}s: {str(e)}")
            time.sleep(wait_time)
```

### Cleanup Pattern
```python
def cleanup():
    """Clean up database resources"""
    try:
        # Close all connections in the pool
        if self.engine:
            self.engine.dispose()
            
        def remove_db():
            if os.path.exists("database.db"):
                os.remove("database.db")
                
        # Retry the cleanup operation
        retry_operation(remove_db)
        return True
        
    except Exception as e:
        logging.error(f"Cleanup failed: {e}")
        return False
```

## Usage Example
```python
def run_test():
    success = False
    try:
        # Test setup and execution
        success = True
    except Exception as e:
        logging.error(f"Test failed: {e}")
        success = False
    finally:
        if not cleanup():
            success = False
    return success
```

## Best Practices
1. Always use connection pooling
2. Implement retry mechanisms for cleanup
3. Close connections in finally blocks
4. Dispose of engine when done
5. Log cleanup failures
6. Return success status

## Common Issues
1. File locks preventing deletion
2. Unclosed connections
3. Pool exhaustion
4. Cleanup timing issues

## Solutions
1. Use connection pooling
2. Implement retry mechanism
3. Proper connection cleanup
4. Engine disposal
5. Error logging 