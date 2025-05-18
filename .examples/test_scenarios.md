# Test Scenarios Examples

## Smoke Test Examples

### 1. API Health Check
```python
def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
```

### 2. Database Connection
```python
def test_database_connection():
    try:
        db = next(get_db())
        assert db is not None
    finally:
        db.close()
```

## ACID Test Examples

### 1. Transaction Atomicity
```python
def test_transaction_atomicity():
    db.begin()
    try:
        # Perform multiple operations
        db.execute("INSERT INTO users (name) VALUES ('test')")
        db.execute("UPDATE counters SET value = value + 1")
        db.commit()
    except Exception:
        db.rollback()
        raise
```

### 2. Data Consistency
```python
def test_data_consistency():
    # Verify foreign key constraints
    with pytest.raises(IntegrityError):
        db.execute("INSERT INTO orders (user_id) VALUES (999)")
```

## Chaos Test Examples

### 1. Network Latency
```python
def test_network_latency():
    start_time = time.time()
    response = client.get("/api/data")
    end_time = time.time()
    assert end_time - start_time < 5.0
```

### 2. Resource Exhaustion
```python
def test_resource_exhaustion():
    threads = []
    for _ in range(100):
        thread = threading.Thread(target=lambda: client.get("/api/data"))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
```

## Security Test Examples

### 1. SQL Injection Prevention
```python
def test_sql_injection():
    malicious_input = "'; DROP TABLE users; --"
    response = client.post(
        "/api/search",
        json={"query": malicious_input}
    )
    assert response.status_code == 400
```

### 2. XSS Prevention
```python
def test_xss_prevention():
    xss_input = "<script>alert('xss')</script>"
    response = client.post(
        "/api/comment",
        json={"content": xss_input}
    )
    assert response.status_code == 400
```

## Performance Test Examples

### 1. Response Time
```python
def test_response_time():
    start_time = time.time()
    response = client.get("/api/data")
    end_time = time.time()
    assert end_time - start_time < 1.0
```

### 2. Concurrent Access
```python
def test_concurrent_access():
    results = []
    threads = []
    
    def make_request():
        response = client.get("/api/data")
        results.append(response.status_code)
    
    for _ in range(50):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    assert all(code == 200 for code in results)
```

## Error Handling Examples

### 1. Error Logging
```python
def test_error_logging():
    try:
        response = client.get("/api/error")
    except Exception as e:
        assert os.path.exists(".errors/error.log")
        with open(".errors/error.log", "r") as f:
            assert str(e) in f.read()
```

### 2. Error Recovery
```python
def test_error_recovery():
    # Simulate error
    response = client.get("/api/error")
    assert response.status_code == 500
    
    # Verify system recovery
    response = client.get("/health")
    assert response.status_code == 200
``` 