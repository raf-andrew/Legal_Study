# Health Check Command User Guide

## Overview
The health check command is a powerful tool for monitoring and verifying the health of various services and components in the Legal Study application. This guide will help you understand how to use the command effectively.

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Legal Study application installed

### Dependencies
```bash
pip install -r requirements.txt
```

## Basic Usage

### Quick Health Check
To perform a basic health check of all services:
```bash
health
```

This will return a JSON response with the current health status of all services.

### Specific Checks
To check specific services or components:
```bash
health --check services
health --check metrics
health --check logs
health --check errors
```

You can combine multiple checks:
```bash
health --check services --check metrics
```

## Command Options

### Report Generation
To generate a detailed report:
```bash
health --report
```

This includes:
- Overall health status
- Individual check results
- Performance metrics
- Recommendations

### Output Format
Choose from different output formats:
```bash
health --format json    # JSON format (default)
health --format yaml    # YAML format
health --format text    # Human-readable text
```

### Logging Level
Control the logging verbosity:
```bash
health --log-level DEBUG    # Detailed debugging
health --log-level INFO     # Standard information
health --log-level WARNING  # Warnings only
health --log-level ERROR    # Errors only
```

## Understanding Output

### Basic Response
```json
{
  "status": "healthy",
  "timestamp": "2024-03-19T12:00:00Z",
  "checks": {
    "services": {
      "status": "healthy",
      "details": {}
    }
  }
}
```

- `status`: Overall health status
- `timestamp`: Check execution time
- `checks`: Individual check results

### Service Status
Services can have the following states:
- `healthy`: Service is functioning normally
- `unhealthy`: Service has issues but is running
- `error`: Service has critical issues

### Metrics
The metrics check provides:
- Service performance data
- Resource utilization
- Error rates
- Response times

### Logs
The logs check shows:
- Log system status
- Recent log entries
- Log handler status
- Log volume metrics

### Errors
The errors check displays:
- Current error states
- Error history
- Error patterns
- Recovery status

## Configuration

### Environment Variables
Set default behavior:
```bash
export LOG_LEVEL=INFO
export OUTPUT_FORMAT=json
export REPORT_ENABLED=true
```

### Configuration File
Create `.config/health_check.yaml`:
```yaml
health_check:
  default_format: json
  log_level: INFO
  report_enabled: false
  check_timeout: 5000
  retry_attempts: 3
```

## Best Practices

### Regular Monitoring
- Run basic health checks periodically
- Monitor trends over time
- Set up automated checks
- Configure alerts for issues

### Troubleshooting
1. Start with basic check
2. Enable detailed reporting
3. Check specific services
4. Review logs
5. Follow recommendations

### Performance
- Use specific checks when possible
- Avoid unnecessary detailed reports
- Configure appropriate timeouts
- Monitor resource usage

## Common Scenarios

### System Startup
Verify all services are running:
```bash
health --check services --report
```

### Performance Issues
Check metrics and errors:
```bash
health --check metrics --check errors --format yaml
```

### Debug Mode
Enable detailed logging:
```bash
health --log-level DEBUG --report
```

### Continuous Monitoring
Regular health checks:
```bash
while true; do health --format text; sleep 60; done
```

## Error Handling

### Common Errors
1. Service not available
   ```bash
   health --check services
   # Response shows service status as "error"
   ```

2. Configuration issues
   ```bash
   health
   # Check configuration in error message
   ```

3. Authentication failure
   ```bash
   health --check protected_service
   # Verify credentials
   ```

### Recovery Steps
1. Check service status
2. Review error messages
3. Verify configuration
4. Check credentials
5. Restart services if needed

## Monitoring

### Key Metrics
- Service health status
- Response times
- Error rates
- Resource utilization
- Check execution time

### Alerting
Configure alerts for:
- Service failures
- High error rates
- Performance issues
- Resource constraints
- Security events

## Security

### Authentication
Use appropriate credentials:
```bash
export SERVICE_TOKEN=your_token
health --check protected_service
```

### Authorization
Ensure proper permissions:
- Service access rights
- Report generation rights
- Configuration access

### Audit
Monitor access:
- Command usage
- Service checks
- Configuration changes
- Error patterns

## Support

### Getting Help
View command help:
```bash
health --help
```

### Debugging
Enable debug output:
```bash
health --log-level DEBUG
```

### Reporting Issues
Include in bug reports:
- Command output
- Error messages
- Configuration
- Environment details

## References

### Documentation
- API Documentation: `.controls/api/health_check_api.md`
- Security Guide: `.controls/security/health_check_security.md`
- Test Guide: `.controls/test/health_check_test.md`

### Code
- Command Implementation: `.controls/commands/health/command.py`
- Unit Tests: `.controls/unit/test_health_command.py`
- Integration Tests: `.controls/integration/test_health_command.py`

### Configuration
- Default Config: `.config/health_check.yaml`
- Environment Variables: `.env.example`
- Service Definitions: `.config/services.yaml` 