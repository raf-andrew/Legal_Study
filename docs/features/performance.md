# Performance Guide

This guide explains the performance optimization system in the Legal Study Platform.

## Overview

The platform implements a comprehensive performance optimization system with support for:

- Caching
- Database optimization
- Query optimization
- Load balancing
- Resource management
- Performance monitoring

## Caching

### 1. Redis Cache

```python
# app/cache/redis.py
import redis
from functools import wraps
import json
from app.config import config

class RedisCache:
    def __init__(self):
        self.redis = redis.Redis(
            host=config['redis']['host'],
            port=config['redis']['port'],
            db=config['redis']['db'],
            decode_responses=True
        )

    def get(self, key: str) -> dict:
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set(self, key: str, value: dict, ttl: int = 3600):
        self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )

    def delete(self, key: str):
        self.redis.delete(key)

    def clear(self):
        self.redis.flushdb()

def cache(ttl: int = 3600):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_result = redis_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Get fresh result
            result = f(*args, **kwargs)

            # Cache result
            redis_cache.set(cache_key, result, ttl)

            return result
        return decorated_function
    return decorator
```

### 2. Usage

```python
# app/routes/api.py
from app.cache.redis import cache

@api.route('/documents/<int:id>', methods=['GET'])
@cache(ttl=300)  # Cache for 5 minutes
def get_document(id):
    document = Document.query.get_or_404(id)
    return jsonify(document.to_dict())
```

## Database Optimization

### 1. Connection Pooling

```python
# app/database/pool.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from app.config import config

def create_db_engine():
    return create_engine(
        config['database']['url'],
        poolclass=QueuePool,
        pool_size=config['database']['pool_size'],
        max_overflow=config['database']['max_overflow'],
        pool_timeout=config['database']['pool_timeout'],
        pool_recycle=config['database']['pool_recycle']
    )
```

### 2. Query Optimization

```python
# app/database/query.py
from sqlalchemy import select, func
from app.models import Document, Tag

def get_documents_with_tags():
    return select([
        Document,
        func.array_agg(Tag.name).label('tags')
    ]).outerjoin(
        Document.tags
    ).group_by(
        Document.id
    )
```

## Load Balancing

### 1. Nginx Configuration

```nginx
# config/nginx/nginx.conf
upstream app_servers {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass http://app_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Load balancing settings
        proxy_next_upstream error timeout http_500 http_502 http_503 http_504;
        proxy_next_upstream_tries 3;
        proxy_next_upstream_timeout 10s;
    }
}
```

### 2. Load Balancer Service

```python
# app/load_balancer/service.py
import requests
from typing import List, Dict
from app.config import config

class LoadBalancer:
    def __init__(self):
        self.servers = config['load_balancer']['servers']
        self.current_server = 0

    def get_next_server(self) -> str:
        server = self.servers[self.current_server]
        self.current_server = (self.current_server + 1) % len(self.servers)
        return server

    def check_server_health(self, server: str) -> bool:
        try:
            response = requests.get(
                f"{server}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def get_healthy_servers(self) -> List[str]:
        return [
            server for server in self.servers
            if self.check_server_health(server)
        ]
```

## Resource Management

### 1. Memory Management

```python
# app/resource/memory.py
import gc
import psutil
import os
from app.config import config

class MemoryManager:
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.memory_limit = config['resource']['memory_limit']

    def check_memory_usage(self) -> bool:
        memory_info = self.process.memory_info()
        return memory_info.rss < self.memory_limit

    def cleanup_memory(self):
        # Force garbage collection
        gc.collect()

        # Clear caches if needed
        if not self.check_memory_usage():
            redis_cache.clear()
```

### 2. CPU Management

```python
# app/resource/cpu.py
import multiprocessing
from app.config import config

class CPUManager:
    def __init__(self):
        self.max_workers = config['resource']['max_workers']
        self.pool = multiprocessing.Pool(
            processes=self.max_workers
        )

    def process_task(self, task, *args, **kwargs):
        return self.pool.apply_async(
            task,
            args=args,
            kwds=kwargs
        )

    def close(self):
        self.pool.close()
        self.pool.join()
```

## Performance Monitoring

### 1. Performance Metrics

```python
# app/monitoring/performance.py
from prometheus_client import Histogram, Counter
from functools import wraps
import time

# Performance metrics
request_duration = Histogram(
    'request_duration_seconds',
    'Request duration in seconds',
    ['endpoint']
)

cache_hits = Counter(
    'cache_hits_total',
    'Total number of cache hits'
)

cache_misses = Counter(
    'cache_misses_total',
    'Total number of cache misses'
)

def track_performance(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time

            request_duration.labels(
                endpoint=f.__name__
            ).observe(duration)

            return result
        except Exception as e:
            raise e
    return decorated_function
```

### 2. Performance Profiling

```python
# app/monitoring/profiler.py
import cProfile
import pstats
import io
from functools import wraps

def profile(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()

        result = f(*args, **kwargs)

        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()

        # Log profiling results
        current_app.logger.info(f"Profile for {f.__name__}:\n{s.getvalue()}")

        return result
    return decorated_function
```

## Performance Testing

### 1. Load Testing

```python
# tests/performance/test_load.py
from locust import HttpUser, task, between

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def get_document(self):
        self.client.get("/api/documents/1")

    @task
    def create_document(self):
        self.client.post(
            "/api/documents",
            json={
                "title": "Test Document",
                "content": "Test content"
            }
        )
```

### 2. Stress Testing

```python
# tests/performance/test_stress.py
import asyncio
import aiohttp
import time

async def stress_test():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(1000):
            task = asyncio.create_task(
                session.get('http://localhost:8000/api/documents')
            )
            tasks.append(task)

        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()

        success_count = sum(1 for r in responses if r.status == 200)
        total_time = end_time - start_time

        print(f"Success rate: {success_count/len(responses)*100}%")
        print(f"Total time: {total_time} seconds")
```

## Performance Best Practices

1. **Caching**:
   - Cache frequently accessed data
   - Use appropriate cache TTL
   - Implement cache invalidation
   - Monitor cache hit rates

2. **Database**:
   - Use connection pooling
   - Optimize queries
   - Create proper indexes
   - Monitor query performance

3. **Load Balancing**:
   - Distribute load evenly
   - Monitor server health
   - Implement failover
   - Use sticky sessions when needed

4. **Resource Management**:
   - Monitor memory usage
   - Manage CPU resources
   - Implement cleanup routines
   - Set resource limits

## Performance Optimization

### 1. Query Optimization

```python
# app/optimization/query.py
from sqlalchemy import Index

# Create indexes
document_title_idx = Index('idx_document_title', Document.title)
document_created_at_idx = Index('idx_document_created_at', Document.created_at)

# Optimize queries
def get_recent_documents():
    return Document.query\
        .filter(Document.created_at >= datetime.utcnow() - timedelta(days=7))\
        .order_by(Document.created_at.desc())\
        .limit(100)
```

### 2. Response Optimization

```python
# app/optimization/response.py
from flask import jsonify
from functools import wraps

def optimize_response(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)

        # Compress response
        response.headers['Content-Encoding'] = 'gzip'

        # Set cache headers
        response.headers['Cache-Control'] = 'public, max-age=300'

        return response
    return decorated_function
```

## Troubleshooting

1. **Performance Issues**:
   - Check response times
   - Monitor resource usage
   - Analyze slow queries
   - Review cache hit rates

2. **Load Issues**:
   - Check server health
   - Monitor load distribution
   - Review error rates
   - Check resource limits

3. **Cache Issues**:
   - Check cache configuration
   - Monitor cache size
   - Review cache hit rates
   - Check cache invalidation

## Additional Resources

- [Redis Documentation](https://redis.io/documentation)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Performance Testing Guide](https://locust.io/)
