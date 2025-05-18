# Health Check Command

## Directory Structure

```
.controls/commands/health/
├── __init__.py
├── command.py       # Main command implementation
├── cli.py          # CLI interface
├── check.py        # Health check implementation
├── config.py       # Configuration handling
├── formatters/     # Output formatters
│   ├── __init__.py
│   ├── json.py
│   ├── yaml.py
│   └── text.py
├── checks/         # Individual checks
│   ├── __init__.py
│   ├── services.py
│   ├── metrics.py
│   ├── logs.py
│   └── errors.py
└── utils/          # Utility functions
    ├── __init__.py
    ├── validation.py
    └── formatting.py
```

## Command Structure

The health check command is organized into several components:

1. Command Interface (`command.py`)
   - Main command class
   - Command registration
   - Option handling
   - Execution flow

2. CLI Interface (`cli.py`)
   - Click command group
   - Command options
   - Output handling
   - Error handling

3. Health Checks (`check.py`)
   - Health check implementation
   - Check registration
   - Check execution
   - Result aggregation

4. Configuration (`config.py`)
   - Configuration loading
   - Environment handling
   - Validation
   - Defaults

5. Formatters
   - JSON output
   - YAML output
   - Text output
   - Custom formats

6. Individual Checks
   - Service health
   - Metrics collection
   - Logging system
   - Error tracking

7. Utilities
   - Input validation
   - Output formatting
   - Error handling
   - Logging

## Testing

Tests are organized in corresponding directories:

1. `.unit/` - Unit tests
2. `.integration/` - Integration tests
3. `.chaos/` - Chaos tests
4. `.security/` - Security tests

## Documentation

Documentation is organized in:

1. `.guide/` - User guides
2. `.api/` - API documentation
3. `.security/` - Security documentation
4. `.qa/` - Quality assurance
5. `.sniff/` - Code sniffing
6. `.refactoring/` - Refactoring notes

## Development Process

1. Implementation
   - Follow TDD approach
   - Write tests first
   - Implement features
   - Refactor code

2. Testing
   - Run unit tests
   - Run integration tests
   - Run chaos tests
   - Run security tests

3. Documentation
   - Update guides
   - Update API docs
   - Update security docs
   - Update QA docs

4. Review
   - Code review
   - Security review
   - Documentation review
   - Test review 