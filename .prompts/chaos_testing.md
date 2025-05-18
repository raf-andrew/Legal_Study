# Chaos Testing Prompt

## Context
Chaos testing helps verify system resilience by simulating various failure scenarios and resource constraints.

## Key Components

### Resource Pressure Simulation
```python
def simulate_high_cpu(duration):
    """Simulate high CPU usage"""
    end_time = time.time() + duration
    while time.time() < end_time:
        _ = [i * i for i in range(1000)]

def simulate_memory_pressure(size_mb):
    """Simulate memory pressure"""
    data = [bytearray(1024 * 1024) for _ in range(size_mb)]
    time.sleep(2)  # Hold memory

def simulate_disk_pressure(size_mb):
    """Simulate disk pressure"""
    with open('temp.dat', 'wb') as f:
        f.write(os.urandom(size_mb * 1024 * 1024))
    time.sleep(2)  # Hold file
    os.remove('temp.dat')
```

### Network Simulation
```python
def simulate_network_latency():
    """Simulate network latency"""
    time.sleep(random.uniform(0.1, 0.5))

def simulate_network_failure():
    """Simulate network failure"""
    raise requests.exceptions.ConnectionError("Simulated network failure")
```

### Concurrent Load Testing
```python
def test_concurrent_load(endpoint, num_requests=50):
    """Test system under concurrent load"""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(requests.get, endpoint)
            for _ in range(num_requests)
        ]
        results = [f.result() for f in futures]
    return all(r.status_code == 200 for r in results)
```

### Resource Monitoring
```python
def monitor_resources():
    """Monitor system resources"""
    process = psutil.Process()
    return {
        'memory_percent': process.memory_percent(),
        'cpu_percent': process.cpu_percent(interval=1),
        'disk_percent': psutil.disk_usage('/').percent
    }
```

## Test Patterns

### Resource Exhaustion
1. Gradually increase resource usage
2. Monitor system behavior
3. Verify graceful degradation
4. Check recovery after release

### Network Issues
1. Introduce latency
2. Simulate packet loss
3. Test connection timeouts
4. Verify retry mechanisms

### Concurrent Access
1. Test with multiple users
2. Check resource contention
3. Verify data consistency
4. Monitor performance

### System Limits
1. Test memory limits
2. Test CPU limits
3. Test disk space limits
4. Test connection limits

## Best Practices
1. Start with small disruptions
2. Monitor system metrics
3. Have clear success criteria
4. Clean up after tests
5. Log all activities
6. Use timeouts
7. Handle cleanup in finally blocks
8. Monitor resource usage
9. Test recovery paths
10. Document findings

## Common Issues
1. Resource leaks
2. Deadlocks
3. Race conditions
4. Memory exhaustion
5. File handle leaks

## Solutions
1. Implement proper cleanup
2. Use resource limits
3. Add monitoring
4. Implement circuit breakers
5. Add retry mechanisms

## Test Structure
```python
def chaos_test():
    try:
        # Setup monitoring
        start_monitoring()
        
        # Apply chaos
        introduce_chaos()
        
        # Verify system
        verify_system_health()
        
        # Test functionality
        test_core_features()
        
    finally:
        # Cleanup
        cleanup_resources()
        stop_monitoring()
```

## Monitoring Strategy
1. Resource usage
2. Response times
3. Error rates
4. Recovery times
5. System health

## Recovery Verification
1. Check data consistency
2. Verify service availability
3. Test core functionality
4. Monitor error rates
5. Verify metrics 