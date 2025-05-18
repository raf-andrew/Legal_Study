"""
Error Handling Tests
Tests for error handling, logging, and monitoring functionality.
"""

import os
import pytest
import requests
from datetime import datetime
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 5  # seconds

def test_error_handling_service_health():
    """Test error handling service health endpoint."""
    response = requests.get(f"{API_BASE_URL}/api/v1/error-handling/health", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "last_updated" in data

def test_error_logging():
    """Test error logging functionality."""
    # Test error logging
    test_error = {
        "level": "error",
        "message": "Test error message",
        "context": {
            "service": "test_service",
            "action": "test_action"
        }
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/error-handling/log",
        json=test_error,
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "logged"
    assert "error_id" in data
    assert "logged_at" in data

def test_error_aggregation():
    """Test error aggregation functionality."""
    # Test getting aggregated errors
    response = requests.get(
        f"{API_BASE_URL}/api/v1/error-handling/aggregate",
        params={"timeframe": "1h"},
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert "errors" in data
    assert isinstance(data["errors"], list)
    
    # Check error details
    if len(data["errors"]) > 0:
        error = data["errors"][0]
        assert "count" in error
        assert "level" in error
        assert "message" in error
        assert "last_occurrence" in error

def test_error_patterns():
    """Test error pattern detection."""
    # Test getting error patterns
    response = requests.get(
        f"{API_BASE_URL}/api/v1/error-handling/patterns",
        params={"timeframe": "24h"},
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert "patterns" in data
    assert isinstance(data["patterns"], list)
    
    # Check pattern details
    if len(data["patterns"]) > 0:
        pattern = data["patterns"][0]
        assert "pattern" in pattern
        assert "count" in pattern
        assert "first_seen" in pattern
        assert "last_seen" in pattern

def test_error_resolution():
    """Test error resolution tracking."""
    # Test resolving an error
    test_resolution = {
        "error_id": "test_error_id",
        "resolution": "Fixed by updating configuration",
        "resolved_by": "test_user"
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/error-handling/resolve",
        json=test_resolution,
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert "resolved_at" in data

def test_error_notifications():
    """Test error notification functionality."""
    # Test error notification settings
    test_settings = {
        "level": "error",
        "channels": ["email", "slack"],
        "recipients": ["admin@example.com", "#alerts"]
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/error-handling/notifications/settings",
        json=test_settings,
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert "settings" in data

def test_error_recovery():
    """Test error recovery mechanisms."""
    # Test automatic recovery
    test_recovery = {
        "error_id": "test_error_id",
        "action": "retry",
        "max_attempts": 3
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/error-handling/recover",
        json=test_recovery,
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recovery_started"
    assert "recovery_id" in data

def test_error_metrics():
    """Test error metrics collection."""
    response = requests.get(f"{API_BASE_URL}/api/v1/error-handling/metrics", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    
    assert "metrics" in data
    metrics = data["metrics"]
    
    # Check essential metrics
    assert "total_errors" in metrics
    assert "error_rate" in metrics
    assert "resolution_time" in metrics
    assert "errors_by_level" in metrics
    
    # Verify metric values
    assert metrics["total_errors"] >= 0
    assert 0 <= metrics["error_rate"] <= 1
    assert metrics["resolution_time"] >= 0
    assert isinstance(metrics["errors_by_level"], dict)

def test_error_validation():
    """Test error validation and error handling."""
    invalid_errors = [
        {},  # Empty error
        {"level": "invalid"},  # Invalid level
        {"message": "Test"},  # Missing level
        {"level": "error"}  # Missing message
    ]
    
    for error in invalid_errors:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/error-handling/log",
            json=error,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "message" in data

def test_error_rate_limiting():
    """Test error logging rate limiting."""
    # Make multiple requests quickly
    responses = []
    for _ in range(10):
        response = requests.post(
            f"{API_BASE_URL}/api/v1/error-handling/log",
            json={
                "level": "error",
                "message": "Test error"
            },
            timeout=TEST_TIMEOUT
        )
        responses.append(response)
    
    # Check rate limit headers
    assert "X-RateLimit-Limit" in responses[-1].headers
    assert "X-RateLimit-Remaining" in responses[-1].headers
    assert "X-RateLimit-Reset" in responses[-1].headers
    
    # Verify some requests were rate limited
    assert any(r.status_code == 429 for r in responses)

def test_error_context():
    """Test error context preservation."""
    # Test error with context
    test_error = {
        "level": "error",
        "message": "Test error with context",
        "context": {
            "service": "test_service",
            "action": "test_action",
            "user_id": "test_user",
            "request_id": "test_request",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/error-handling/log",
        json=test_error,
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "logged"
    assert "error_id" in data
    
    # Verify context was preserved
    response = requests.get(
        f"{API_BASE_URL}/api/v1/error-handling/errors/{data['error_id']}",
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    error_data = response.json()
    assert "context" in error_data
    assert error_data["context"] == test_error["context"] 