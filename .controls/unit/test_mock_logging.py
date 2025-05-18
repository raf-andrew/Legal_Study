"""Unit tests for mock logging service."""
import pytest
import yaml
import json
import logging
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from ..mocks.services.logging import (
    MockLoggingService,
    LogRecord,
    LogHandler,
    FileHandler,
    ConsoleHandler
)

@pytest.fixture
def config() -> Dict[str, Any]:
    """Load test configuration."""
    with open(".config/mock.yaml") as f:
        config = yaml.safe_load(f)
    return config["logging"]

@pytest.fixture
def logging_service(config) -> MockLoggingService:
    """Create mock logging service instance."""
    return MockLoggingService("test_logging", config)

@pytest.fixture
def log_file(tmp_path) -> Path:
    """Create temporary log file."""
    return tmp_path / "test.log"

def test_service_initialization(logging_service):
    """Test service initialization."""
    assert logging_service.name == "test_logging"
    assert logging_service._handlers == {}
    assert logging_service._default_level == "INFO"

def test_service_start(logging_service):
    """Test service start."""
    logging_service.start()
    handlers = logging_service.list_handlers()
    assert len(handlers) == 2  # file and console handlers
    assert any(h.startswith("file_") for h in handlers)
    assert any(h.startswith("console_") for h in handlers)

def test_service_stop(logging_service):
    """Test service stop."""
    logging_service.start()
    assert len(logging_service._handlers) > 0
    
    logging_service.stop()
    assert len(logging_service._handlers) == 0

def test_service_reset(logging_service):
    """Test service reset."""
    logging_service.start()
    logging_service.log("INFO", "test")
    
    logging_service.reset()
    for handler in logging_service._handlers.values():
        assert len(handler.records) == 0

def test_log_record():
    """Test log record creation."""
    timestamp = datetime.now()
    record = LogRecord("INFO", "test message", "test_logger", timestamp,
                      extra="value")
    
    data = record.to_dict()
    assert data["level"] == "INFO"
    assert data["message"] == "test message"
    assert data["logger"] == "test_logger"
    assert data["timestamp"] == timestamp.isoformat()
    assert data["extra"] == "value"

def test_log_handler():
    """Test basic log handler."""
    handler = LogHandler("test", "INFO")
    record = LogRecord("INFO", "test", "test")
    
    assert handler.handle(record) is True
    assert len(handler.records) == 1
    assert handler.records[0] is record

def test_log_handler_level_filtering():
    """Test log level filtering."""
    handler = LogHandler("test", "WARNING")
    info_record = LogRecord("INFO", "test", "test")
    warn_record = LogRecord("WARNING", "test", "test")
    error_record = LogRecord("ERROR", "test", "test")
    
    assert handler.handle(info_record) is False
    assert handler.handle(warn_record) is True
    assert handler.handle(error_record) is True
    assert len(handler.records) == 2

def test_file_handler(log_file):
    """Test file log handler."""
    handler = FileHandler("test", str(log_file))
    record = LogRecord("INFO", "test", "test")
    
    assert handler.handle(record) is True
    assert log_file.exists()
    
    with open(log_file) as f:
        data = json.loads(f.read())
        assert data["message"] == "test"

def test_file_handler_rotation(log_file):
    """Test log file rotation."""
    handler = FileHandler("test", str(log_file), max_bytes=100, backup_count=2)
    
    # Write enough data to trigger rotation
    for i in range(10):
        record = LogRecord("INFO", "x" * 20, "test")
        handler.handle(record)
    
    assert log_file.exists()
    assert Path(f"{log_file}.1").exists()
    assert Path(f"{log_file}.2").exists()
    assert not Path(f"{log_file}.3").exists()

def test_console_handler(capsys):
    """Test console log handler."""
    handler = ConsoleHandler("test")
    record = LogRecord("INFO", "test", "test")
    
    assert handler.handle(record) is True
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["message"] == "test"

def test_add_file_handler(logging_service, log_file):
    """Test adding a file handler."""
    handler = logging_service.add_file_handler("test", str(log_file))
    
    assert isinstance(handler, FileHandler)
    assert handler.name == "test"
    assert handler.filename == str(log_file)
    assert handler.level == "INFO"

def test_add_console_handler(logging_service):
    """Test adding a console handler."""
    handler = logging_service.add_console_handler("test")
    
    assert isinstance(handler, ConsoleHandler)
    assert handler.name == "test"
    assert handler.level == "INFO"

def test_add_duplicate_handler(logging_service):
    """Test adding a duplicate handler."""
    logging_service.add_console_handler("test")
    
    with pytest.raises(ValueError):
        logging_service.add_console_handler("test")

def test_get_handler(logging_service):
    """Test getting a handler."""
    created = logging_service.add_console_handler("test")
    retrieved = logging_service.get_handler("test")
    
    assert retrieved is created

def test_list_handlers(logging_service):
    """Test listing handlers."""
    logging_service.add_console_handler("test1")
    logging_service.add_console_handler("test2")
    
    handlers = logging_service.list_handlers()
    assert "test1" in handlers
    assert "test2" in handlers

def test_log_message(logging_service):
    """Test logging a message."""
    handler = logging_service.add_console_handler("test")
    
    assert logging_service.log("INFO", "test message", extra="value") is True
    records = handler.records
    assert len(records) == 1
    assert records[0].message == "test message"
    assert records[0].attributes["extra"] == "value"

def test_get_records(logging_service):
    """Test getting records from a handler."""
    logging_service.add_console_handler("test")
    logging_service.log("INFO", "test")
    
    records = logging_service.get_records("test")
    assert len(records) == 1
    assert records[0]["message"] == "test"

def test_clear_handler(logging_service):
    """Test clearing a handler."""
    logging_service.add_console_handler("test")
    logging_service.log("INFO", "test")
    
    assert logging_service.clear_handler("test") is True
    records = logging_service.get_records("test")
    assert len(records) == 0

def test_clear_all(logging_service):
    """Test clearing all handlers."""
    handler1 = logging_service.add_console_handler("test1")
    handler2 = logging_service.add_console_handler("test2")
    logging_service.log("INFO", "test")
    
    logging_service.clear_all()
    assert len(handler1.records) == 0
    assert len(handler2.records) == 0

def test_metrics_recording(logging_service):
    """Test metrics recording."""
    logging_service.add_console_handler("test")
    logging_service.log("INFO", "test")
    
    metrics = logging_service.get_metrics()
    assert metrics["total_calls"] == 1
    assert metrics["total_errors"] == 0

def test_error_recording(logging_service):
    """Test error recording."""
    with pytest.raises(ValueError):
        logging_service.get_records("nonexistent")
    
    errors = logging_service.get_errors()
    assert len(errors) == 1
    assert errors[0]["error"] == "Handler not found: nonexistent"

def test_call_recording(logging_service):
    """Test call recording."""
    logging_service.add_console_handler("test")
    logging_service.log("INFO", "test")
    
    calls = logging_service.get_calls()
    assert len(calls) == 1
    assert calls[0]["method"] == "log" 