"""Unit tests for security monitoring interface."""

import pytest
from datetime import datetime, timedelta
from typing import List, Set

from ...security.monitoring import (
    SecurityEvent,
    SecurityEventType,
    SecurityEventSeverity,
    SecurityMonitor,
    InMemorySecurityMonitor
)

@pytest.fixture
def monitor() -> SecurityMonitor:
    """Create security monitor."""
    return InMemorySecurityMonitor()

@pytest.fixture
def test_events() -> List[SecurityEvent]:
    """Create test security events."""
    now = datetime.now()
    return [
        SecurityEvent(
            event_type=SecurityEventType.AUTH_SUCCESS,
            severity=SecurityEventSeverity.INFO,
            timestamp=now - timedelta(minutes=5),
            user_id="user1",
            command_name="login",
            source="auth.jwt",
            details={"method": "jwt"}
        ),
        SecurityEvent(
            event_type=SecurityEventType.AUTH_FAILURE,
            severity=SecurityEventSeverity.ERROR,
            timestamp=now - timedelta(minutes=4),
            user_id="user2",
            command_name="login",
            source="auth.jwt",
            details={"reason": "invalid_token"}
        ),
        SecurityEvent(
            event_type=SecurityEventType.PERMISSION_GRANT,
            severity=SecurityEventSeverity.INFO,
            timestamp=now - timedelta(minutes=3),
            user_id="user1",
            command_name="grant_permission",
            source="auth.rbac",
            details={"permission": "read"}
        ),
        SecurityEvent(
            event_type=SecurityEventType.VALIDATION_FAILURE,
            severity=SecurityEventSeverity.WARNING,
            timestamp=now - timedelta(minutes=2),
            user_id="user1",
            command_name="create_item",
            source="validation",
            details={"errors": ["invalid_input"]}
        ),
        SecurityEvent(
            event_type=SecurityEventType.SECURITY_VIOLATION,
            severity=SecurityEventSeverity.CRITICAL,
            timestamp=now - timedelta(minutes=1),
            user_id="user2",
            command_name="delete_item",
            source="security",
            details={"reason": "unauthorized_access"}
        )
    ]

def test_security_event_initialization():
    """Test security event initialization."""
    event = SecurityEvent(
        event_type=SecurityEventType.AUTH_SUCCESS,
        severity=SecurityEventSeverity.INFO,
        user_id="test_user",
        command_name="test_command",
        source="test_source",
        details={"test": True},
        metadata={"meta": True}
    )
    
    assert event.event_type == SecurityEventType.AUTH_SUCCESS
    assert event.severity == SecurityEventSeverity.INFO
    assert isinstance(event.timestamp, datetime)
    assert event.user_id == "test_user"
    assert event.command_name == "test_command"
    assert event.source == "test_source"
    assert event.details == {"test": True}
    assert event.metadata == {"meta": True}

def test_monitor_record_event(monitor):
    """Test recording security events."""
    event = SecurityEvent(
        event_type=SecurityEventType.AUTH_SUCCESS,
        severity=SecurityEventSeverity.INFO
    )
    
    monitor.record_event(event)
    events = monitor.get_events()
    
    assert len(events) == 1
    assert events[0] == event

def test_monitor_get_events_by_type(monitor, test_events):
    """Test getting events by type."""
    for event in test_events:
        monitor.record_event(event)
    
    # Filter by single type
    events = monitor.get_events(
        event_types={SecurityEventType.AUTH_SUCCESS}
    )
    assert len(events) == 1
    assert all(e.event_type == SecurityEventType.AUTH_SUCCESS for e in events)
    
    # Filter by multiple types
    events = monitor.get_events(
        event_types={
            SecurityEventType.AUTH_SUCCESS,
            SecurityEventType.AUTH_FAILURE
        }
    )
    assert len(events) == 2
    assert all(
        e.event_type in {
            SecurityEventType.AUTH_SUCCESS,
            SecurityEventType.AUTH_FAILURE
        }
        for e in events
    )

def test_monitor_get_events_by_severity(monitor, test_events):
    """Test getting events by severity."""
    for event in test_events:
        monitor.record_event(event)
    
    # Filter by single severity
    events = monitor.get_events(
        severity={SecurityEventSeverity.CRITICAL}
    )
    assert len(events) == 1
    assert all(e.severity == SecurityEventSeverity.CRITICAL for e in events)
    
    # Filter by multiple severities
    events = monitor.get_events(
        severity={
            SecurityEventSeverity.ERROR,
            SecurityEventSeverity.CRITICAL
        }
    )
    assert len(events) == 2
    assert all(
        e.severity in {
            SecurityEventSeverity.ERROR,
            SecurityEventSeverity.CRITICAL
        }
        for e in events
    )

def test_monitor_get_events_by_time(monitor, test_events):
    """Test getting events by time range."""
    for event in test_events:
        monitor.record_event(event)
    
    now = datetime.now()
    
    # Filter by start time
    events = monitor.get_events(
        start_time=now - timedelta(minutes=3)
    )
    assert len(events) == 3
    
    # Filter by end time
    events = monitor.get_events(
        end_time=now - timedelta(minutes=3)
    )
    assert len(events) == 3
    
    # Filter by time range
    events = monitor.get_events(
        start_time=now - timedelta(minutes=4),
        end_time=now - timedelta(minutes=2)
    )
    assert len(events) == 3

def test_monitor_get_events_by_user(monitor, test_events):
    """Test getting events by user."""
    for event in test_events:
        monitor.record_event(event)
    
    events = monitor.get_events(user_id="user1")
    assert len(events) == 3
    assert all(e.user_id == "user1" for e in events)

def test_monitor_get_events_by_command(monitor, test_events):
    """Test getting events by command."""
    for event in test_events:
        monitor.record_event(event)
    
    events = monitor.get_events(command_name="login")
    assert len(events) == 2
    assert all(e.command_name == "login" for e in events)

def test_monitor_get_events_by_source(monitor, test_events):
    """Test getting events by source."""
    for event in test_events:
        monitor.record_event(event)
    
    events = monitor.get_events(source="auth.jwt")
    assert len(events) == 2
    assert all(e.source == "auth.jwt" for e in events)

def test_monitor_get_events_combined_filters(monitor, test_events):
    """Test getting events with combined filters."""
    for event in test_events:
        monitor.record_event(event)
    
    events = monitor.get_events(
        event_types={SecurityEventType.AUTH_SUCCESS},
        severity={SecurityEventSeverity.INFO},
        user_id="user1",
        command_name="login",
        source="auth.jwt"
    )
    assert len(events) == 1
    assert events[0].event_type == SecurityEventType.AUTH_SUCCESS
    assert events[0].severity == SecurityEventSeverity.INFO
    assert events[0].user_id == "user1"
    assert events[0].command_name == "login"
    assert events[0].source == "auth.jwt"

def test_monitor_clear_events(monitor, test_events):
    """Test clearing events."""
    for event in test_events:
        monitor.record_event(event)
    
    # Clear all events
    monitor.clear_events()
    assert len(monitor.get_events()) == 0
    
    # Record events again
    for event in test_events:
        monitor.record_event(event)
    
    # Clear events before specific time
    now = datetime.now()
    monitor.clear_events(before_time=now - timedelta(minutes=3))
    events = monitor.get_events()
    assert len(events) == 3
    assert all(
        e.timestamp >= now - timedelta(minutes=3)
        for e in events
    ) 