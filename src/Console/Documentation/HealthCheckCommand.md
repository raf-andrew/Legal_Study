# Health Check Command

## Overview
The `health:check` command provides a comprehensive health check of the Legal Study System components. It can check individual components or perform a system-wide health assessment.

## Usage
```bash
php console.php health:check [options]
```

## Options
- `--component`: Specify which component to check (default: all)
  - Available components: database, cache, security
- `--verbose`: Show detailed health information (default: false)

## Examples

### Basic Health Check
```bash
php console.php health:check
```

### Check Specific Component
```bash
php console.php health:check --component=database
```

### Detailed Health Check
```bash
php console.php health:check --verbose
```

### Check Specific Component with Details
```bash
php console.php health:check --component=security --verbose
```

## Output Format
The command provides color-coded output:
- Green: Component is healthy
- Red: Component has issues
- Yellow: Component has warnings

When verbose mode is enabled, additional details are shown for each component.

## Exit Codes
- `0`: All components are healthy
- `1`: One or more components have issues

## Implementation Details
The command checks the following aspects:

### Database
- Connection status
- Query execution
- Response time
- Version compatibility

### Cache
- Connection status
- Read/Write operations
- Memory usage
- Hit rate

### Security
- Authentication systems
- Authorization checks
- Vulnerability status
- Last security scan

## Error Handling
The command includes comprehensive error handling:
- Invalid component names are ignored
- Connection failures are properly reported
- Timeouts are handled gracefully
- Detailed error messages are provided in verbose mode

## Testing
The command is thoroughly tested with:
- Unit tests for all components
- Integration tests for system interactions
- Error scenario testing
- Performance testing

## Security Considerations
- No sensitive information is exposed in non-verbose mode
- All security checks are performed with appropriate permissions
- Error messages are sanitized to prevent information leakage 