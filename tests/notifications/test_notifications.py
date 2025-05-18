"""
Notification Tests
Tests for notification functionality including email, push, and in-app notifications.
"""

import os
import pytest
import requests
from datetime import datetime
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 5  # seconds

def test_notification_service_health():
    """Test notification service health endpoint."""
    response = requests.get(f"{API_BASE_URL}/api/v1/notifications/health", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "last_updated" in data

def test_email_notification():
    """Test email notification functionality."""
    test_notification = {
        "type": "email",
        "recipient": "test@example.com",
        "subject": "Test Email",
        "body": "This is a test email notification",
        "template": "default"
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
    assert "sent_at" in data

def test_push_notification():
    """Test push notification functionality."""
    test_notification = {
        "type": "push",
        "recipient": "test_device_token",
        "title": "Test Push",
        "body": "This is a test push notification",
        "data": {"key": "value"}
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
    assert "sent_at" in data

def test_in_app_notification():
    """Test in-app notification functionality."""
    test_notification = {
        "type": "in_app",
        "recipient": "test_user_id",
        "title": "Test In-App",
        "message": "This is a test in-app notification",
        "priority": "high"
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
    assert "sent_at" in data

def test_notification_templates():
    """Test notification template functionality."""
    # Test template listing
    response = requests.get(f"{API_BASE_URL}/api/v1/notifications/templates", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert "templates" in data
    assert isinstance(data["templates"], list)
    assert len(data["templates"]) > 0
    
    # Test template usage
    template = data["templates"][0]
    test_notification = {
        "type": "email",
        "recipient": "test@example.com",
        "template": template["name"],
        "variables": {"name": "Test User"}
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/notifications/send",
        json=test_notification,
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"

def test_notification_preferences():
    """Test notification preferences functionality."""
    # Test getting preferences
    response = requests.get(
        f"{API_BASE_URL}/api/v1/notifications/preferences/test_user_id",
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert "preferences" in data
    assert isinstance(data["preferences"], dict)
    
    # Test updating preferences
    new_preferences = {
        "email": True,
        "push": False,
        "in_app": True,
        "frequency": "daily"
    }
    
    response = requests.put(
        f"{API_BASE_URL}/api/v1/notifications/preferences/test_user_id",
        json=new_preferences,
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert "preferences" in data
    assert data["preferences"] == new_preferences

def test_notification_history():
    """Test notification history functionality."""
    # Test getting history
    response = requests.get(
        f"{API_BASE_URL}/api/v1/notifications/history/test_user_id",
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert "notifications" in data
    assert isinstance(data["notifications"], list)
    
    # Check notification details
    if len(data["notifications"]) > 0:
        notification = data["notifications"][0]
        assert "id" in notification
        assert "type" in notification
        assert "status" in notification
        assert "sent_at" in notification

def test_notification_validation():
    """Test notification validation and error handling."""
    invalid_notifications = [
        {},  # Empty notification
        {"type": "invalid"},  # Invalid type
        {"type": "email"},  # Missing recipient
        {"type": "email", "recipient": "invalid_email"}  # Invalid email
    ]
    
    for notification in invalid_notifications:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/notifications/send",
            json=notification,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "message" in data

def test_notification_rate_limiting():
    """Test notification rate limiting."""
    # Make multiple requests quickly
    responses = []
    for _ in range(10):
        response = requests.post(
            f"{API_BASE_URL}/api/v1/notifications/send",
            json={
                "type": "email",
                "recipient": "test@example.com",
                "subject": "Test",
                "body": "Test"
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

def test_notification_metrics():
    """Test notification metrics collection."""
    response = requests.get(f"{API_BASE_URL}/api/v1/notifications/metrics", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    
    assert "metrics" in data
    metrics = data["metrics"]
    
    # Check essential metrics
    assert "total_sent" in metrics
    assert "success_rate" in metrics
    assert "average_delivery_time" in metrics
    assert "notifications_by_type" in metrics
    
    # Verify metric values
    assert metrics["total_sent"] >= 0
    assert 0 <= metrics["success_rate"] <= 1
    assert metrics["average_delivery_time"] >= 0
    assert isinstance(metrics["notifications_by_type"], dict) 