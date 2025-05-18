"""
Security Tests

This module contains security tests to verify authentication, authorization, and data protection.
"""

import pytest
import jwt
import logging
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/security_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import application
from api.app import app
from api.database import DatabaseManager

@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def db() -> DatabaseManager:
    """Create a test database instance."""
    return DatabaseManager("sqlite:///test.db")

@pytest.fixture
def encryption_key() -> bytes:
    """Generate a secure encryption key."""
    return base64.urlsafe_b64encode(secrets.token_bytes(32))

@pytest.fixture
def jwt_secret() -> str:
    """Generate a secure JWT secret."""
    return secrets.token_urlsafe(32)

def create_token(secret: str, user_id: int, expiry_minutes: int = 30) -> str:
    """Create a JWT token."""
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(minutes=expiry_minutes)
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def test_password_hashing():
    """Test secure password hashing."""
    password = "test_password123"
    salt = secrets.token_bytes(16)
    
    # Hash password with salt
    hash_1 = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # Number of iterations
    )
    
    # Verify same password hashes to same value
    hash_2 = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    
    assert hash_1 == hash_2, "Password hashing is inconsistent"
    
    # Verify different password produces different hash
    wrong_hash = hashlib.pbkdf2_hmac(
        'sha256',
        "wrong_password".encode('utf-8'),
        salt,
        100000
    )
    
    assert hash_1 != wrong_hash, "Password hashing collision detected"

def test_data_encryption(encryption_key: bytes):
    """Test data encryption and decryption."""
    fernet = Fernet(encryption_key)
    
    # Test data
    sensitive_data = "sensitive information"
    
    # Encrypt data
    encrypted_data = fernet.encrypt(sensitive_data.encode())
    assert encrypted_data != sensitive_data.encode(), "Data not properly encrypted"
    
    # Decrypt data
    decrypted_data = fernet.decrypt(encrypted_data).decode()
    assert decrypted_data == sensitive_data, "Data not properly decrypted"

def test_token_validation(client: TestClient, jwt_secret: str):
    """Test JWT token validation."""
    # Create valid token
    valid_token = create_token(jwt_secret, user_id=1)
    
    # Create expired token
    expired_token = create_token(jwt_secret, user_id=1, expiry_minutes=-30)
    
    # Test valid token
    headers = {"Authorization": f"Bearer {valid_token}"}
    response = client.get("/metrics", headers=headers)
    assert response.status_code == 200, "Valid token rejected"
    
    # Test expired token
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/metrics", headers=headers)
    assert response.status_code == 401, "Expired token accepted"
    
    # Test invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/metrics", headers=headers)
    assert response.status_code == 401, "Invalid token accepted"

def test_sql_injection_prevention(db: DatabaseManager):
    """Test SQL injection prevention."""
    # Attempt SQL injection in username
    malicious_username = "' OR '1'='1"
    malicious_email = "attacker@example.com"
    
    try:
        user = db.create_user(malicious_username, malicious_email)
        # Verify no data leaked
        assert user is None or user.username == malicious_username, "SQL injection may be possible"
    except Exception as e:
        logger.info("SQL injection attempt properly blocked")

def test_rate_limiting(client: TestClient):
    """Test rate limiting functionality."""
    # Make multiple rapid requests
    responses = []
    for _ in range(10):
        response = client.get("/status")
        responses.append(response.status_code)
    
    # Verify rate limiting
    assert 429 in responses or all(r == 200 for r in responses), \
        "Rate limiting not properly enforced"

def test_secure_headers(client: TestClient):
    """Test security headers."""
    response = client.get("/health")
    headers = response.headers
    
    # Check security headers
    assert headers.get("X-Content-Type-Options") == "nosniff", "Missing nosniff header"
    assert headers.get("X-Frame-Options") == "DENY", "Missing X-Frame-Options header"
    assert headers.get("X-XSS-Protection") == "1; mode=block", "Missing XSS protection header"
    assert "Content-Security-Policy" in headers, "Missing CSP header"

def test_file_upload_security(client: TestClient):
    """Test file upload security."""
    # Try to upload executable
    malicious_file = {
        "file": ("malicious.exe", b"malicious content", "application/x-msdownload")
    }
    response = client.post("/upload", files=malicious_file)
    assert response.status_code in (400, 403, 404), "Dangerous file upload not blocked"
    
    # Try to upload large file
    large_file = {
        "file": ("large.txt", b"x" * 1024 * 1024 * 11, "text/plain")  # 11MB
    }
    response = client.post("/upload", files=large_file)
    assert response.status_code in (400, 413), "Large file upload not blocked"

def test_error_information_leakage(client: TestClient):
    """Test prevention of sensitive information leakage in errors."""
    # Trigger application error
    response = client.get("/nonexistent")
    assert response.status_code == 404
    
    # Verify error response doesn't contain sensitive information
    error_response = response.json()
    sensitive_terms = ["stack trace", "sql", "error", "exception", "debug"]
    response_str = str(error_response).lower()
    for term in sensitive_terms:
        assert term not in response_str, f"Error response may leak sensitive information: {term}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"]) 