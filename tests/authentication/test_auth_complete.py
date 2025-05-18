import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import jwt
from typing import Dict, Any
import json
import os

# Test data
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "password_confirmation": "TestPass123!"
}

def test_user_registration(client: TestClient, db: Session):
    """Test user registration functionality"""
    response = client.post(
        "/api/v1/auth/register",
        json=TEST_USER
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["username"] == TEST_USER["username"]
    assert data["email"] == TEST_USER["email"]
    assert "password" not in data

def test_user_login(client: TestClient, db: Session):
    """Test user login functionality"""
    # First register the user
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Test login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"

def test_password_reset(client: TestClient, db: Session):
    """Test password reset functionality"""
    # Register user
    client.post("/api/v1/auth/register", json=TEST_USER)
    
    # Request password reset
    response = client.post(
        "/api/v1/auth/password-reset-request",
        json={"email": TEST_USER["email"]}
    )
    assert response.status_code == 200
    
    # Get reset token from email (simulated)
    reset_token = "test_reset_token"
    
    # Reset password
    new_password = "NewPass123!"
    response = client.post(
        "/api/v1/auth/password-reset",
        json={
            "token": reset_token,
            "new_password": new_password,
            "new_password_confirmation": new_password
        }
    )
    assert response.status_code == 200
    
    # Verify new password works
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": TEST_USER["username"],
            "password": new_password
        }
    )
    assert response.status_code == 200

def test_token_refresh(client: TestClient, db: Session):
    """Test token refresh functionality"""
    # Register and login
    client.post("/api/v1/auth/register", json=TEST_USER)
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    refresh_token = login_response.json()["refresh_token"]
    
    # Refresh token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

def test_session_management(client: TestClient, db: Session):
    """Test session management functionality"""
    # Register and login
    client.post("/api/v1/auth/register", json=TEST_USER)
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        }
    )
    access_token = login_response.json()["access_token"]
    
    # Test session validation
    response = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    
    # Test session termination
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    
    # Verify session is terminated
    response = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401

def test_security_measures(client: TestClient, db: Session):
    """Test security measures"""
    # Test rate limiting
    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "wrong",
                "password": "wrong"
            }
        )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "wrong",
            "password": "wrong"
        }
    )
    assert response.status_code == 429
    
    # Test password complexity
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "weak",
            "password_confirmation": "weak"
        }
    )
    assert response.status_code == 400
    
    # Test token expiration
    expired_token = jwt.encode(
        {
            "sub": TEST_USER["username"],
            "exp": datetime.utcnow() - timedelta(minutes=1)
        },
        "secret",
        algorithm="HS256"
    )
    response = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401

def test_error_handling(client: TestClient, db: Session):
    """Test error handling"""
    # Test invalid credentials
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "wrong",
            "password": "wrong"
        }
    )
    assert response.status_code == 401
    
    # Test invalid token
    response = client.get(
        "/api/v1/auth/session",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    
    # Test missing token
    response = client.get("/api/v1/auth/session")
    assert response.status_code == 401
    
    # Test duplicate registration
    client.post("/api/v1/auth/register", json=TEST_USER)
    response = client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 400

def test_documentation(client: TestClient):
    """Test API documentation"""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert "components" in spec
    assert "securitySchemes" in spec["components"]
    assert "BearerAuth" in spec["components"]["securitySchemes"] 