# Initialization Commands

This guide provides detailed information about the initialization commands available in the system.

## Overview

The initialization commands are designed to set up and configure various system components:

- Database Initialization: Set up database schema and initial data
- Cache Initialization: Configure and warm up cache
- Service Registry Setup: Register and configure services

## Database Initialization

### Usage

```bash
init database [--schema <schema_file>] [--data <data_file>] [--force]
```

### Parameters

- `--schema`: Optional path to SQL schema file
- `--data`: Optional path to SQL data file
- `--force`: Force reinitialization if database exists

### Output Format

```json
{
    "status": "success|error",
    "timestamp": "ISO-8601 timestamp",
    "schema": {
        "status": "success|error",
        "file": "path/to/schema.sql|default",
        "error": "error message if failed"
    },
    "data": {
        "status": "success|error",
        "file": "path/to/data.sql|default",
        "records": 100,
        "error": "error message if failed"
    },
    "migrations": {
        "status": "success|error",
        "migrations": [
            {
                "migration": "migration_name",
                "status": "success|error",
                "details": { ... },
                "error": "error message if failed"
            }
        ]
    }
}
```

### Error Codes

- `DATABASE_NOT_AVAILABLE`: Database service is not available
- `DATABASE_EXISTS`: Database already exists (when not using --force)
- `SCHEMA_ERROR`: Failed to execute schema
- `DATA_ERROR`: Failed to load data
- `MIGRATION_ERROR`: Failed to run migrations
- `FILE_NOT_FOUND`: Schema or data file not found
- `FILE_READ_ERROR`: Failed to read schema or data file

### Schema Format

The schema file should contain valid SQL statements for creating database objects:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id),
    role_id INTEGER REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);
```

### Data Format

The data file should contain valid SQL statements for inserting initial data:

```sql
INSERT INTO roles (name, description) VALUES
    ('admin', 'System administrator'),
    ('user', 'Regular user');

INSERT INTO users (username, email) VALUES
    ('admin', 'admin@example.com'),
    ('test', 'test@example.com');

INSERT INTO user_roles (user_id, role_id) VALUES
    (1, 1),  -- admin user -> admin role
    (2, 2);  -- test user -> user role
```

### Migration Format

Migrations should be numbered SQL files in the migrations directory:

```
migrations/
  ├── 001_initial_schema.sql
  ├── 002_add_user_roles.sql
  └── 003_add_timestamps.sql
```

Each migration file should contain:
- Up migration (changes to apply)
- Down migration (changes to roll back)
- Version information

Example migration file:

```sql
-- Migration: 001_initial_schema
-- Version: 1.0
-- Description: Initial database schema

-- Up
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

-- Down
DROP TABLE users;
```

### Rollback

To roll back database initialization:

```bash
init database rollback
```

This will:
1. Roll back all applied migrations
2. Drop all database objects
3. Remove the database

Output format:

```json
{
    "status": "success|error",
    "migrations": {
        "status": "success|error",
        "rolled_back": ["migration_name"],
        "error": "error message if failed"
    }
}
```

## Cache Initialization

### Usage

```bash
init cache [--config <config_file>] [--warm-up] [--clear]
```

### Parameters

- `--config`: Optional path to cache configuration file
- `--warm-up`: Warm up cache with predefined queries
- `--clear`: Clear existing cache data

### Output Format

```json
{
    "status": "success|error",
    "timestamp": "ISO-8601 timestamp",
    "setup": {
        "status": "success|error",
        "config": {
            "max_size": "1GB",
            "eviction_policy": "LRU",
            "ttl": 3600
        },
        "error": "error message if failed"
    },
    "clear": {
        "status": "success|error",
        "before": {
            "size": "100MB",
            "items": 1000,
            "hits": 5000,
            "misses": 1000
        },
        "after": {
            "size": "0MB",
            "items": 0,
            "hits": 0,
            "misses": 0
        },
        "error": "error message if failed"
    },
    "warm_up": {
        "status": "success|error",
        "queries": [
            {
                "query": "query_name",
                "status": "success|error",
                "details": { ... },
                "error": "error message if failed"
            }
        ],
        "stats": {
            "size": "50MB",
            "items": 500,
            "hits": 0,
            "misses": 500
        },
        "error": "error message if failed"
    }
}
```

### Error Codes

- `CACHE_NOT_AVAILABLE`: Cache service is not available
- `CONFIG_ERROR`: Failed to apply configuration
- `CLEAR_ERROR`: Failed to clear cache
- `WARM_UP_ERROR`: Failed to warm up cache
- `FILE_NOT_FOUND`: Configuration file not found
- `FILE_READ_ERROR`: Failed to read configuration file

### Configuration Format

The configuration file should be in JSON format:

```json
{
    "max_size": "1GB",
    "eviction_policy": "LRU",
    "ttl": 3600,
    "compression": {
        "enabled": true,
        "algorithm": "lz4"
    },
    "persistence": {
        "enabled": true,
        "path": "/var/cache/data",
        "sync_interval": 300
    },
    "warm_up": {
        "queries": [
            "popular_items",
            "user_preferences",
            "system_settings"
        ],
        "parallel": true,
        "timeout": 60
    }
}
```

### Reset Cache

To reset the cache service:

```bash
init cache reset
```

This will:
1. Clear all cached data
2. Reset configuration to defaults
3. Stop the cache service

Output format:

```json
{
    "status": "success|error",
    "clear": {
        "status": "success|error",
        "before": { ... },
        "after": { ... }
    },
    "error": "error message if failed"
}
```

## Best Practices

1. Cache Configuration
   - Set appropriate size limits
   - Choose suitable eviction policy
   - Configure TTL values
   - Enable compression if needed

2. Cache Warm-up
   - Identify frequently accessed data
   - Prepare warm-up queries
   - Monitor warm-up performance
   - Schedule periodic warm-up

3. Cache Maintenance
   - Monitor cache usage
   - Clear cache when needed
   - Update configuration
   - Verify cache health

4. Error Handling
   - Handle service failures
   - Implement fallbacks
   - Monitor error rates
   - Log cache operations

## Troubleshooting

### Common Issues

1. Configuration Problems
   - Check file format
   - Verify settings
   - Check permissions
   - Monitor resource usage

2. Warm-up Issues
   - Check query syntax
   - Monitor execution time
   - Verify data availability
   - Check error logs

3. Performance Issues
   - Monitor hit rates
   - Check eviction rates
   - Analyze memory usage
   - Optimize queries

### Recovery Steps

1. Failed Configuration
   - Check error messages
   - Verify configuration
   - Apply defaults
   - Retry configuration

2. Failed Warm-up
   - Check failed queries
   - Fix query issues
   - Adjust timeout
   - Retry warm-up

3. Service Issues
   - Reset service
   - Clear data
   - Reconfigure service
   - Restart service

## Service Registry Setup

### Usage

```bash
init service-registry [--config <config_file>]
```

### Parameters

- `--config`: Optional path to service registry configuration file

### Output Format

```json
{
    "status": "success|error",
    "timestamp": "ISO-8601 timestamp",
    "setup": {
        "status": "success|error",
        "config": {
            "max_services": 100,
            "discovery_interval": 300
        },
        "error": "error message if failed"
    }
}
```

### Error Codes

- `SERVICE_REGISTRY_NOT_AVAILABLE`: Service registry service is not available
- `CONFIG_ERROR`: Failed to apply configuration
- `FILE_NOT_FOUND`: Configuration file not found
- `FILE_READ_ERROR`: Failed to read configuration file

### Configuration Format

The configuration file should be in JSON format:

```json
{
    "max_services": 100,
    "discovery_interval": 300
}
```

### Best Practices

1. Service Registry Configuration
   - Set appropriate max services
   - Configure discovery interval
   - Monitor service health
   - Implement service discovery

2. Error Handling
   - Handle service failures
   - Implement fallbacks
   - Monitor error rates
   - Log registry operations

## Troubleshooting

### Common Issues

1. Configuration Problems
   - Check file format
   - Verify settings
   - Check permissions
   - Monitor resource usage

2. Service Issues
   - Reset service
   - Clear data
   - Reconfigure service
   - Restart service 