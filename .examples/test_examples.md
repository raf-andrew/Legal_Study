# Test Examples

## Smoke Test Example

```python
def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    try:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
    except Exception as e:
        logger.error(f"Health check test failed: {e}")
        raise
```

## ACID Test Example

```python
def test_atomicity_rollback(db):
    """Test that failed transactions are rolled back."""
    # Create initial user
    user = db.create_user("unique_user", "unique@example.com")
    assert user is not None

    # Attempt to create user with same username
    with pytest.raises(IntegrityError):
        db.create_user("unique_user", "another@example.com")

    # Verify original user still exists unchanged
    retrieved_user = db.get_user(user.id)
    assert retrieved_user is not None
    assert retrieved_user.username == "unique_user"
```

## Chaos Test Example

```python
def test_system_stress(db):
    """Test database operations under system stress."""
    # Create initial user
    user = db.create_user("stress_test_user", "stress@example.com")
    assert user is not None

    # Start stress thread
    stress_thread = threading.Thread(target=simulate_high_load, args=(2.0,))
    stress_thread.start()

    # Perform database operations under stress
    results = []
    for i in range(5):
        try:
            post = db.create_post(f"Post {i}", f"Content {i}", user.id)
            results.append({"success": True, "post": post})
        except Exception as e:
            results.append({"success": False, "error": str(e)})
        time.sleep(0.1)

    stress_thread.join()
```

## Security Test Example

```python
def test_token_validation(client: TestClient, jwt_secret: str):
    """Test JWT token validation."""
    # Create valid token
    valid_token = create_token(jwt_secret, user_id=1)
    
    # Create expired token
    expired_token = create_token(jwt_secret, user_id=1, expiry_minutes=-30)
    
    # Test valid token
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = client.get("/metrics", headers=headers)
    assert response.status_code == 200
    
    # Test expired token
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/metrics", headers=headers)
    assert response.status_code == 401
```

## Test Runner Example

```python
def run_test_suite(self, test_file: str) -> Dict[str, Any]:
    """Run a specific test suite and return results"""
    logging.info(f"Running test suite: {test_file}")
    try:
        result = pytest.main([
            f".tests/{test_file}",
            "--verbose",
            "--tb=short",
            "--junitxml=.logs/junit.xml",
            "--html=.logs/report.html"
        ])
        return {
            "status": "passed" if result == 0 else "failed",
            "timestamp": datetime.datetime.now().isoformat(),
            "test_file": test_file
        }
    except Exception as e:
        logging.error(f"Error running test suite {test_file}: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat(),
            "test_file": test_file
        }
```

## Error Recording Example

```python
def record_error(self, test_file: str, error: str):
    """Record an error to the errors directory"""
    error_file = self.errors_dir / f"{test_file}.error"
    with open(error_file, 'w') as f:
        f.write(f"Test: {test_file}\n")
        f.write(f"Time: {datetime.datetime.now().isoformat()}\n")
        f.write(f"Error: {error}\n")
```

## Test Completion Example

```python
def mark_complete(self, test_file: str):
    """Mark a test as completed"""
    complete_file = self.complete_dir / f"{test_file}.complete"
    with open(complete_file, 'w') as f:
        f.write(f"Test: {test_file}\n")
        f.write(f"Completed: {datetime.datetime.now().isoformat()}\n")
``` 