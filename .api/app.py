"""
Legal Study API

This module provides the main FastAPI application with basic health check endpoints.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import psutil
import jwt
from datetime import datetime, timedelta
import os
from typing import Dict, Any
import yaml
from pathlib import Path

# Load configuration
config_path = Path('.config/environment/env.dev')
with open(config_path, 'r') as f:
    config = {line.split('=')[0]: line.split('=')[1].strip() 
              for line in f.readlines() 
              if line.strip() and not line.startswith('#')}

app = FastAPI(
    title="Legal Study API",
    description="API for legal study application",
    version="1.0.0"
)

security = HTTPBearer()

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

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify JWT token."""
    try:
        jwt.decode(
            credentials.credentials,
            config['JWT_SECRET'],
            algorithms=["HS256"]
        )
        return True
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 