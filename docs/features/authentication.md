# Authentication Guide

This guide explains the authentication system in the Legal Study Platform.

## Overview

The platform uses JWT (JSON Web Tokens) for authentication, with support for:

- Email/password authentication
- Social authentication (Google, GitHub)
- Two-factor authentication
- Session management
- Role-based access control

## Authentication Flow

1. **Registration**:
   - User provides email and password
   - System validates input
   - System creates user account
   - System sends verification email
   - System returns JWT token

2. **Login**:
   - User provides credentials
   - System validates credentials
   - System checks 2FA if enabled
   - System creates session
   - System returns JWT token

3. **Token Usage**:
   - Client includes token in requests
   - System validates token
   - System checks permissions
   - System processes request

4. **Token Refresh**:
   - Client requests new token
   - System validates refresh token
   - System creates new access token
   - System returns new token

## Implementation

### 1. User Model

```python
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2. Authentication Service

```python
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from app.config import config
from app.models import User
from app.utils import hash_password, verify_password

class AuthService:
    def __init__(self):
        self.secret = config['jwt']['secret']
        self.algorithm = config['jwt']['algorithm']
        self.access_token_expiry = config['jwt']['access_token_expiry']
        self.refresh_token_expiry = config['jwt']['refresh_token_expiry']

    def register(self, email: str, password: str, name: str) -> Dict[str, Any]:
        # Check if user exists
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already registered")

        # Create user
        user = User(
            email=email,
            password_hash=hash_password(password),
            name=name
        )
        user.save()

        # Send verification email
        self.send_verification_email(user)

        # Generate tokens
        tokens = self.generate_tokens(user)

        return {
            'user': user.to_dict(),
            'tokens': tokens
        }

    def login(self, email: str, password: str) -> Dict[str, Any]:
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            raise ValueError("Invalid credentials")

        # Verify password
        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        # Check 2FA
        if user.two_factor_enabled:
            return {
                'requires_2fa': True,
                'user_id': user.id
            }

        # Generate tokens
        tokens = self.generate_tokens(user)

        return {
            'user': user.to_dict(),
            'tokens': tokens
        }

    def verify_2fa(self, user_id: int, code: str) -> Dict[str, Any]:
        # Find user
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        # Verify 2FA code
        if not self.verify_2fa_code(user, code):
            raise ValueError("Invalid 2FA code")

        # Generate tokens
        tokens = self.generate_tokens(user)

        return {
            'user': user.to_dict(),
            'tokens': tokens
        }

    def refresh_token(self, refresh_token: str) -> Dict[str, str]:
        try:
            # Decode token
            payload = jwt.decode(
                refresh_token,
                self.secret,
                algorithms=[self.algorithm]
            )

            # Find user
            user = User.query.get(payload['sub'])
            if not user:
                raise ValueError("User not found")

            # Generate new tokens
            tokens = self.generate_tokens(user)

            return tokens

        except jwt.InvalidTokenError:
            raise ValueError("Invalid refresh token")

    def generate_tokens(self, user: User) -> Dict[str, str]:
        # Generate access token
        access_token = jwt.encode(
            {
                'sub': user.id,
                'exp': datetime.utcnow() + timedelta(seconds=self.access_token_expiry),
                'type': 'access'
            },
            self.secret,
            algorithm=self.algorithm
        )

        # Generate refresh token
        refresh_token = jwt.encode(
            {
                'sub': user.id,
                'exp': datetime.utcnow() + timedelta(seconds=self.refresh_token_expiry),
                'type': 'refresh'
            },
            self.secret,
            algorithm=self.algorithm
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=[self.algorithm]
            )

            # Find user
            user = User.query.get(payload['sub'])
            if not user:
                raise ValueError("User not found")

            return {
                'user': user.to_dict(),
                'payload': payload
            }

        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
```

### 3. Authentication Middleware

```python
from functools import wraps
from flask import request, g
from app.services import AuthService
from app.exceptions import UnauthorizedError

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise UnauthorizedError("No token provided")

        token = auth_header.split(' ')[1]

        # Verify token
        auth_service = AuthService()
        try:
            result = auth_service.verify_token(token)
            g.user = result['user']
            g.token_payload = result['payload']
        except ValueError as e:
            raise UnauthorizedError(str(e))

        return f(*args, **kwargs)

    return decorated

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check if user has required role
            if not g.user or g.user.role not in roles:
                raise UnauthorizedError("Insufficient permissions")

            return f(*args, **kwargs)

        return decorated

    return decorator
```

### 4. Authentication Routes

```python
from flask import Blueprint, request, jsonify
from app.services import AuthService
from app.exceptions import ValidationError

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        result = auth_service.register(
            email=data['email'],
            password=data['password'],
            name=data.get('name')
        )
        return jsonify(result), 201
    except ValueError as e:
        raise ValidationError(str(e))

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        result = auth_service.login(
            email=data['email'],
            password=data['password']
        )
        return jsonify(result)
    except ValueError as e:
        raise ValidationError(str(e))

@auth_bp.route('/verify-2fa', methods=['POST'])
def verify_2fa():
    try:
        data = request.get_json()
        result = auth_service.verify_2fa(
            user_id=data['user_id'],
            code=data['code']
        )
        return jsonify(result)
    except ValueError as e:
        raise ValidationError(str(e))

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    try:
        data = request.get_json()
        result = auth_service.refresh_token(data['refresh_token'])
        return jsonify(result)
    except ValueError as e:
        raise ValidationError(str(e))

@auth_bp.route('/logout', methods=['POST'])
@auth_required
def logout():
    # Invalidate token (optional)
    return jsonify({'message': 'Successfully logged out'})
```

## Security Best Practices

1. **Password Security**:
   - Use strong hashing (bcrypt)
   - Enforce password policies
   - Implement password reset
   - Monitor failed attempts

2. **Token Security**:
   - Use short-lived access tokens
   - Use secure refresh tokens
   - Implement token revocation
   - Use secure storage

3. **Session Security**:
   - Implement session timeout
   - Track active sessions
   - Allow session revocation
   - Monitor suspicious activity

4. **2FA Security**:
   - Use TOTP for 2FA
   - Allow backup codes
   - Implement recovery process
   - Monitor 2FA changes

## Configuration

### 1. JWT Settings

```python
# config/auth.py
JWT = {
    'secret': 'your-secret-key',
    'algorithm': 'HS256',
    'access_token_expiry': 3600,  # 1 hour
    'refresh_token_expiry': 604800,  # 1 week
}
```

### 2. Password Settings

```python
# config/auth.py
PASSWORD = {
    'min_length': 8,
    'require_uppercase': True,
    'require_lowercase': True,
    'require_numbers': True,
    'require_special': True,
    'max_attempts': 5,
    'lockout_duration': 1800,  # 30 minutes
}
```

### 3. Session Settings

```python
# config/auth.py
SESSION = {
    'timeout': 3600,  # 1 hour
    'max_sessions': 5,
    'inactivity_timeout': 1800,  # 30 minutes
}
```

## Troubleshooting

1. **Authentication Issues**:
   - Check token expiration
   - Verify token signature
   - Check user status
   - Review session logs

2. **2FA Issues**:
   - Verify time synchronization
   - Check backup codes
   - Review 2FA logs
   - Reset 2FA if needed

3. **Session Issues**:
   - Check session timeout
   - Verify session storage
   - Review session logs
   - Clear expired sessions

## Additional Resources

- [JWT Documentation](https://jwt.io/)
- [OAuth 2.0](https://oauth.net/2/)
- [2FA Best Practices](https://www.nist.gov/publications/digital-identity-guidelines)
- [Security Best Practices](https://owasp.org/www-project-top-ten/)
