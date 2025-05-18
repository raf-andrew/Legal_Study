# Security Guide

This guide explains the security system in the Legal Study Platform.

## Overview

The platform implements a comprehensive security system with support for:

- Authentication and authorization
- Data encryption
- Input validation
- Security headers
- Rate limiting
- Audit logging

## Authentication and Authorization

### 1. JWT Authentication

```python
# app/security/jwt.py
from datetime import datetime, timedelta
from typing import Dict, Any
import jwt
from app.config import config

class JWTHandler:
    def __init__(self):
        self.secret = config['jwt']['secret']
        self.algorithm = config['jwt']['algorithm']
        self.access_token_expiry = config['jwt']['access_token_expiry']
        self.refresh_token_expiry = config['jwt']['refresh_token_expiry']

    def create_access_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(seconds=self.access_token_expiry)
        to_encode.update({'exp': expire, 'type': 'access'})
        return jwt.encode(to_encode, self.secret, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(seconds=self.refresh_token_expiry)
        to_encode.update({'exp': expire, 'type': 'refresh'})
        return jwt.encode(to_encode, self.secret, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.JWTError:
            raise ValueError("Invalid token")
```

### 2. Role-Based Access Control

```python
# app/security/rbac.py
from enum import Enum
from typing import List, Set
from functools import wraps
from flask import g, abort

class Role(Enum):
    ADMIN = 'admin'
    USER = 'user'
    GUEST = 'guest'

class Permission(Enum):
    READ = 'read'
    WRITE = 'write'
    DELETE = 'delete'
    MANAGE = 'manage'

ROLE_PERMISSIONS = {
    Role.ADMIN: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.MANAGE},
    Role.USER: {Permission.READ, Permission.WRITE},
    Role.GUEST: {Permission.READ}
}

def require_permission(permission: Permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.user:
                abort(401)

            user_permissions = ROLE_PERMISSIONS.get(g.user.role, set())
            if permission not in user_permissions:
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

## Data Encryption

### 1. Password Hashing

```python
# app/security/password.py
import bcrypt
from typing import Tuple

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```

### 2. Data Encryption

```python
# app/security/encryption.py
from cryptography.fernet import Fernet
from app.config import config

class Encryption:
    def __init__(self):
        self.key = config['encryption']['key'].encode()
        self.cipher_suite = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        return self.cipher_suite.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
```

## Input Validation

### 1. Request Validation

```python
# app/security/validation.py
from marshmallow import Schema, fields, validate, ValidationError

class UserSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))
    name = fields.Str(validate=validate.Length(max=100))

class DocumentSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(max=200))
    content = fields.Str(required=True)
    type = fields.Str(required=True, validate=validate.OneOf(['legal', 'contract', 'policy']))

def validate_request(schema: Schema, data: dict) -> dict:
    try:
        return schema.load(data)
    except ValidationError as e:
        raise ValueError(str(e))
```

### 2. SQL Injection Prevention

```python
# app/security/sql.py
from sqlalchemy import text
from typing import Any, Dict

def safe_query(query: str, params: Dict[str, Any] = None) -> text:
    return text(query).bindparams(**(params or {}))
```

## Security Headers

### 1. Middleware

```python
# app/security/headers.py
from flask import request, make_response
from functools import wraps

def security_headers(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))

        # Set security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response
    return decorated_function
```

### 2. CORS Configuration

```python
# app/security/cors.py
from flask_cors import CORS
from app.config import config

def configure_cors(app):
    CORS(app, resources={
        r"/api/*": {
            "origins": config['cors']['allowed_origins'],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Range", "X-Content-Range"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
```

## Rate Limiting

### 1. Rate Limiter

```python
# app/security/rate_limit.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import config

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=config['redis']['url']
)

def rate_limit(limit_string: str):
    def decorator(f):
        return limiter.limit(limit_string)(f)
    return decorator
```

### 2. Usage

```python
# app/routes/api.py
from app.security.rate_limit import rate_limit

@api.route('/documents', methods=['GET'])
@rate_limit("100 per minute")
def get_documents():
    # ... implementation
```

## Audit Logging

### 1. Logger

```python
# app/security/audit.py
import logging
from datetime import datetime
from typing import Dict, Any
from app.models import AuditLog

class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger('audit')

    def log(self, action: str, user_id: int, details: Dict[str, Any] = None):
        log_entry = AuditLog(
            action=action,
            user_id=user_id,
            details=details or {},
            timestamp=datetime.utcnow()
        )
        log_entry.save()
        self.logger.info(f"Audit: {action} by user {user_id}")
```

### 2. Usage

```python
# app/routes/api.py
from app.security.audit import AuditLogger

audit_logger = AuditLogger()

@api.route('/documents/<int:id>', methods=['DELETE'])
@require_permission(Permission.DELETE)
def delete_document(id):
    document = Document.query.get_or_404(id)
    document.delete()

    audit_logger.log(
        action='document_delete',
        user_id=g.user.id,
        details={'document_id': id}
    )

    return jsonify({'message': 'Document deleted'})
```

## Security Configuration

### 1. Security Settings

```python
# config/security.py
SECURITY = {
    'jwt': {
        'secret': 'your-secret-key',
        'algorithm': 'HS256',
        'access_token_expiry': 3600,
        'refresh_token_expiry': 604800
    },
    'password': {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_numbers': True,
        'require_special': True
    },
    'encryption': {
        'key': 'your-encryption-key'
    },
    'cors': {
        'allowed_origins': ['https://app.example.com']
    },
    'rate_limit': {
        'default': '200 per day',
        'api': '1000 per hour'
    }
}
```

### 2. Environment Variables

```bash
# .env
JWT_SECRET=your-secret-key
ENCRYPTION_KEY=your-encryption-key
CORS_ORIGINS=https://app.example.com
RATE_LIMIT_DEFAULT=200 per day
RATE_LIMIT_API=1000 per hour
```

## Security Best Practices

1. **Authentication**:
   - Use strong password policies
   - Implement 2FA
   - Use secure session management
   - Implement account lockout

2. **Authorization**:
   - Follow principle of least privilege
   - Implement role-based access
   - Validate permissions
   - Audit access logs

3. **Data Protection**:
   - Encrypt sensitive data
   - Use secure communication
   - Implement data backup
   - Follow data retention policies

4. **Application Security**:
   - Validate all input
   - Prevent SQL injection
   - Implement CSRF protection
   - Use security headers

## Security Monitoring

### 1. Security Metrics

```python
# app/security/monitoring.py
from prometheus_client import Counter, Histogram
from functools import wraps

# Metrics
failed_login_attempts = Counter(
    'failed_login_attempts_total',
    'Total number of failed login attempts'
)

request_duration = Histogram(
    'request_duration_seconds',
    'Request duration in seconds',
    ['endpoint']
)

def track_security_metrics(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        with request_duration.labels(f.__name__).time():
            return f(*args, **kwargs)
    return decorated_function
```

### 2. Alerting

```python
# app/security/alerting.py
import smtplib
from email.message import EmailMessage
from app.config import config

class SecurityAlert:
    def __init__(self):
        self.smtp_server = config['email']['smtp_server']
        self.smtp_port = config['email']['smtp_port']
        self.sender = config['email']['sender']
        self.recipients = config['email']['security_team']

    def send_alert(self, subject: str, message: str):
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = self.recipients

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.send_message(msg)
```

## Security Testing

### 1. Security Tests

```python
# tests/security/test_security.py
import pytest
from app.security import JWTHandler, Encryption

def test_jwt_security():
    jwt_handler = JWTHandler()

    # Test token creation
    token = jwt_handler.create_access_token({'user_id': 1})
    assert token is not None

    # Test token verification
    payload = jwt_handler.verify_token(token)
    assert payload['user_id'] == 1

    # Test expired token
    with pytest.raises(ValueError):
        jwt_handler.verify_token('expired_token')

def test_encryption():
    encryption = Encryption()

    # Test encryption
    data = 'sensitive_data'
    encrypted = encryption.encrypt(data)
    assert encrypted != data

    # Test decryption
    decrypted = encryption.decrypt(encrypted)
    assert decrypted == data
```

### 2. Penetration Testing

```python
# tests/security/test_penetration.py
import pytest
from app import create_app

def test_sql_injection():
    app = create_app('testing')
    client = app.test_client()

    # Test SQL injection
    response = client.get('/api/documents?title=1%27%20OR%201%3D1')
    assert response.status_code == 400

def test_xss_attack():
    app = create_app('testing')
    client = app.test_client()

    # Test XSS attack
    response = client.post('/api/documents', json={
        'title': '<script>alert("xss")</script>',
        'content': 'Test content'
    })
    assert response.status_code == 400
```

## Troubleshooting

1. **Authentication Issues**:
   - Check token expiration
   - Verify credentials
   - Check account status
   - Review access logs

2. **Authorization Issues**:
   - Verify user roles
   - Check permissions
   - Review access policies
   - Check audit logs

3. **Security Issues**:
   - Review security logs
   - Check for vulnerabilities
   - Monitor failed attempts
   - Review security alerts

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT Best Practices](https://auth0.com/blog/jwt-security-best-practices/)
- [Security Headers](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers#security)
- [Rate Limiting](https://www.nginx.com/blog/rate-limiting-nginx/)
