"""Monitoring utility for security events."""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from prometheus_client import Counter, Histogram, Gauge

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metrics
AUTH_FAILURES = Counter(
    'auth_failures_total',
    'Total number of authentication failures',
    ['reason']
)

AUTH_LATENCY = Histogram(
    'auth_latency_seconds',
    'Authentication request latency',
    ['endpoint']
)

ACTIVE_SESSIONS = Gauge(
    'active_sessions',
    'Number of active user sessions'
)

@dataclass
class SecurityEvent:
    """Security event data."""
    timestamp: str
    event_type: str
    user_id: Optional[str]
    ip_address: str
    details: Dict
    severity: str

class SecurityMonitor:
    """Monitor and track security events."""
    
    def __init__(self, events_file: str = ".security/events.json"):
        """Initialize security monitor.
        
        Args:
            events_file: Path to events storage file
        """
        self.events_file = Path(events_file)
        self.events_file.parent.mkdir(parents=True, exist_ok=True)
        self.events: List[Dict] = []
        self.load_events()
        
    def load_events(self) -> None:
        """Load events from storage."""
        if self.events_file.exists():
            try:
                with open(self.events_file) as f:
                    self.events = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load events: {e}")
                self.events = []
                
    def save_events(self) -> None:
        """Save events to storage."""
        try:
            with open(self.events_file, 'w') as f:
                json.dump(self.events, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save events: {e}")
            
    def record_event(
        self,
        event_type: str,
        user_id: Optional[str],
        ip_address: str,
        details: Dict,
        severity: str = "info"
    ) -> None:
        """Record a security event.
        
        Args:
            event_type: Type of security event
            user_id: ID of user involved (if any)
            ip_address: IP address of request
            details: Additional event details
            severity: Event severity level
        """
        event = SecurityEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            severity=severity
        )
        
        # Add to events list
        self.events.append(asdict(event))
        
        # Update metrics
        if event_type == "auth_failure":
            AUTH_FAILURES.labels(
                reason=details.get("reason", "unknown")
            ).inc()
            
        # Save events
        self.save_events()
        
        # Log event
        logger.warning(f"Security event: {event}")
        
    def get_events(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get security events with optional filtering.
        
        Args:
            event_type: Filter by event type
            severity: Filter by severity level
            limit: Maximum number of events to return
            
        Returns:
            List of matching events
        """
        filtered = self.events
        
        if event_type:
            filtered = [e for e in filtered if e["event_type"] == event_type]
            
        if severity:
            filtered = [e for e in filtered if e["severity"] == severity]
            
        return sorted(
            filtered,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
        
    def get_auth_failures(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        minutes: int = 60
    ) -> int:
        """Get count of authentication failures.
        
        Args:
            user_id: Filter by user ID
            ip_address: Filter by IP address
            minutes: Time window in minutes
            
        Returns:
            Count of matching failures
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        failures = [
            e for e in self.events
            if (
                e["event_type"] == "auth_failure"
                and datetime.fromisoformat(e["timestamp"]) >= cutoff
                and (user_id is None or e["user_id"] == user_id)
                and (ip_address is None or e["ip_address"] == ip_address)
            )
        ]
        
        return len(failures)
        
    def should_block(
        self,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Check if authentication should be blocked.
        
        Args:
            user_id: User ID to check
            ip_address: IP address to check
            
        Returns:
            True if authentication should be blocked
        """
        # Check user failures
        if user_id and self.get_auth_failures(user_id=user_id) >= 5:
            return True
            
        # Check IP failures
        if ip_address and self.get_auth_failures(ip_address=ip_address) >= 10:
            return True
            
        return False
        
    def track_session(self, action: str) -> None:
        """Track user session count.
        
        Args:
            action: Either 'start' or 'end'
        """
        if action == "start":
            ACTIVE_SESSIONS.inc()
        elif action == "end":
            ACTIVE_SESSIONS.dec()
            
    def track_latency(self, endpoint: str, duration: float) -> None:
        """Track authentication latency.
        
        Args:
            endpoint: Authentication endpoint
            duration: Request duration in seconds
        """
        AUTH_LATENCY.labels(endpoint=endpoint).observe(duration) 