"""Tests for security monitoring utility."""

import pytest
import json
from datetime import datetime, timedelta
from pathlib import Path
from app.core.monitoring import SecurityMonitor, SecurityEvent

@pytest.fixture
def test_events_file(tmp_path):
    """Create a temporary events file."""
    return str(tmp_path / "test_events.json")

@pytest.fixture
def security_monitor(test_events_file):
    """Create a security monitor instance."""
    return SecurityMonitor(test_events_file)

def test_record_event(security_monitor):
    """Test event recording."""
    security_monitor.record_event(
        event_type="auth_failure",
        user_id="test_user",
        ip_address="127.0.0.1",
        details={"reason": "invalid_password"},
        severity="warning"
    )
    
    events = security_monitor.get_events()
    assert len(events) == 1
    assert events[0]["event_type"] == "auth_failure"
    assert events[0]["user_id"] == "test_user"
    assert events[0]["ip_address"] == "127.0.0.1"
    assert events[0]["details"]["reason"] == "invalid_password"
    assert events[0]["severity"] == "warning"

def test_event_storage(test_events_file, security_monitor):
    """Test event storage."""
    # Record event
    security_monitor.record_event(
        event_type="auth_failure",
        user_id="test_user",
        ip_address="127.0.0.1",
        details={"reason": "invalid_password"}
    )
    
    # Check file exists
    assert Path(test_events_file).exists()
    
    # Check file content
    with open(test_events_file) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["event_type"] == "auth_failure"

def test_get_events_filtering(security_monitor):
    """Test event filtering."""
    # Add test events
    security_monitor.record_event(
        event_type="auth_failure",
        user_id="user1",
        ip_address="127.0.0.1",
        details={"reason": "invalid_password"},
        severity="warning"
    )
    security_monitor.record_event(
        event_type="auth_success",
        user_id="user2",
        ip_address="127.0.0.1",
        details={},
        severity="info"
    )
    
    # Filter by type
    failures = security_monitor.get_events(event_type="auth_failure")
    assert len(failures) == 1
    assert failures[0]["user_id"] == "user1"
    
    # Filter by severity
    warnings = security_monitor.get_events(severity="warning")
    assert len(warnings) == 1
    assert warnings[0]["event_type"] == "auth_failure"

def test_auth_failure_tracking(security_monitor):
    """Test authentication failure tracking."""
    # Add multiple failures
    for _ in range(3):
        security_monitor.record_event(
            event_type="auth_failure",
            user_id="test_user",
            ip_address="127.0.0.1",
            details={"reason": "invalid_password"}
        )
    
    # Check failure count
    assert security_monitor.get_auth_failures(user_id="test_user") == 3
    assert security_monitor.get_auth_failures(ip_address="127.0.0.1") == 3

def test_blocking_logic(security_monitor):
    """Test authentication blocking logic."""
    # Add failures for user
    for _ in range(5):
        security_monitor.record_event(
            event_type="auth_failure",
            user_id="test_user",
            ip_address="127.0.0.1",
            details={"reason": "invalid_password"}
        )
    
    # Check blocking
    assert security_monitor.should_block(user_id="test_user")
    assert not security_monitor.should_block(user_id="other_user")

def test_session_tracking(security_monitor):
    """Test session tracking."""
    initial = float(ACTIVE_SESSIONS._value.get())
    
    # Start session
    security_monitor.track_session("start")
    assert float(ACTIVE_SESSIONS._value.get()) == initial + 1
    
    # End session
    security_monitor.track_session("end")
    assert float(ACTIVE_SESSIONS._value.get()) == initial

def test_latency_tracking(security_monitor):
    """Test latency tracking."""
    # Track latency
    security_monitor.track_latency("login", 0.5)
    
    # Check histogram
    histogram = AUTH_LATENCY.labels("login")
    assert histogram._sum.get() > 0

def test_error_handling(security_monitor, caplog):
    """Test error handling."""
    # Test with invalid file path
    invalid_monitor = SecurityMonitor("/invalid/path/events.json")
    invalid_monitor.record_event(
        event_type="test",
        user_id="user",
        ip_address="127.0.0.1",
        details={}
    )
    assert "Failed to save events" in caplog.text

def test_event_cleanup(security_monitor):
    """Test old event cleanup."""
    # Add old event
    old_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()
    security_monitor.events.append({
        "timestamp": old_time,
        "event_type": "auth_failure",
        "user_id": "test_user",
        "ip_address": "127.0.0.1",
        "details": {},
        "severity": "warning"
    })
    
    # Add recent event
    security_monitor.record_event(
        event_type="auth_failure",
        user_id="test_user",
        ip_address="127.0.0.1",
        details={}
    )
    
    # Check failure count (should only count recent event)
    assert security_monitor.get_auth_failures(
        user_id="test_user",
        minutes=60
    ) == 1 