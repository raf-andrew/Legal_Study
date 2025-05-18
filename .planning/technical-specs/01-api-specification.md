# API Specification

## Authentication

### 1. Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "user@example.com",
    "role": "admin"
  }
}
```

### 2. Logout
```http
POST /api/auth/logout
Authorization: Bearer {token}
```

## Initialization

### 1. Start Initialization
```http
POST /api/initialize
Authorization: Bearer {token}
Content-Type: application/json

{
  "components": ["database", "cache", "queue"],
  "options": {
    "force": false,
    "validate": true
  }
}
```

Response:
```json
{
  "id": "init_123",
  "status": "INITIALIZING",
  "started_at": "2024-01-01T00:00:00Z",
  "components": {
    "database": "PENDING",
    "cache": "PENDING",
    "queue": "PENDING"
  }
}
```

### 2. Get Initialization Status
```http
GET /api/initialize/{id}
Authorization: Bearer {token}
```

Response:
```json
{
  "id": "init_123",
  "status": "COMPLETED",
  "started_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:01:00Z",
  "components": {
    "database": "COMPLETED",
    "cache": "COMPLETED",
    "queue": "COMPLETED"
  },
  "metrics": {
    "total_time": 60,
    "database_time": 20,
    "cache_time": 15,
    "queue_time": 25
  }
}
```

## Service Management

### 1. List Services
```http
GET /api/services
Authorization: Bearer {token}
```

Response:
```json
{
  "services": [
    {
      "id": "db_service",
      "name": "Database Service",
      "status": "RUNNING",
      "health": "HEALTHY",
      "last_check": "2024-01-01T00:00:00Z"
    },
    {
      "id": "cache_service",
      "name": "Cache Service",
      "status": "RUNNING",
      "health": "HEALTHY",
      "last_check": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 2. Service Control
```http
POST /api/services/{id}/control
Authorization: Bearer {token}
Content-Type: application/json

{
  "action": "restart",
  "options": {
    "force": false
  }
}
```

Response:
```json
{
  "id": "db_service",
  "action": "restart",
  "status": "PENDING",
  "started_at": "2024-01-01T00:00:00Z"
}
```

## Configuration

### 1. Get Configuration
```http
GET /api/config
Authorization: Bearer {token}
```

Response:
```json
{
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "app_db"
  },
  "cache": {
    "driver": "redis",
    "host": "localhost",
    "port": 6379
  },
  "queue": {
    "driver": "rabbitmq",
    "host": "localhost",
    "port": 5672
  }
}
```

### 2. Update Configuration
```http
PUT /api/config
Authorization: Bearer {token}
Content-Type: application/json

{
  "database": {
    "host": "newhost",
    "port": 5432
  }
}
```

Response:
```json
{
  "status": "UPDATED",
  "updated_at": "2024-01-01T00:00:00Z",
  "changes": {
    "database.host": {
      "old": "localhost",
      "new": "newhost"
    }
  }
}
```

## Monitoring

### 1. Get Metrics
```http
GET /api/metrics
Authorization: Bearer {token}
```

Response:
```json
{
  "cpu": {
    "usage": 45.2,
    "cores": 4
  },
  "memory": {
    "used": 2048,
    "total": 4096
  },
  "services": {
    "database": {
      "connections": 10,
      "queries_per_second": 100
    },
    "cache": {
      "hits": 1000,
      "misses": 50
    }
  }
}
```

### 2. Get Logs
```http
GET /api/logs
Authorization: Bearer {token}
Query Parameters:
  - service: string
  - level: string
  - start: datetime
  - end: datetime
```

Response:
```json
{
  "logs": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "level": "INFO",
      "service": "database",
      "message": "Connection established",
      "context": {
        "connection_id": "conn_123"
      }
    }
  ],
  "pagination": {
    "total": 100,
    "per_page": 10,
    "current_page": 1
  }
}
```

## WebSocket Events

### 1. Initialization Events
```json
{
  "event": "initialization.status",
  "data": {
    "id": "init_123",
    "status": "INITIALIZING",
    "component": "database",
    "progress": 50
  }
}
```

### 2. Service Events
```json
{
  "event": "service.status",
  "data": {
    "id": "db_service",
    "status": "RUNNING",
    "health": "HEALTHY",
    "metrics": {
      "connections": 10
    }
  }
}
```

### 3. Alert Events
```json
{
  "event": "alert.triggered",
  "data": {
    "id": "alert_123",
    "level": "WARNING",
    "message": "High CPU usage detected",
    "service": "database",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## Error Responses

### 1. Validation Error
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "database.host": ["The host field is required"]
    }
  }
}
```

### 2. Authentication Error
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid credentials"
  }
}
```

### 3. Service Error
```json
{
  "error": {
    "code": "SERVICE_ERROR",
    "message": "Database service unavailable",
    "service": "database",
    "status": "DOWN"
  }
}
```

## Rate Limiting

- 100 requests per minute per user
- 1000 requests per minute per IP
- Headers:
  - X-RateLimit-Limit
  - X-RateLimit-Remaining
  - X-RateLimit-Reset

## Pagination

All list endpoints support pagination:
- page: integer
- per_page: integer (max: 100)
- sort: string
- direction: asc|desc

Response includes:
```json
{
  "data": [...],
  "meta": {
    "total": 100,
    "per_page": 10,
    "current_page": 1,
    "last_page": 10
  }
}
``` 