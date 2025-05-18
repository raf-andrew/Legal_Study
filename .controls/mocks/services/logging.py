"""Mock logging service implementation."""
import logging
import threading
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path
from ..base import BaseMockService

logger = logging.getLogger(__name__)

class LogRecord:
    """Mock log record."""
    
    def __init__(self, level: str, message: str, logger_name: str,
                 timestamp: Optional[datetime] = None, **kwargs):
        self.level = level.upper()
        self.message = message
        self.logger_name = logger_name
        self.timestamp = timestamp or datetime.now()
        self.attributes = kwargs
        self.record_id = str(hash((self.timestamp, self.message)))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.record_id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "logger": self.logger_name,
            "message": self.message,
            **self.attributes
        }

class LogHandler:
    """Mock log handler."""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.name = name
        self.level = level.upper()
        self.level_no = getattr(logging, self.level)
        self.records: List[LogRecord] = []
        self._lock = threading.Lock()

    def handle(self, record: LogRecord) -> bool:
        """Handle log record."""
        if getattr(logging, record.level) >= self.level_no:
            with self._lock:
                self.records.append(record)
            return True
        return False

    def clear(self):
        """Clear records."""
        with self._lock:
            self.records.clear()

class FileHandler(LogHandler):
    """Mock file log handler."""
    
    def __init__(self, name: str, filename: str, level: str = "INFO",
                 max_bytes: int = 10485760, backup_count: int = 5):
        super().__init__(name, level)
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.current_size = 0
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure log directory exists."""
        Path(self.filename).parent.mkdir(parents=True, exist_ok=True)

    def handle(self, record: LogRecord) -> bool:
        """Handle log record."""
        if super().handle(record):
            record_data = json.dumps(record.to_dict()) + "\n"
            record_size = len(record_data.encode())
            
            if self.current_size + record_size > self.max_bytes:
                self._rotate()
            
            with open(self.filename, "a") as f:
                f.write(record_data)
            
            self.current_size += record_size
            return True
        return False

    def _rotate(self):
        """Rotate log files."""
        if not Path(self.filename).exists():
            return
        
        for i in range(self.backup_count - 1, 0, -1):
            src = f"{self.filename}.{i}"
            dst = f"{self.filename}.{i + 1}"
            
            if Path(src).exists():
                Path(src).rename(dst)
        
        if Path(self.filename).exists():
            Path(self.filename).rename(f"{self.filename}.1")
        
        self.current_size = 0

class ConsoleHandler(LogHandler):
    """Mock console log handler."""
    
    def handle(self, record: LogRecord) -> bool:
        """Handle log record."""
        if super().handle(record):
            print(json.dumps(record.to_dict()))
            return True
        return False

class MockLoggingService(BaseMockService):
    """Mock logging service."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self._handlers: Dict[str, LogHandler] = {}
        self._default_level = "INFO"

    def _start(self):
        """Start the mock logging service."""
        self._load_handlers()

    def _stop(self):
        """Stop the mock logging service."""
        self._handlers.clear()

    def _reset(self):
        """Reset the mock logging service."""
        super()._reset()
        for handler in self._handlers.values():
            handler.clear()

    def _load_handlers(self):
        """Load handlers from configuration."""
        handlers = self.state.config.get("handlers", [])
        for handler_config in handlers:
            type_ = handler_config["type"]
            name = f"{type_}_{len(self._handlers)}"
            level = handler_config.get("level", self._default_level)
            
            if type_ == "file":
                self.add_file_handler(
                    name,
                    handler_config["filename"],
                    level,
                    handler_config.get("max_bytes", 10485760),
                    handler_config.get("backup_count", 5)
                )
            elif type_ == "console":
                self.add_console_handler(name, level)

    def add_file_handler(self, name: str, filename: str, level: str = "INFO",
                        max_bytes: int = 10485760, backup_count: int = 5) -> FileHandler:
        """Add a file handler."""
        if name in self._handlers:
            raise ValueError(f"Handler already exists: {name}")
        
        handler = FileHandler(name, filename, level, max_bytes, backup_count)
        self._handlers[name] = handler
        self.logger.info(f"Added file handler: {name}")
        return handler

    def add_console_handler(self, name: str, level: str = "INFO") -> ConsoleHandler:
        """Add a console handler."""
        if name in self._handlers:
            raise ValueError(f"Handler already exists: {name}")
        
        handler = ConsoleHandler(name, level)
        self._handlers[name] = handler
        self.logger.info(f"Added console handler: {name}")
        return handler

    def get_handler(self, name: str) -> Optional[LogHandler]:
        """Get a handler."""
        return self._handlers.get(name)

    def list_handlers(self) -> List[str]:
        """List handlers."""
        return list(self._handlers.keys())

    def log(self, level: str, message: str, logger_name: str = "root", **kwargs) -> bool:
        """Log a message."""
        try:
            self.state.record_call("log", (level, message), {
                "logger_name": logger_name,
                **kwargs
            })
            
            record = LogRecord(level, message, logger_name, **kwargs)
            handled = False
            
            for handler in self._handlers.values():
                if handler.handle(record):
                    handled = True
            
            return handled
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "log",
                "level": level,
                "message": message,
                "logger_name": logger_name,
                "kwargs": kwargs
            })
            raise

    def get_records(self, handler_name: str) -> List[Dict[str, Any]]:
        """Get records from a handler."""
        try:
            self.state.record_call("get_records", (handler_name,), {})
            
            handler = self.get_handler(handler_name)
            if not handler:
                raise ValueError(f"Handler not found: {handler_name}")
            
            return [record.to_dict() for record in handler.records]
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "get_records",
                "handler_name": handler_name
            })
            raise

    def clear_handler(self, handler_name: str) -> bool:
        """Clear records from a handler."""
        try:
            self.state.record_call("clear_handler", (handler_name,), {})
            
            handler = self.get_handler(handler_name)
            if not handler:
                return False
            
            handler.clear()
            return True
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "clear_handler",
                "handler_name": handler_name
            })
            raise

    def clear_all(self):
        """Clear all handlers."""
        try:
            self.state.record_call("clear_all", (), {})
            self._reset()
            
        except Exception as e:
            self.state.record_error(e, {
                "action": "clear_all"
            })
            raise 