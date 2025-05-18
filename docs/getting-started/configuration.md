# Configuration Guide

This guide explains how to configure the Legal Study Platform.

## Overview

The platform can be configured through:

- Environment variables
- Configuration files
- Command-line arguments
- API settings

## Environment Variables

### Core Settings

```env
# Application
APP_NAME=Legal Study Platform
APP_ENV=development
APP_DEBUG=true
APP_URL=http://localhost:8000
APP_TIMEZONE=UTC

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4
TIMEOUT=120

# Security
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
JWT_EXPIRATION=3600
PASSWORD_SALT=your-salt

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/legal_study
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
DATABASE_ECHO=false

# Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
```

### Feature Settings

```env
# Storage
STORAGE_DRIVER=local
STORAGE_PATH=/path/to/storage
STORAGE_URL=http://localhost:8000/storage
STORAGE_MAX_SIZE=10485760

# Search
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX=legal_study
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=password

# Email
MAIL_DRIVER=smtp
MAIL_HOST=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=user@example.com
MAIL_PASSWORD=password
MAIL_ENCRYPTION=tls
MAIL_FROM_ADDRESS=noreply@example.com
MAIL_FROM_NAME="Legal Study Platform"

# Notifications
NOTIFICATION_DRIVER=database
NOTIFICATION_QUEUE=default
NOTIFICATION_RETRY=3
```

### Integration Settings

```env
# Authentication
AUTH_DRIVER=database
AUTH_PROVIDERS=google,github
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret

# Analytics
ANALYTICS_DRIVER=mixpanel
MIXPANEL_TOKEN=your-token
MIXPANEL_ENABLED=true

# Monitoring
MONITORING_DRIVER=prometheus
PROMETHEUS_PORT=9090
PROMETHEUS_PATH=/metrics
```

## Configuration Files

### 1. Application Config

`config/app.py`:
```python
from typing import Dict, Any

config: Dict[str, Any] = {
    'name': 'Legal Study Platform',
    'env': 'development',
    'debug': True,
    'url': 'http://localhost:8000',
    'timezone': 'UTC',

    'providers': [
        'app.providers.DatabaseProvider',
        'app.providers.CacheProvider',
        'app.providers.QueueProvider',
        'app.providers.EventProvider',
    ],

    'middleware': [
        'app.middleware.CorsMiddleware',
        'app.middleware.AuthMiddleware',
        'app.middleware.RateLimitMiddleware',
    ],

    'commands': [
        'app.commands.SetupCommand',
        'app.commands.MigrateCommand',
        'app.commands.SeedCommand',
    ],
}
```

### 2. Database Config

`config/database.py`:
```python
from typing import Dict, Any

config: Dict[str, Any] = {
    'default': 'postgresql',

    'connections': {
        'postgresql': {
            'driver': 'postgresql',
            'url': 'postgresql://user:password@localhost:5432/legal_study',
            'pool_size': 20,
            'max_overflow': 10,
            'echo': False,
        },
    },

    'migrations': 'database/migrations',
    'seeds': 'database/seeds',
}
```

### 3. Cache Config

`config/cache.py`:
```python
from typing import Dict, Any

config: Dict[str, Any] = {
    'default': 'redis',

    'stores': {
        'redis': {
            'driver': 'redis',
            'url': 'redis://localhost:6379/0',
            'ttl': 3600,
        },
        'file': {
            'driver': 'file',
            'path': 'storage/cache',
            'ttl': 3600,
        },
    },
}
```

### 4. Queue Config

`config/queue.py`:
```python
from typing import Dict, Any

config: Dict[str, Any] = {
    'default': 'redis',

    'connections': {
        'redis': {
            'driver': 'redis',
            'url': 'redis://localhost:6379/1',
            'queue': 'default',
            'retry_after': 90,
        },
    },
}
```

## Command-Line Arguments

### 1. Server

```bash
# Start server
./scripts/start.sh --host 0.0.0.0 --port 8000 --workers 4

# Start with config
./scripts/start.sh --config production.yaml

# Start with environment
./scripts/start.sh --env production
```

### 2. Database

```bash
# Run migrations
./scripts/migrate.sh --database postgresql

# Run seeds
./scripts/seed.sh --database postgresql

# Reset database
./scripts/reset.sh --database postgresql
```

### 3. Maintenance

```bash
# Clear cache
./scripts/cache.sh clear --store redis

# Clear queue
./scripts/queue.sh clear --connection redis

# Optimize database
./scripts/optimize.sh --database postgresql
```

## API Settings

### 1. Rate Limiting

```python
# config/api.py
RATE_LIMIT = {
    'enabled': True,
    'driver': 'redis',
    'max_attempts': 60,
    'decay_minutes': 1,
    'by': 'ip',
}
```

### 2. CORS

```python
# config/api.py
CORS = {
    'enabled': True,
    'allowed_origins': ['http://localhost:3000'],
    'allowed_methods': ['GET', 'POST', 'PUT', 'DELETE'],
    'allowed_headers': ['Content-Type', 'Authorization'],
    'exposed_headers': ['X-RateLimit-Limit', 'X-RateLimit-Remaining'],
    'max_age': 3600,
    'supports_credentials': True,
}
```

### 3. Authentication

```python
# config/api.py
AUTH = {
    'driver': 'jwt',
    'ttl': 3600,
    'refresh_ttl': 20160,
    'algo': 'HS256',
    'required': True,
    'lockout': {
        'enabled': True,
        'max_attempts': 5,
        'decay_minutes': 30,
    },
}
```

## Best Practices

1. **Security**:
   - Use strong secrets
   - Enable HTTPS
   - Set secure headers
   - Use rate limiting

2. **Performance**:
   - Configure caching
   - Optimize database
   - Set worker count
   - Enable compression

3. **Monitoring**:
   - Enable logging
   - Set up metrics
   - Configure alerts
   - Track errors

4. **Maintenance**:
   - Regular backups
   - Clean up logs
   - Monitor disk space
   - Update dependencies

## Troubleshooting

1. **Configuration Issues**:
   ```bash
   # Check config
   ./scripts/check-config.sh

   # Validate config
   ./scripts/validate-config.sh

   # Test config
   ./scripts/test-config.sh
   ```

2. **Environment Issues**:
   ```bash
   # Check environment
   ./scripts/check-env.sh

   # List variables
   ./scripts/list-env.sh

   # Export variables
   ./scripts/export-env.sh
   ```

3. **Permission Issues**:
   ```bash
   # Check permissions
   ./scripts/check-permissions.sh

   # Fix permissions
   ./scripts/fix-permissions.sh
   ```

## Additional Resources

- [Environment Variables](https://12factor.net/config)
- [Configuration Best Practices](https://12factor.net/config)
- [Security Best Practices](https://owasp.org/www-project-top-ten/)
- [Performance Best Practices](https://web.dev/fast/)
