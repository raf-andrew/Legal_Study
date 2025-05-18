# Health Check Command API Documentation

## Overview
The health check command provides a comprehensive system for checking the health of various services and components in the Legal Study application. It supports multiple check types, detailed reporting, and various output formats.

## Command Interface

### Basic Usage
```bash
health [OPTIONS]
```

### Options
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--check`, `-c` | CHOICE | All checks | Specific checks to run |
| `--report`, `-r` | FLAG | False | Generate detailed report |
| `--format`, `-f` | CHOICE | json | Output format (json, yaml, text) |
| `--log-level`, `-l` | CHOICE | INFO | Logging level |

### Check Types
- `services`: Check service health
- `metrics`: Check metrics collection
- `logs`: Check logging system
- `errors`: Check for service errors

## Response Format

### Basic Response
```json
{
  "status": "healthy",
  "timestamp": "2024-03-19T12:00:00Z",
  "checks": {
    "services": {
      "status": "healthy",
      "details": {
        "healthy": true,
        "services": {
          "api": {
            "status": "healthy",
            "started_at": "2024-03-19T11:00:00Z",
            "total_calls": 100,
            "total_errors": 0
          }
        }
      }
    }
  }
}
```

### Detailed Report
```json
{
  "status": "healthy",
  "timestamp": "2024-03-19T12:00:00Z",
  "checks": {
    "services": {
      "status": "healthy",
      "details": {}
    }
  },
  "report": {
    "summary": {
      "total_checks": 4,
      "healthy_checks": 4,
      "unhealthy_checks": 0,
      "error_checks": 0,
      "health_percentage": 100
    },
    "recommendations": []
  }
}
```

## Service Checks

### Service Health Check
Checks the health of all registered services.

**Response Fields:**
- `healthy`: Boolean indicating overall health
- `services`: Object containing service-specific health information
  - `status`: Service status (healthy, unhealthy, error)
  - `started_at`: Service start time
  - `total_calls`: Total number of service calls
  - `total_errors`: Total number of service errors

### Metrics Check
Checks the metrics collection system.

**Response Fields:**
- `healthy`: Boolean indicating metrics system health
- `metrics`: Object containing collected metrics
  - Metric name: Object containing metric data
    - `type`: Metric type (counter, gauge, histogram)
    - `values`: Metric values

### Logs Check
Checks the logging system.

**Response Fields:**
- `healthy`: Boolean indicating logging system health
- `handlers`: Object containing handler information
  - Handler name: Object containing handler stats
    - `total_records`: Total number of log records
    - `last_record`: Most recent log record

### Errors Check
Checks for service errors.

**Response Fields:**
- `healthy`: Boolean indicating error status
- `errors`: Object containing service errors
  - Service name: Array of error objects
    - `error`: Error message
    - `type`: Error type
    - `timestamp`: Error occurrence time

## Status Codes

| Code | Description |
|------|-------------|
| 0 | Success - All checks healthy |
| 1 | Warning - Some checks unhealthy |
| 2 | Error - Command execution failed |

## Error Handling

### Error Response
```json
{
  "status": "error",
  "timestamp": "2024-03-19T12:00:00Z",
  "error": "Error message"
}
```

### Common Errors
- Invalid check type
- Service not available
- Configuration error
- Authentication failure
- Authorization failure

## Examples

### Basic Health Check
```bash
health
```

### Specific Service Check
```bash
health --check services
```

### Detailed Report
```bash
health --report
```

### Custom Format
```bash
health --format yaml --report
```

### Debug Output
```bash
health --log-level DEBUG
```

## Integration

### Service Registry
The health check command uses the mock service registry to access and check services:

```python
from ...mocks.registry import MockServiceRegistry

registry = MockServiceRegistry()
registry.create_all_services()
registry.start_all()
```

### Service Interface
Services must implement the following methods:
- `get_metrics()`: Return service metrics
- `get_errors()`: Return service errors
- `start()`: Start the service
- `stop()`: Stop the service

### Output Formatting
The command supports multiple output formats through the formatter service:

```python
formatter = registry.get_service("formatters")
output = formatter.format_output(result, format)
```

## Configuration

### Environment Variables
- `LOG_LEVEL`: Default logging level
- `OUTPUT_FORMAT`: Default output format
- `REPORT_ENABLED`: Enable detailed reporting by default

### Configuration File
```yaml
health_check:
  default_format: json
  log_level: INFO
  report_enabled: false
  check_timeout: 5000
  retry_attempts: 3
```

## Security

### Authentication
The command supports authentication through:
- API tokens
- Service credentials
- Environment-based auth

### Authorization
Access control is managed through:
- Role-based access
- Service-level permissions
- Environment restrictions

## Performance

### Timeouts
- Command timeout: 30s
- Service check timeout: 5s
- Report generation timeout: 10s

### Caching
- Service status: 60s
- Metrics data: 30s
- Error data: 0s (no cache)

## Monitoring

### Metrics
- Command execution time
- Check execution time
- Error rate
- Success rate
- Resource usage

### Logging
- Command invocation
- Check execution
- Error occurrence
- Performance data
- Security events

## References

### Code Files
- `.controls/commands/health/command.py`: Main implementation
- `.controls/unit/test_health_command.py`: Unit tests
- `.controls/integration/test_health_command.py`: Integration tests
- `.controls/chaos/test_health_command_chaos.py`: Chaos tests

### Documentation
- `.guide/health_check_guide.md`: User guide
- `.test/health_check_test.md`: Test documentation
- `.security/health_check_security.md`: Security documentation
- `.refactoring/health_check_refactor.md`: Refactoring guide 