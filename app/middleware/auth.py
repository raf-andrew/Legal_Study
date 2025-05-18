"""Authentication middleware."""

from fastapi import Request, HTTPException, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.core.config import settings
from datetime import datetime, timedelta
from typing import Optional, Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.security import verify_token

security = HTTPBearer()

def create_access_token(data: Dict[str, str], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_token(token: str) -> Dict[str, str]:
    """Verify JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = None) -> Dict[str, str]:
    """Get current user from token."""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    return verify_token(token)

class AuthMiddleware:
    def __init__(self, app):
        self.app = app
        self.security = HTTPBearer()
        self.rate_limit = {}
        self.rate_limit_window = 60  # 1 minute window
        self.max_requests = 100  # Maximum requests per window

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive=receive)
        path = scope.get("path", "")
        # Skip auth for public endpoints
        if path in ["/api/v1/public", "/api/v1/health", "/", "/docs", "/openapi.json"]:
            await self.app(scope, receive, send)
            return
        try:
            # Rate limiting
            client_ip = scope.get("client")[0] if scope.get("client") else "unknown"
            current_time = datetime.now()
            if client_ip in self.rate_limit:
                window_start, count = self.rate_limit[client_ip]
                if (current_time - window_start).total_seconds() > self.rate_limit_window:
                    self.rate_limit[client_ip] = (current_time, 1)
                elif count >= self.max_requests:
                    response = JSONResponse(status_code=429, content={"detail": "Too many requests"})
                    await response(scope, receive, send)
                    return
                else:
                    self.rate_limit[client_ip] = (window_start, count + 1)
            else:
                self.rate_limit[client_ip] = (current_time, 1)
            # Auth
            auth = await self.security(request)
            if not auth:
                response = JSONResponse(status_code=401, content={"detail": "Not authenticated"}, headers={"WWW-Authenticate": "Bearer"})
                await response(scope, receive, send)
                return
            try:
                payload = verify_token(auth.credentials)
                # request.state.user = payload  # Not available in ASGI middleware
            except JWTError:
                response = JSONResponse(status_code=401, content={"detail": "Invalid token"}, headers={"WWW-Authenticate": "Bearer"})
                await response(scope, receive, send)
                return
            # Call downstream app and add security headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    headers[b"x-content-type-options"] = b"nosniff"
                    headers[b"x-frame-options"] = b"DENY"
                    headers[b"x-xss-protection"] = b"1; mode=block"
                    headers[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains"
                    message["headers"] = list(headers.items())
                await send(message)
            await self.app(scope, receive, send_wrapper)
        except HTTPException as e:
            response = JSONResponse(status_code=e.status_code, content={"detail": e.detail}, headers=e.headers)
            await response(scope, receive, send)
        except Exception:
            response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
            await response(scope, receive, send)
