"""Base mock service implementation."""
import logging
import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(".logs/mocks.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class MockServiceState:
    """Mock service state container."""
    
    def __init__(self):
        self.calls: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.data: Dict[str, Any] = {}
        self.config: Dict[str, Any] = {}
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        self._lock = threading.Lock()

    def record_call(self, method: str, args: tuple, kwargs: dict):
        """Record a method call."""
        with self._lock:
            self.calls.append({
                "method": method,
                "args": args,
                "kwargs": kwargs,
                "timestamp": datetime.now().isoformat()
            })

    def record_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Record an error."""
        with self._lock:
            self.errors.append({
                "error": str(error),
                "type": error.__class__.__name__,
                "context": context,
                "timestamp": datetime.now().isoformat()
            })

    def set_data(self, key: str, value: Any):
        """Set state data."""
        with self._lock:
            self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get state data."""
        with self._lock:
            return self.data.get(key, default)

    def update_config(self, config: Dict[str, Any]):
        """Update configuration."""
        with self._lock:
            self.config.update(config)

    def reset(self):
        """Reset state."""
        with self._lock:
            self.calls = []
            self.errors = []
            self.data = {}
            self.started_at = None
            self.stopped_at = None

class BaseMockService(ABC):
    """Base class for mock services."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.state = MockServiceState()
        if config:
            self.state.update_config(config)
        self.logger = logging.getLogger(f"mock.{name}")

    def start(self):
        """Start the mock service."""
        try:
            self.logger.info(f"Starting mock service: {self.name}")
            self.state.started_at = datetime.now()
            self._start()
        except Exception as e:
            self.state.record_error(e, {"action": "start"})
            raise

    def stop(self):
        """Stop the mock service."""
        try:
            self.logger.info(f"Stopping mock service: {self.name}")
            self.state.stopped_at = datetime.now()
            self._stop()
        except Exception as e:
            self.state.record_error(e, {"action": "stop"})
            raise

    def reset(self):
        """Reset the mock service."""
        try:
            self.logger.info(f"Resetting mock service: {self.name}")
            self.state.reset()
            self._reset()
        except Exception as e:
            self.state.record_error(e, {"action": "reset"})
            raise

    @abstractmethod
    def _start(self):
        """Start implementation."""
        pass

    @abstractmethod
    def _stop(self):
        """Stop implementation."""
        pass

    def _reset(self):
        """Reset implementation."""
        pass

    def configure(self, config: Dict[str, Any]):
        """Configure the mock service."""
        try:
            self.logger.info(f"Configuring mock service: {self.name}")
            self.state.update_config(config)
            self._configure(config)
        except Exception as e:
            self.state.record_error(e, {"action": "configure", "config": config})
            raise

    def _configure(self, config: Dict[str, Any]):
        """Configure implementation."""
        pass

    def verify_calls(self, method: str, count: Optional[int] = None) -> bool:
        """Verify method calls."""
        calls = [call for call in self.state.calls if call["method"] == method]
        if count is not None:
            return len(calls) == count
        return len(calls) > 0

    def verify_no_errors(self) -> bool:
        """Verify no errors occurred."""
        return len(self.state.errors) == 0

    def get_calls(self, method: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recorded calls."""
        if method:
            return [call for call in self.state.calls if call["method"] == method]
        return self.state.calls

    def get_errors(self) -> List[Dict[str, Any]]:
        """Get recorded errors."""
        return self.state.errors

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics."""
        return {
            "name": self.name,
            "started_at": self.state.started_at.isoformat() if self.state.started_at else None,
            "stopped_at": self.state.stopped_at.isoformat() if self.state.stopped_at else None,
            "total_calls": len(self.state.calls),
            "total_errors": len(self.state.errors),
            "config": self.state.config
        } 