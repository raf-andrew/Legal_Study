# Health Check Commands

This guide provides detailed information about the health check commands available in the system.

## Overview

The health check commands are designed to monitor and report the health status of various system components:

- Service Health Check: Monitors the overall health of services
- Database Health Check: Checks database connectivity and performance
- Security Health Check: Verifies security configurations and status

## Service Health Check

### Usage

```bash
health check service [--services service1,service2]
```

### Parameters

- `--services`: Optional comma-separated list of services to check. If not provided, checks all services.

### Output Format

```json
{
    "status": "healthy|unhealthy",
    "timestamp": "ISO-8601 timestamp",
    "details": {
        "services": {
            "service_name": {
                "healthy": true|false,
                "status": "operational|error",
                "health": {
                    "healthy": true|false,
                    "status": "running|stopped",
                    "details": { ... }
                },
                "dependencies": {
                    "healthy": true|false,
                    "dependencies": {
                        "dependency_name": {
                            "status": "available|unavailable",
                            "details": { ... }
                        }
                    }
                },
                "resources": {
                    "healthy": true|false,
                    "metrics": { ... },
                    "thresholds": { ... },
                    "issues": [ ... ]
                },
                "endpoints": {
                    "healthy": true|false,
                    "endpoints": {
                        "endpoint_path": {
                            "status": "healthy|unhealthy",
                            "response_time": number,
                            "details": { ... }
                        }
                    }
                }
            }
        }
    }
}
```

### Error Codes

- `SERVICE_NOT_FOUND`: Service does not exist
- `SERVICE_NOT_RUNNING`: Service is not running
- `DEPENDENCY_UNAVAILABLE`: Service dependency is not available
- `RESOURCE_THRESHOLD_EXCEEDED`: Service resource usage exceeds threshold
- `ENDPOINT_UNHEALTHY`: Service endpoint is not responding

## Database Health Check

### Usage

```bash
health check database
```

### Output Format

```json
{
    "status": "healthy|unhealthy",
    "timestamp": "ISO-8601 timestamp",
    "details": {
        "connection": {
            "healthy": true|false,
            "status": "connected|disconnected",
            "details": { ... }
        },
        "queries": {
            "healthy": true|false,
            "execution": {
                "status": "success|error",
                "result": { ... }
            },
            "statistics": { ... }
        },
        "pool": {
            "healthy": true|false,
            "statistics": { ... },
            "configuration": { ... }
        },
        "transactions": {
            "healthy": true|false,
            "execution": {
                "status": "success|error",
                "result": { ... }
            },
            "statistics": { ... }
        },
        "performance": {
            "healthy": true|false,
            "metrics": { ... },
            "thresholds": { ... },
            "issues": [ ... ]
        }
    }
}
```

### Error Codes

- `DATABASE_NOT_AVAILABLE`: Database service is not available
- `CONNECTION_FAILED`: Failed to connect to database
- `QUERY_FAILED`: Failed to execute test query
- `POOL_EXHAUSTED`: Connection pool is full
- `TRANSACTION_FAILED`: Failed to execute test transaction
- `PERFORMANCE_DEGRADED`: Database performance metrics exceed thresholds

## Security Health Check

### Usage

```bash
health check security
```

### Output Format

```json
{
    "status": "healthy|unhealthy",
    "timestamp": "ISO-8601 timestamp",
    "details": {
        "authentication": {
            "healthy": true|false,
            "methods": {
                "method_name": {
                    "status": "active|inactive",
                    "details": { ... }
                }
            }
        },
        "authorization": {
            "rbac_enabled": true|false,
            "roles": {
                "role_name": {
                    "status": "active",
                    "permissions": [ ... ]
                }
            }
        },
        "ssl": {
            "healthy": true|false,
            "certificate": {
                "valid": true|false,
                "file": "path/to/cert"
            }
        },
        "tokens": {
            "healthy": true|false,
            "jwt_configured": true|false,
            "token_validation": true|false
        },
        "services": {
            "healthy": true|false,
            "services": {
                "service_name": {
                    "status": "secure|insecure",
                    "config": { ... },
                    "details": { ... }
                }
            }
        }
    }
}
```

### Error Codes

- `AUTH_SERVICE_UNAVAILABLE`: Authentication service is not available
- `AUTH_SERVICE_NOT_RUNNING`: Authentication service is not running
- `RBAC_NOT_ENABLED`: Role-based access control is not enabled
- `SSL_NOT_CONFIGURED`: SSL certificate is not configured
- `JWT_NOT_CONFIGURED`: JWT secret is not configured
- `SERVICE_INSECURE`: Service security check failed

## Health Metrics

The health check commands collect and report various metrics:

### Service Metrics
- CPU Usage (%)
- Memory Usage (%)
- Disk Usage (%)
- Response Time (ms)
- Error Rate (%)
- Request Rate (req/s)

### Database Metrics
- Connection Count
- Active Queries
- Query Response Time (ms)
- Transaction Rate (tx/s)
- Rollback Rate (%)
- Cache Hit Rate (%)

### Security Metrics
- Authentication Success Rate (%)
- Authorization Success Rate (%)
- Token Validation Rate (%)
- SSL Certificate Expiry (days)
- Security Policy Compliance (%)

## Troubleshooting

### Common Issues

1. Service Not Responding
   - Check if service is running
   - Check service logs
   - Verify network connectivity
   - Check resource usage

2. Database Connection Issues
   - Verify database service is running
   - Check connection string
   - Check network connectivity
   - Verify credentials
   - Check connection pool settings

3. Security Configuration Issues
   - Verify SSL certificate configuration
   - Check JWT secret configuration
   - Verify RBAC settings
   - Check service security policies

### Best Practices

1. Regular Health Checks
   - Schedule periodic health checks
   - Monitor trends in metrics
   - Set up alerts for threshold violations

2. Resource Management
   - Monitor resource usage trends
   - Adjust thresholds based on patterns
   - Plan capacity based on metrics

3. Security Maintenance
   - Rotate SSL certificates before expiry
   - Update security configurations
   - Review security policies regularly 