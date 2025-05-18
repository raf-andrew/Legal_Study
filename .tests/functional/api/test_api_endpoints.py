"""
API endpoint functional tests.
"""
import os
import json
import pytest
import requests
from datetime import datetime
from typing import Dict, List

# Test configuration
API_URL = os.getenv('API_URL', 'http://localhost:8000')
TEST_USER = {
    'username': 'testuser',
    'password': 'testpass123',
    'email': 'test@example.com'
}

class TestAPIEndpoints:
    """Test suite for API endpoints."""

    @pytest.fixture(scope='class')
    def auth_token(self) -> str:
        """Get authentication token."""
        response = requests.post(
            f"{API_URL}/api/v1/auth/login",
            json={
                'username': TEST_USER['username'],
                'password': TEST_USER['password']
            }
        )
        assert response.status_code == 200
        return response.json()['access_token']

    @pytest.fixture(scope='class')
    def headers(self, auth_token: str) -> Dict[str, str]:
        """Get request headers with auth token."""
        return {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }

    def test_health_check(self):
        """Test health check endpoint."""
        response = requests.get(f"{API_URL}/health")
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'

    def test_api_version(self):
        """Test API version endpoint."""
        response = requests.get(f"{API_URL}/api/v1/version")
        assert response.status_code == 200
        assert 'version' in response.json()

    def test_authentication(self, headers: Dict[str, str]):
        """Test authentication."""
        # Test protected endpoint
        response = requests.get(
            f"{API_URL}/api/v1/protected",
            headers=headers
        )
        assert response.status_code == 200

    def test_rate_limiting(self):
        """Test rate limiting."""
        # Make multiple requests in quick succession
        responses = []
        for _ in range(10):
            response = requests.get(f"{API_URL}/api/v1/public")
            responses.append(response)

        # Check if rate limiting is enforced
        assert any(r.status_code == 429 for r in responses)

    def test_error_handling(self):
        """Test error handling."""
        # Test invalid endpoint
        response = requests.get(f"{API_URL}/api/v1/invalid")
        assert response.status_code == 404

        # Test invalid request
        response = requests.post(
            f"{API_URL}/api/v1/auth/login",
            json={'invalid': 'data'}
        )
        assert response.status_code == 422

    def test_response_validation(self, headers: Dict[str, str]):
        """Test response validation."""
        # Test response structure
        response = requests.get(
            f"{API_URL}/api/v1/monitoring/health",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data

    def test_security_headers(self):
        """Test security headers."""
        response = requests.get(f"{API_URL}/health")
        headers = response.headers

        # Check security headers
        assert 'X-Content-Type-Options' in headers
        assert 'X-Frame-Options' in headers
        assert 'X-XSS-Protection' in headers
        assert 'Strict-Transport-Security' in headers

    def test_cors_headers(self):
        """Test CORS headers."""
        response = requests.options(
            f"{API_URL}/health",
            headers={'Origin': 'http://localhost:3000'}
        )
        headers = response.headers

        # Check CORS headers
        assert 'Access-Control-Allow-Origin' in headers
        assert 'Access-Control-Allow-Methods' in headers
        assert 'Access-Control-Allow-Headers' in headers

    def test_performance(self, headers: Dict[str, str]):
        """Test API performance."""
        import time

        # Measure response time
        start_time = time.time()
        response = requests.get(
            f"{API_URL}/api/v1/monitoring/health",
            headers=headers
        )
        end_time = time.time()

        assert response.status_code == 200
        assert end_time - start_time < 1.0  # Response within 1 second

    def test_monitoring_endpoints(self, headers: Dict[str, str]):
        """Test monitoring endpoints."""
        # Test system metrics
        response = requests.get(
            f"{API_URL}/api/v1/monitoring/system",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert 'metrics' in data
        assert 'cpu_usage' in data['metrics']
        assert 'memory_usage' in data['metrics']

        # Test application metrics
        response = requests.get(
            f"{API_URL}/api/v1/monitoring/application",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert 'metrics' in data
        assert 'requests_per_second' in data['metrics']
        assert 'average_response_time' in data['metrics']

    def test_error_logging(self, headers: Dict[str, str]):
        """Test error logging."""
        # Test error logging endpoint
        error_data = {
            'level': 'error',
            'message': 'Test error message',
            'context': {
                'service': 'test_service',
                'action': 'test_action'
            }
        }
        response = requests.post(
            f"{API_URL}/api/v1/error-handling/log",
            headers=headers,
            json=error_data
        )
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'error_id' in data
        assert 'logged_at' in data
