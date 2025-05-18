"""
Smoke Tests

This module contains smoke tests for basic API functionality.
"""

import pytest
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, Generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/smoke_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import the FastAPI application
import sys
import os
sys.path.append(os.path.abspath("."))
from api.app import app

@pytest.fixture
def client() -> Generator:
    """Create a test client."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def auth_token() -> str:
    """Create a valid JWT token."""
    # Load configuration
    config_path = Path('.config/environment/env.dev')
    with open(config_path, 'r') as f:
        config = {line.split('=')[0]: line.split('=')[1].strip() 
                 for line in f.readlines() 
                 if line.strip() and not line.startswith('#')}
    
    # Create token
    token = jwt.encode(
        {
            "sub": "test_user",
            "exp": datetime.utcnow() + timedelta(minutes=30)
        },
        config['JWT_SECRET'],
        algorithm="HS256"
    )
    return token

def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    try:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data
        logger.info("Health check test passed")
    except Exception as e:
        logger.error(f"Health check test failed: {e}")
        raise

def test_status_check(client: TestClient) -> None:
    """Test status check endpoint."""
    try:
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "environment" in data
        assert "timestamp" in data
        logger.info("Status check test passed")
    except Exception as e:
        logger.error(f"Status check test failed: {e}")
        raise

def test_metrics_unauthorized(client: TestClient) -> None:
    """Test metrics endpoint without authentication."""
    try:
        response = client.get("/metrics")
        assert response.status_code == 401
        logger.info("Unauthorized metrics test passed")
    except Exception as e:
        logger.error(f"Unauthorized metrics test failed: {e}")
        raise

def test_metrics_authorized(client: TestClient, auth_token: str) -> None:
    """Test metrics endpoint with authentication."""
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get("/metrics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "cpu_percent" in data
        assert "memory_percent" in data
        assert "disk_usage" in data
        assert "timestamp" in data
        logger.info("Authorized metrics test passed")
    except Exception as e:
        logger.error(f"Authorized metrics test failed: {e}")
        raise

def test_invalid_token(client: TestClient) -> None:
    """Test metrics endpoint with invalid token."""
    try:
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/metrics", headers=headers)
        assert response.status_code == 401
        logger.info("Invalid token test passed")
    except Exception as e:
        logger.error(f"Invalid token test failed: {e}")
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 