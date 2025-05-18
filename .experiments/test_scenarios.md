# Test Scenarios and Experiments

## 1. Load Testing Scenarios
```python
# Example load test scenario
async def test_concurrent_users():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(100):
            tasks.append(session.get('http://localhost:8000/api/v1/public'))
        responses = await asyncio.gather(*tasks)
        assert all(r.status == 200 for r in responses)
```

## 2. Database Stress Testing
```python
# Example database stress test
def test_concurrent_writes():
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i in range(100):
            futures.append(executor.submit(write_to_db, f"test_{i}"))
        results = [f.result() for f in futures]
        assert all(results)
```

## 3. Security Testing Scenarios
```python
# Example security test scenarios
def test_sql_injection_prevention():
    malicious_inputs = [
        "' OR '1'='1",
        "; DROP TABLE users;--",
        "' UNION SELECT * FROM users--"
    ]
    for input in malicious_inputs:
        response = client.get(f"/api/v1/search?q={input}")
        assert response.status_code == 400

def test_xss_prevention():
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "<img src='x' onerror='alert(1)'>",
        "javascript:alert('xss')"
    ]
    for input in malicious_inputs:
        response = client.post("/api/v1/comment", json={"content": input})
        assert response.status_code == 400
```

## 4. Chaos Testing Scenarios
```python
# Example chaos test scenarios
def test_service_resilience():
    # Kill random system processes
    processes = psutil.process_iter()
    for _ in range(5):
        process = random.choice(list(processes))
        try:
            process.kill()
        except:
            pass
        # Verify system still responds
        response = client.get("/health")
        assert response.status_code == 200
```

## 5. Performance Benchmarks
```python
# Example performance test
def test_response_time():
    start_time = time.time()
    response = client.get("/api/v1/public")
    end_time = time.time()
    
    assert response.status_code == 200
    assert end_time - start_time < 0.1  # Response under 100ms
```

## 6. Recovery Testing
```python
# Example recovery test
def test_database_recovery():
    # Corrupt database
    with open("app.db", "wb") as f:
        f.write(b"corrupted")
    
    # Restart application
    restart_app()
    
    # Verify automatic recovery
    response = client.get("/health")
    assert response.status_code == 200
```

## Notes
- All scenarios should be run in isolated environments
- Record metrics for each test run
- Document any failures or unexpected behaviors
- Track performance degradation over time 