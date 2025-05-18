"""
Smoke tests for platform health checks.
These tests verify basic functionality of core platform components.
"""

import os
import pytest
import requests
from datetime import datetime
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 5  # seconds

def test_api_health():
    """Test API health endpoint."""
    response = requests.get(f"{API_BASE_URL}/health", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data

def test_database_connection():
    """Test database connection."""
    response = requests.get(f"{API_BASE_URL}/api/v1/health/database", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "connection_time" in data

def test_redis_connection():
    """Test Redis connection."""
    response = requests.get(f"{API_BASE_URL}/api/v1/health/redis", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "connection_time" in data

def test_ai_service():
    """Test AI service functionality."""
    # Test health endpoint
    response = requests.get(f"{API_BASE_URL}/api/v1/ai/health", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    
    # Test basic AI functionality
    test_prompt = "Test prompt for smoke testing"
    response = requests.post(
        f"{API_BASE_URL}/api/v1/ai/process",
        json={"text": test_prompt, "model": "default"},
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0

def test_notification_service():
    """Test notification service."""
    # Test health endpoint
    response = requests.get(f"{API_BASE_URL}/api/v1/notifications/health", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    
    # Test notification sending
    test_notification = {
        "type": "test",
        "message": "Test notification",
        "recipient": "test@example.com"
    }
    response = requests.post(
        f"{API_BASE_URL}/api/v1/notifications/send",
        json=test_notification,
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert "notification_id" in data

def test_error_handling():
    """Test error handling and monitoring."""
    # Test error endpoint
    response = requests.get(f"{API_BASE_URL}/api/v1/error", timeout=TEST_TIMEOUT)
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "message" in data
    
    # Test error logging
    response = requests.get(f"{API_BASE_URL}/api/v1/monitoring/errors", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["errors"], list)

def test_monitoring_metrics():
    """Test monitoring metrics collection."""
    response = requests.get(f"{API_BASE_URL}/api/v1/monitoring/metrics", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert isinstance(data["metrics"], dict)
    
    # Check for essential metrics
    essential_metrics = [
        "cpu_usage",
        "memory_usage",
        "response_time",
        "error_rate"
    ]
    for metric in essential_metrics:
        assert metric in data["metrics"]

def test_file_system():
    """Test file system operations."""
    # Test file system health
    response = requests.get(f"{API_BASE_URL}/api/v1/health/filesystem", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "disk_space" in data
    assert "free_space" in data

def test_authentication():
    """Test authentication service."""
    # Test authentication health
    response = requests.get(f"{API_BASE_URL}/api/v1/auth/health", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    
    # Test token generation
    test_credentials = {
        "username": "test_user",
        "password": "test_password"
    }
    response = requests.post(
        f"{API_BASE_URL}/api/v1/auth/token",
        json=test_credentials,
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data

def test_rate_limiting():
    """Test rate limiting functionality."""
    # Make multiple requests to test rate limiting
    for _ in range(5):
        response = requests.get(f"{API_BASE_URL}/api/v1/health", timeout=TEST_TIMEOUT)
        assert response.status_code in [200, 429]  # 429 is rate limit exceeded
    
    # Check rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

def test_cors():
    """Test CORS configuration."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    }
    response = requests.options(f"{API_BASE_URL}/api/v1/health", headers=headers, timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert "Access-Control-Allow-Methods" in response.headers
    assert "Access-Control-Allow-Headers" in response.headers 