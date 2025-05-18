# Security Context Documentation

## Overview

The security context system provides a unified way to manage and access security-related information during command execution. It encapsulates authentication, authorization, and execution context information.

## Components

### Authentication Context

The authentication context holds user identity and authentication information:

```python
@dataclass
class AuthenticationContext:
    user_id: str
    username: str
    roles: list[str]
    permissions: list[str]
    authenticated_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
```

#### Properties:
- **user_id**: Unique identifier for the user
- **username**: User's display name
- **roles**: List of assigned roles
- **permissions**: List of granted permissions
- **authenticated_at**: Authentication timestamp
- **expires_at**: Optional expiration timestamp
- **metadata**: Additional authentication metadata

### Validation Context

The validation context holds command validation information:

```python
@dataclass
class ValidationContext:
    command_name: str
    arguments: Dict[str, Any]
    user_id: Optional[str] = None
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    environment: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
```

#### Properties:
- **command_name**: Name of the command being validated
- **arguments**: Command arguments
- **user_id**: Optional user identifier
- **roles**: Set of user roles
- **permissions**: Set of user permissions
- **environment**: Environment information
- **metadata**: Additional validation metadata
- **timestamp**: Validation timestamp

## Usage Examples

### Authentication Context

1. Create authentication context:
```python
context = AuthenticationContext(
    user_id="user123",
    username="john_doe",
    roles=["user", "admin"],
    permissions=["read", "write"],
    authenticated_at=datetime.now(),
    expires_at=datetime.now() + timedelta(hours=1),
    metadata={"device": "web"}
)
```

2. Check expiration:
```python
if context.is_expired:
    # Handle expired context
```

3. Check permissions:
```python
if context.has_permission("write"):
    # Allow write operation
```

### Validation Context

1. Create validation context:
```python
context = ValidationContext(
    command_name="create_document",
    arguments={
        "title": "Test Document",
        "content": "Test Content"
    },
    user_id="user123",
    roles={"user", "editor"},
    permissions={"document.create"},
    environment={"env": "production"}
)
```

2. Use in validation:
```python
result = validation_rule.validate(context)
if not result.is_valid:
    # Handle validation failure
```

## Context Flow

### Authentication Flow

1. User Authentication:
   ```
   Login Request -> Authentication Provider -> Authentication Context
   ```

2. Token Validation:
   ```
   Token -> Authentication Provider -> Authentication Context
   ```

3. Context Update:
   ```
   Token Refresh -> New Authentication Context
   ```

### Validation Flow

1. Command Validation:
   ```
   Command -> Validation Context -> Validation Rules -> Validation Result
   ```

2. Security Checks:
   ```
   Validation Context -> Security Rules -> Security Result
   ```

3. Context Propagation:
   ```
   Parent Context -> Child Context -> Nested Validation
   ```

## Security Considerations

### Context Security
- Immutable context objects
- Secure context propagation
- Context validation
- Context isolation
- Context cleanup

### Data Security
- Sensitive data handling
- Context serialization
- Context storage
- Context transmission
- Data sanitization

## Error Handling

### Common Errors

1. Context Errors:
   - Invalid context data
   - Missing required fields
   - Context validation failure
   - Context expiration

2. Propagation Errors:
   - Context corruption
   - Context isolation failure
   - Context chain break
   - Context overflow

### Error Response Format

```json
{
    "error": "context_error",
    "message": "Context validation failed",
    "details": {
        "context_type": "authentication",
        "validation_errors": [
            "missing_field: user_id",
            "invalid_value: roles"
        ]
    }
}
```

## Monitoring and Logging

### Event Types

1. Context Events:
   - `CONTEXT_CREATE`
   - `CONTEXT_UPDATE`
   - `CONTEXT_EXPIRE`
   - `CONTEXT_VALIDATE`

2. Security Events:
   - `CONTEXT_VIOLATION`
   - `CONTEXT_CORRUPTION`
   - `CONTEXT_OVERFLOW`
   - `CONTEXT_BREACH`

### Event Format

```json
{
    "event_type": "context.create",
    "severity": "info",
    "timestamp": "iso_timestamp",
    "context_id": "ctx123",
    "details": {
        "type": "authentication",
        "user_id": "user123",
        "source": "login"
    }
}
```

## Testing

### Unit Tests

1. Context Tests:
   - Test context creation
   - Test context validation
   - Test context expiration
   - Test context isolation

2. Flow Tests:
   - Test context propagation
   - Test context inheritance
   - Test context cleanup
   - Test context security

### Integration Tests

1. Context Flow:
   - Test complete context lifecycle
   - Test context interactions
   - Test context boundaries
   - Test context performance

2. Security Tests:
   - Test context isolation
   - Test context corruption
   - Test context overflow
   - Test context breach

## Best Practices

1. Context Design:
   - Immutable contexts
   - Clear boundaries
   - Minimal scope
   - Regular cleanup

2. Security:
   - Validate all contexts
   - Secure propagation
   - Monitor usage
   - Regular audits

3. Performance:
   - Efficient context creation
   - Context pooling
   - Context caching
   - Context optimization

4. Testing:
   - Comprehensive testing
   - Security testing
   - Performance testing
   - Integration testing

## References

1. [Context Pattern](https://www.patterns.dev/posts/context-pattern/)
2. [Security Contexts](https://docs.spring.io/spring-security/reference/servlet/authentication/architecture.html)
3. [Python Context Management](https://docs.python.org/3/reference/datamodel.html#context-managers)
4. [Security Best Practices](https://owasp.org/www-project-top-ten/) 