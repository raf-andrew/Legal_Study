from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import jwt
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.status import HTTP_403_FORBIDDEN

from app.core.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token handling
security = HTTPBearer()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(subject: Union[str, int]) -> str:
    """
    Create a new refresh token.

    Args:
        subject: Token subject (usually user ID)

    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt

def verify_token(token: str) -> Dict[str, Any]:
    """Verify a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise JWTError("Invalid token")

def get_token_payload(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    Get payload from token in authorization header.

    Args:
        credentials: Authorization credentials

    Returns:
        Token payload
    """
    return verify_token(credentials.credentials)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def validate_token(token: str, token_type: str = "access") -> bool:
    """
    Validate a token.

    Args:
        token: Token to validate
        token_type: Expected token type

    Returns:
        True if token is valid

    Raises:
        HTTPException: If token is invalid
    """
    payload = verify_token(token)

    if payload["type"] != token_type:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f"Invalid token type. Expected {token_type}"
        )

    return True

def generate_token_pair(user_id: str) -> Dict[str, str]:
    """Generate access and refresh tokens."""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        data={"sub": user_id, "type": "access"},
        expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
