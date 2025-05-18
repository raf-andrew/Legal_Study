"""Security monitoring interface for command execution."""

import abc
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

class SecurityEventType(Enum):
    """Types of security events."""
    
    # Authentication events
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    AUTH_LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token.refresh"
    TOKEN_REVOKE = "auth.token.revoke"
    
    # Authorization events
    PERMISSION_GRANT = "auth.permission.grant"
    PERMISSION_REVOKE = "auth.permission.revoke"
    ROLE_GRANT = "auth.role.grant"
    ROLE_REVOKE = "auth.role.revoke"
    
    # Validation events
    VALIDATION_SUCCESS = "validation.success"
    VALIDATION_FAILURE = "validation.failure"
    
    # Command events
    COMMAND_START = "command.start"
    COMMAND_SUCCESS = "command.success"
    COMMAND_FAILURE = "command.failure"
    
    # Security events
    SECURITY_VIOLATION = "security.violation"
    SECURITY_WARNING = "security.warning"
    SECURITY_INFO = "security.info"

class SecurityEventSeverity(Enum):
    """Severity levels for security events."""
    
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class SecurityEvent:
    """Security event data."""
    
    event_type: SecurityEventType
    severity: SecurityEventSeverity
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    command_name: Optional[str] = None
    source: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class SecurityMonitor(abc.ABC):
    """Interface for security monitoring."""
    
    @abc.abstractmethod
    def record_event(self, event: SecurityEvent) -> None:
        """Record a security event.
        
        Args:
            event: Security event to record
        """
        raise NotImplementedError("Security monitors must implement record_event")
    
    @abc.abstractmethod
    def get_events(
        self,
        event_types: Optional[Set[SecurityEventType]] = None,
        severity: Optional[Set[SecurityEventSeverity]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        command_name: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[SecurityEvent]:
        """Get recorded security events.
        
        Args:
            event_types: Optional set of event types to filter by
            severity: Optional set of severity levels to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            user_id: Optional user ID to filter by
            command_name: Optional command name to filter by
            source: Optional source to filter by
            
        Returns:
            List of matching security events
        """
        raise NotImplementedError("Security monitors must implement get_events")
    
    @abc.abstractmethod
    def clear_events(
        self,
        before_time: Optional[datetime] = None
    ) -> None:
        """Clear recorded security events.
        
        Args:
            before_time: Optional time before which to clear events
        """
        raise NotImplementedError("Security monitors must implement clear_events")

class InMemorySecurityMonitor(SecurityMonitor):
    """In-memory implementation of security monitor."""
    
    def __init__(self):
        """Initialize monitor."""
        self._events: List[SecurityEvent] = []
        self.logger = logging.getLogger("security.monitor")
    
    def record_event(self, event: SecurityEvent) -> None:
        """Record a security event."""
        self._events.append(event)
        self.logger.info(
            f"Security event recorded: {event.event_type.value} "
            f"[{event.severity.value}] "
            f"user={event.user_id} "
            f"command={event.command_name} "
            f"source={event.source}"
        )
    
    def get_events(
        self,
        event_types: Optional[Set[SecurityEventType]] = None,
        severity: Optional[Set[SecurityEventSeverity]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        command_name: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[SecurityEvent]:
        """Get recorded security events."""
        filtered_events = self._events
        
        if event_types:
            filtered_events = [
                e for e in filtered_events
                if e.event_type in event_types
            ]
        
        if severity:
            filtered_events = [
                e for e in filtered_events
                if e.severity in severity
            ]
        
        if start_time:
            filtered_events = [
                e for e in filtered_events
                if e.timestamp >= start_time
            ]
        
        if end_time:
            filtered_events = [
                e for e in filtered_events
                if e.timestamp <= end_time
            ]
        
        if user_id:
            filtered_events = [
                e for e in filtered_events
                if e.user_id == user_id
            ]
        
        if command_name:
            filtered_events = [
                e for e in filtered_events
                if e.command_name == command_name
            ]
        
        if source:
            filtered_events = [
                e for e in filtered_events
                if e.source == source
            ]
        
        return filtered_events
    
    def clear_events(
        self,
        before_time: Optional[datetime] = None
    ) -> None:
        """Clear recorded security events."""
        if before_time:
            self._events = [
                e for e in self._events
                if e.timestamp > before_time
            ]
            self.logger.info(f"Cleared events before {before_time}")
        else:
            self._events.clear()
            self.logger.info("Cleared all events") 