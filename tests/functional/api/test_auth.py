import pytest
import requests
from datetime import datetime, timedelta
import jwt
import os

# Test configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
TEST_USER = {
    'username': 'test_user',
    'password': 'test_password',
    'email': 'test@example.com'
}

@pytest.fixture(scope='module')
def auth_token():
    """Fixture to get authentication token for tests."""
    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={
            'username': TEST_USER['username'],
            'password': TEST_USER['password']
        }
    )
    assert response.status_code == 200
    return response.json()['token']

@pytest.fixture(scope='module')
def invalid_token():
    """Fixture to get an invalid token for negative testing."""
    return "invalid_token"

class TestAuthentication:
    """Test suite for API authentication."""

    def test_login_success(self):
        """Test successful login with valid credentials."""
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={
                'username': TEST_USER['username'],
                'password': TEST_USER['password']
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert 'token' in data
        assert isinstance(data['token'], str)

        # Verify token structure
        token = data['token']
        decoded = jwt.decode(token, options={"verify_signature": False})
        assert 'sub' in decoded
        assert 'exp' in decoded
        assert 'iat' in decoded

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={
                'username': TEST_USER['username'],
                'password': 'wrong_password'
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'Invalid credentials'

    def test_protected_endpoint_with_valid_token(self, auth_token):
        """Test accessing protected endpoint with valid token."""
        response = requests.get(
            f"{API_BASE_URL}/api/protected",
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert data['message'] == 'Access granted'

    def test_protected_endpoint_with_invalid_token(self, invalid_token):
        """Test accessing protected endpoint with invalid token."""
        response = requests.get(
            f"{API_BASE_URL}/api/protected",
            headers={'Authorization': f'Bearer {invalid_token}'}
        )

        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'Invalid token'

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token."""
        response = requests.get(f"{API_BASE_URL}/api/protected")

        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'Missing token'

    def test_token_expiration(self):
        """Test token expiration handling."""
        # Create an expired token
        expired_token = jwt.encode(
            {
                'sub': TEST_USER['username'],
                'exp': datetime.utcnow() - timedelta(hours=1),
                'iat': datetime.utcnow() - timedelta(hours=2)
            },
            'secret',
            algorithm='HS256'
        )

        response = requests.get(
            f"{API_BASE_URL}/api/protected",
            headers={'Authorization': f'Bearer {expired_token}'}
        )

        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'Token expired'

    def test_token_refresh(self, auth_token):
        """Test token refresh functionality."""
        response = requests.post(
            f"{API_BASE_URL}/auth/refresh",
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = response.json()
        assert 'token' in data
        assert isinstance(data['token'], str)
        assert data['token'] != auth_token

    def test_logout(self, auth_token):
        """Test logout functionality."""
        response = requests.post(
            f"{API_BASE_URL}/auth/logout",
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert data['message'] == 'Successfully logged out'

        # Verify token is invalidated
        response = requests.get(
            f"{API_BASE_URL}/api/protected",
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 401
        data = response.json()
        assert 'error' in data
        assert data['error'] == 'Token invalidated'
