# Security Configuration Prompt

## Context
Security configuration is critical for protecting the application and its users. This prompt provides guidance on setting up secure configurations.

## Environment Variables

### JWT Configuration
```ini
# Secret key for JWT signing (min 32 chars)
JWT_SECRET_KEY=your-secure-jwt-secret-key-here

# JWT algorithm (HS256, HS384, HS512)
JWT_ALGORITHM=HS256

# Token expiration times (in seconds)
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7 days
```

### Password Policy
```ini
# Password requirements
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=True
PASSWORD_REQUIRE_LOWERCASE=True
PASSWORD_REQUIRE_NUMBERS=True
PASSWORD_REQUIRE_SPECIAL=True
PASSWORD_SALT_ROUNDS=12  # For bcrypt
```

### Rate Limiting
```ini
# Rate limiting settings
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10
RATE_LIMIT_STORAGE_URL=memory://
```

### CORS Configuration
```ini
# CORS settings
CORS_ORIGINS=["http://localhost:3000"]
CORS_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_HEADERS=["Authorization", "Content-Type"]
CORS_EXPOSE_HEADERS=["X-Total-Count"]
CORS_MAX_AGE=600
CORS_ALLOW_CREDENTIALS=True
```

### Security Headers
```ini
# Security headers
SECURE_HEADERS=True
X_FRAME_OPTIONS=DENY
X_CONTENT_TYPE_OPTIONS=nosniff
X_XSS_PROTECTION=1; mode=block
STRICT_TRANSPORT_SECURITY=max-age=31536000; includeSubDomains
CONTENT_SECURITY_POLICY=default-src 'self'; img-src 'self' data:; script-src 'self'
```

## Implementation Examples

### JWT Handling
```python
from datetime import datetime, timedelta
import jwt

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES')))
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        os.getenv('JWT_SECRET_KEY'),
        algorithm=os.getenv('JWT_ALGORITHM')
    )

def verify_token(token: str):
    try:
        payload = jwt.decode(
            token,
            os.getenv('JWT_SECRET_KEY'),
            algorithms=[os.getenv('JWT_ALGORITHM')]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Password Hashing
```python
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=int(os.getenv('PASSWORD_SALT_ROUNDS')))
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode(),
        hashed_password.encode()
    )
```

### Rate Limiting
```python
from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/resource")
@limiter.limit(os.getenv('RATE_LIMIT_PER_MINUTE') + "/minute")
async def read_resource(request: Request):
    return {"message": "Success"}
```

### CORS Middleware
```python
from fastapi.middleware.cors import CORSMiddleware
import json

app.add_middleware(
    CORSMiddleware,
    allow_origins=json.loads(os.getenv('CORS_ORIGINS')),
    allow_methods=json.loads(os.getenv('CORS_METHODS')),
    allow_headers=json.loads(os.getenv('CORS_HEADERS')),
    expose_headers=json.loads(os.getenv('CORS_EXPOSE_HEADERS')),
    allow_credentials=os.getenv('CORS_ALLOW_CREDENTIALS') == 'True',
    max_age=int(os.getenv('CORS_MAX_AGE'))
)
```

### Security Headers Middleware
```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Frame-Options'] = os.getenv('X_FRAME_OPTIONS')
        response.headers['X-Content-Type-Options'] = os.getenv('X_CONTENT_TYPE_OPTIONS')
        response.headers['X-XSS-Protection'] = os.getenv('X_XSS_PROTECTION')
        response.headers['Strict-Transport-Security'] = os.getenv('STRICT_TRANSPORT_SECURITY')
        response.headers['Content-Security-Policy'] = os.getenv('CONTENT_SECURITY_POLICY')
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

## Best Practices

### Secret Management
1. Use environment variables
2. Never commit secrets
3. Use different keys per environment
4. Rotate keys regularly
5. Use secure key generation

### Password Security
1. Use strong hashing (bcrypt)
2. Enforce password policy
3. Implement rate limiting
4. Add account lockout
5. Use secure password reset

### API Security
1. Use HTTPS only
2. Implement rate limiting
3. Validate all input
4. Use proper error handling
5. Add request logging

### Token Security
1. Short expiration times
2. Implement refresh flow
3. Use secure algorithms
4. Validate all tokens
5. Add token revocation

### Headers Security
1. Set security headers
2. Configure CORS properly
3. Use HSTS
4. Enable XSS protection
5. Set CSP headers

## Monitoring

### Security Events
1. Failed login attempts
2. Rate limit violations
3. Invalid tokens
4. Suspicious patterns
5. Error rates

### Metrics
1. Authentication success/failure
2. Token usage
3. Rate limit hits
4. Resource usage
5. Response times

## Documentation
1. Security policies
2. API documentation
3. Error codes
4. Rate limits
5. Token usage 