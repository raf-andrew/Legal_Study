import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import User
from app.main import app

client = TestClient(app)

def test_register_user(db: Session):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "password_confirm": "testpassword123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    
    # Verify user in database
    user = db.query(User).filter(User.username == "testuser").first()
    assert user is not None
    assert user.email == "test@example.com"
    assert verify_password("testpassword123", user.password_hash)
    assert user.is_active
    assert not user.is_admin

def test_register_duplicate_username(db: Session):
    """Test registration with duplicate username."""
    # Create first user
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "duplicate",
            "email": "first@example.com",
            "password": "testpassword123",
            "password_confirm": "testpassword123"
        }
    )
    assert response.status_code == 200
    
    # Try to create second user with same username
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "duplicate",
            "email": "second@example.com",
            "password": "testpassword123",
            "password_confirm": "testpassword123"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_register_duplicate_email(db: Session):
    """Test registration with duplicate email."""
    # Create first user
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "firstuser",
            "email": "duplicate@example.com",
            "password": "testpassword123",
            "password_confirm": "testpassword123"
        }
    )
    assert response.status_code == 200
    
    # Try to create second user with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "seconduser",
            "email": "duplicate@example.com",
            "password": "testpassword123",
            "password_confirm": "testpassword123"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

def test_register_invalid_password_confirmation(db: Session):
    """Test registration with mismatched passwords."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "password_confirm": "wrongpassword123"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Passwords do not match"

def test_register_invalid_email(db: Session):
    """Test registration with invalid email."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "invalid-email",
            "password": "testpassword123",
            "password_confirm": "testpassword123"
        }
    )
    assert response.status_code == 422  # Validation error

def test_register_short_username(db: Session):
    """Test registration with too short username."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "te",  # Too short
            "email": "test@example.com",
            "password": "testpassword123",
            "password_confirm": "testpassword123"
        }
    )
    assert response.status_code == 422  # Validation error

def test_register_short_password(db: Session):
    """Test registration with too short password."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "short",  # Too short
            "password_confirm": "short"
        }
    )
    assert response.status_code == 422  # Validation error 