import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.middleware.auth import AuthMiddleware
import jwt
import time
from datetime import datetime, timedelta

# Initialize middleware
auth_middleware = AuthMiddleware(app)
app.middleware("http")(auth_middleware)

client = TestClient(app)

@pytest.mark.security
def test_authentication_required():
    """Test that authentication is required for protected endpoints."""
    response = client.get("/api/v1/protected")
    assert response.status_code == 401
    assert "detail" in response.json()

@pytest.mark.security
def test_jwt_token_validation():
    """Test JWT token validation."""
    # Create a valid token
    token = jwt.encode(
        {"sub": "test_user", "exp": datetime.utcnow() + timedelta(minutes=30)},
        "test_secret_key",
        algorithm="HS256"
    )

    # Test with valid token
    response = client.get(
        "/api/v1/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Test with expired token
    expired_token = jwt.encode(
        {"sub": "test_user", "exp": datetime.utcnow() - timedelta(minutes=30)},
        "test_secret_key",
        algorithm="HS256"
    )
    response = client.get(
        "/api/v1/protected",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401

    # Test with invalid token
    response = client.get(
        "/api/v1/protected",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

@pytest.mark.security
def test_rate_limiting():
    """Test rate limiting functionality."""
    # Make multiple requests in quick succession
    for _ in range(10):
        response = client.get("/api/v1/public")
        assert response.status_code == 200

    # Should be rate limited after threshold
    response = client.get("/api/v1/public")
    assert response.status_code == 429

@pytest.mark.security
def test_cors_headers():
    """Test CORS headers configuration."""
    response = client.get("/api/v1/public")
    assert "access-control-allow-origin" in response.headers
    assert "access-control-allow-methods" in response.headers
    assert "access-control-allow-headers" in response.headers

@pytest.mark.security
def test_security_headers():
    """Test security headers configuration."""
    response = client.get("/api/v1/public")
    headers = response.headers

    # Check for security headers
    assert "x-frame-options" in headers
    assert "x-content-type-options" in headers
    assert "x-xss-protection" in headers
    assert "strict-transport-security" in headers
    assert "content-security-policy" in headers

@pytest.mark.security
def test_input_validation():
    """Test input validation and sanitization."""
    # Test SQL injection attempt
    response = client.get("/api/v1/search?query=' OR '1'='1")
    assert response.status_code == 400

    # Test XSS attempt
    response = client.get("/api/v1/search?query=<script>alert('xss')</script>")
    assert response.status_code == 400

    # Test path traversal attempt
    response = client.get("/api/v1/files/../../etc/passwd")
    assert response.status_code == 400

@pytest.mark.security
def test_session_management():
    """Test session management and timeout."""
    # Login and get session token
    response = client.post(
        "/api/v1/login",
        json={"username": "test_user", "password": "test_password"}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Use token immediately
    response = client.get(
        "/api/v1/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Wait for session timeout
    time.sleep(31)  # Assuming 30-minute session timeout

    # Try to use expired token
    response = client.get(
        "/api/v1/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
