"""
Legal Study API

This module provides the main FastAPI application with security features and health check endpoints.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request, Response, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import psutil
import jwt
from datetime import datetime, timedelta
import os
from typing import Dict, Any, Optional, List
import yaml
from pathlib import Path
import secrets
import hashlib
import base64
from cryptography.fernet import Fernet
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import UploadFile as StarletteUploadFile

# Load configuration
config_path = Path('.config/environment/env.dev')
with open(config_path, 'r') as f:
    config = {line.split('=')[0]: line.split('=')[1].strip() 
              for line in f.readlines() 
              if line.strip() and not line.startswith('#')}

# Initialize encryption
ENCRYPTION_KEY = base64.urlsafe_b64encode(config['ENCRYPTION_KEY'].encode())
fernet = Fernet(ENCRYPTION_KEY)

# Initialize FastAPI app
app = FastAPI(
    title="Legal Study API",
    description="API for legal study application",
    version="1.0.0",
    docs_url="/api/docs" if config['DOCS_ENABLED'].lower() == 'true' else None
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=config['ALLOWED_HOSTS'].split(',')
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config['CORS_ORIGINS'].split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Rate limiting
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        now = time.time()

        # Clean old requests
        self.requests = {
            ip: reqs for ip, reqs in self.requests.items()
            if now - reqs["timestamp"] < self.window_seconds
        }

        # Check rate limit
        if client_ip in self.requests:
            if self.requests[client_ip]["count"] >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests"}
                )
            self.requests[client_ip]["count"] += 1
        else:
            self.requests[client_ip] = {"count": 1, "timestamp": now}

        response = await call_next(request)
        return response

app.add_middleware(
    RateLimitMiddleware,
    max_requests=int(config['RATE_LIMIT_REQUESTS']),
    window_seconds=int(config['RATE_LIMIT_PERIOD'])
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    if config['HSTS_ENABLED'].lower() == 'true':
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Models
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: str

class MetricsResponse(BaseModel):
    """Metrics response model."""
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    timestamp: str

class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str

# Security
security = HTTPBearer(auto_error=True)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify JWT token."""
    try:
        jwt.decode(
            credentials.credentials,
            config['JWT_SECRET'],
            algorithms=["HS256"]
        )
        return True
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

def get_system_metrics() -> Dict[str, Any]:
    """Get system metrics."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": {
            "total": psutil.disk_usage('/').total / (1024 * 1024 * 1024),  # GB
            "used": psutil.disk_usage('/').used / (1024 * 1024 * 1024),    # GB
            "free": psutil.disk_usage('/').free / (1024 * 1024 * 1024)     # GB
        }
    }

# File upload settings
UPLOAD_DIR = Path(".uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_SIZE = int(config['MAX_FILE_SIZE']) * 1024 * 1024  # Convert MB to bytes
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.doc', '.docx', '.md'}

def validate_file(file: UploadFile) -> bool:
    """Validate file upload."""
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Reset position
    
    if size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large"
        )
    
    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed"
        )
    
    return True

# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )

@app.get("/status")
async def status_check() -> Dict[str, str]:
    """Status check endpoint."""
    return {
        "status": "ok",
        "environment": config['ENVIRONMENT'],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics(authorized: bool = Depends(verify_token)) -> MetricsResponse:
    """Get system metrics (requires authentication)."""
    metrics = get_system_metrics()
    return MetricsResponse(
        cpu_percent=metrics["cpu_percent"],
        memory_percent=metrics["memory_percent"],
        disk_usage=metrics["disk_usage"],
        timestamp=datetime.now().isoformat()
    )

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload with security checks."""
    try:
        validate_file(file)
        
        # Generate secure filename
        ext = Path(file.filename).suffix.lower()
        secure_filename = f"{secrets.token_hex(16)}{ext}"
        file_path = UPLOAD_DIR / secure_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        return {"filename": secure_filename}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing file"
        )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler to prevent information leakage."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Generic exception handler to prevent information leakage."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile=config.get('SSL_KEY_FILE'),
        ssl_certfile=config.get('SSL_CERT_FILE')
    ) 