import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
import json
from datetime import datetime

client = TestClient(app)

def test_environment_setup():
    """Verify environment configuration is loaded correctly"""
    assert os.getenv('APP_ENV') == 'development'
    assert os.getenv('DEBUG') == 'True'
    assert os.getenv('TESTING') == 'True'

def test_api_health_check():
    """Verify API health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_api_version():
    """Verify API version endpoint"""
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json()["version"] == os.getenv("API_VERSION", "v1")

def test_error_handling():
    """Verify error handling endpoint"""
    response = client.get("/api/v1/error")
    assert response.status_code == 500
    assert "detail" in response.json()

def test_database_connection():
    """Verify database connectivity"""
    # This test will be implemented based on the database configuration
    pass

def test_authentication_flow():
    """Verify basic authentication flow"""
    # This test will be implemented based on the authentication setup
    pass

def test_cors_configuration():
    """Verify CORS configuration"""
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers

def test_rate_limiting():
    """Verify rate limiting configuration"""
    # Make multiple requests to test rate limiting
    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200
    
    # This should trigger rate limiting
    response = client.get("/health")
    assert response.status_code == 429

def test_security_headers():
    """Verify security headers are properly set"""
    response = client.get("/health")
    assert "x-frame-options" in response.headers
    assert "x-content-type-options" in response.headers
    assert "x-xss-protection" in response.headers
    assert "content-security-policy" in response.headers

def test_logging_configuration():
    """Verify logging is properly configured"""
    # Check if log directory exists
    assert os.path.exists(".logs")
    assert os.path.exists(".errors")
    
    # Check if log files are created
    assert os.path.exists(".logs/app.log")
    assert os.path.exists(".errors/error.log") 