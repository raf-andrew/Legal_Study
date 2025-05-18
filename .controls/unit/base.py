"""Base test infrastructure for unit testing."""

import logging
import pytest
import typing
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

@dataclass
class TestContext:
    """Test execution context."""
    
    test_name: str
    test_class: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "pending"  # pending, running, passed, failed, skipped, error
    error: Optional[Exception] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseTest:
    """Base class for all unit tests."""
    
    def __init__(self):
        """Initialize test case."""
        self.logger = logging.getLogger(f"test.{self.__class__.__name__}")
        self.context = TestContext(
            test_name=self._get_test_name(),
            test_class=self.__class__.__name__
        )
    
    def _get_test_name(self) -> str:
        """Get current test name from pytest."""
        return pytest.current_test.__name__ if hasattr(pytest, "current_test") else "unknown"
    
    def setup_method(self, method):
        """Set up test method.
        
        Args:
            method: Test method being executed
        """
        self.context.start_time = datetime.now()
        self.context.status = "running"
        self.logger.info(f"Starting test: {self.context.test_name}")
    
    def teardown_method(self, method):
        """Tear down test method.
        
        Args:
            method: Test method being executed
        """
        self.context.end_time = datetime.now()
        self.context.duration_ms = (
            self.context.end_time - self.context.start_time
        ).total_seconds() * 1000
        
        if self.context.status == "running":
            self.context.status = "passed"
        
        self.logger.info(
            f"Completed test: {self.context.test_name} "
            f"(status: {self.context.status}, "
            f"duration: {self.context.duration_ms:.2f}ms)"
        )
    
    def add_warning(self, message: str) -> None:
        """Add warning message to test context.
        
        Args:
            message: Warning message
        """
        self.context.warnings.append(message)
        self.logger.warning(f"Test warning: {message}")
    
    def set_error(self, error: Exception) -> None:
        """Set error in test context.
        
        Args:
            error: Exception that occurred
        """
        self.context.error = error
        self.context.status = "error"
        self.logger.error(f"Test error: {str(error)}")
    
    def skip_test(self, reason: str) -> None:
        """Skip current test.
        
        Args:
            reason: Reason for skipping
        """
        self.context.status = "skipped"
        self.logger.info(f"Skipping test: {reason}")
        pytest.skip(reason)
    
    def fail_test(self, reason: str) -> None:
        """Fail current test.
        
        Args:
            reason: Reason for failure
        """
        self.context.status = "failed"
        self.logger.error(f"Test failed: {reason}")
        pytest.fail(reason)
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to test context.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.context.metadata[key] = value
    
    @staticmethod
    def parametrize(*args, **kwargs):
        """Wrapper for pytest.mark.parametrize."""
        return pytest.mark.parametrize(*args, **kwargs)
    
    @staticmethod
    def skip_if(condition: bool, reason: str):
        """Skip test if condition is true.
        
        Args:
            condition: Skip condition
            reason: Skip reason
        """
        if condition:
            pytest.skip(reason)
    
    @staticmethod
    def fail_if(condition: bool, reason: str):
        """Fail test if condition is true.
        
        Args:
            condition: Fail condition
            reason: Fail reason
        """
        if condition:
            pytest.fail(reason)
    
    @staticmethod
    def assert_logs(caplog, level: str, message: str):
        """Assert that a log message exists.
        
        Args:
            caplog: pytest caplog fixture
            level: Expected log level
            message: Expected log message
        """
        assert any(
            record.levelname == level.upper() and message in record.message
            for record in caplog.records
        )
    
    @staticmethod
    def assert_no_logs(caplog, level: str, message: str):
        """Assert that a log message does not exist.
        
        Args:
            caplog: pytest caplog fixture
            level: Log level to check
            message: Log message to check
        """
        assert not any(
            record.levelname == level.upper() and message in record.message
            for record in caplog.records
        )
    
    @staticmethod
    def assert_warning_logged(caplog, message: str):
        """Assert that a warning was logged.
        
        Args:
            caplog: pytest caplog fixture
            message: Expected warning message
        """
        BaseTest.assert_logs(caplog, "WARNING", message)
    
    @staticmethod
    def assert_error_logged(caplog, message: str):
        """Assert that an error was logged.
        
        Args:
            caplog: pytest caplog fixture
            message: Expected error message
        """
        BaseTest.assert_logs(caplog, "ERROR", message)
    
    @staticmethod
    def assert_info_logged(caplog, message: str):
        """Assert that an info message was logged.
        
        Args:
            caplog: pytest caplog fixture
            message: Expected info message
        """
        BaseTest.assert_logs(caplog, "INFO", message)
    
    @staticmethod
    def assert_debug_logged(caplog, message: str):
        """Assert that a debug message was logged.
        
        Args:
            caplog: pytest caplog fixture
            message: Expected debug message
        """
        BaseTest.assert_logs(caplog, "DEBUG", message) 