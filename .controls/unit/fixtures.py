"""Common test fixtures for unit testing."""

import os
import pytest
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional

from .base import BaseTest
from ..mocks.database import MockDatabase
from ..mocks.auth import MockAuthService
from ..mocks.cache import MockCacheService
from ..mocks.queue import MockQueueService

@pytest.fixture
def base_test() -> BaseTest:
    """Create base test instance."""
    return BaseTest()

@pytest.fixture
def mock_database() -> MockDatabase:
    """Create mock database instance."""
    return MockDatabase(
        name="test_db",
        connection_string="mock://localhost:5432/test_db"
    )

@pytest.fixture
def mock_auth_service() -> MockAuthService:
    """Create mock authentication service."""
    return MockAuthService(
        secret_key="test_secret",
        token_expiry=timedelta(hours=1)
    )

@pytest.fixture
def mock_cache_service() -> MockCacheService:
    """Create mock cache service."""
    return MockCacheService(
        host="localhost",
        port=6379
    )

@pytest.fixture
def mock_queue_service() -> MockQueueService:
    """Create mock queue service."""
    return MockQueueService(
        host="localhost",
        port=5672
    )

@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Create test configuration."""
    return {
        "environment": "test",
        "debug": True,
        "log_level": "DEBUG",
        "timeout_ms": 1000,
        "max_retries": 3
    }

@pytest.fixture
def test_user() -> Dict[str, Any]:
    """Create test user data."""
    return {
        "id": "test_user_id",
        "username": "test_user",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["read", "write"]
    }

@pytest.fixture
def test_token(mock_auth_service, test_user) -> str:
    """Create test authentication token."""
    return mock_auth_service.create_token(test_user)

@pytest.fixture
def test_data() -> Dict[str, Any]:
    """Create test data."""
    return {
        "string_value": "test",
        "int_value": 42,
        "float_value": 3.14,
        "bool_value": True,
        "list_value": [1, 2, 3],
        "dict_value": {"key": "value"},
        "none_value": None,
        "datetime_value": datetime.now()
    }

@pytest.fixture
def test_errors() -> List[Dict[str, Any]]:
    """Create test error data."""
    return [
        {
            "code": "ERR001",
            "message": "Test error 1",
            "details": {"source": "test"}
        },
        {
            "code": "ERR002",
            "message": "Test error 2",
            "details": {"source": "test"}
        }
    ]

@pytest.fixture
def test_metrics() -> Dict[str, float]:
    """Create test metrics data."""
    return {
        "execution_time_ms": 100.0,
        "cpu_usage_percent": 50.0,
        "memory_usage_mb": 256.0,
        "error_rate": 0.01,
        "success_rate": 0.99
    }

@pytest.fixture
def test_logger() -> Generator[logging.Logger, None, None]:
    """Create test logger."""
    logger = logging.getLogger("test")
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    
    yield logger
    
    logger.setLevel(original_level)

@pytest.fixture
def test_environment() -> Generator[Dict[str, str], None, None]:
    """Create test environment variables."""
    original_env = {}
    test_env = {
        "TEST_VAR1": "value1",
        "TEST_VAR2": "value2",
        "TEST_VAR3": "value3"
    }
    
    # Save original environment variables
    for key in test_env:
        if key in os.environ:
            original_env[key] = os.environ[key]
    
    # Set test environment variables
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # Restore original environment variables
    for key in test_env:
        if key in original_env:
            os.environ[key] = original_env[key]
        else:
            del os.environ[key]

@pytest.fixture
def test_context() -> Dict[str, Any]:
    """Create test execution context."""
    return {
        "request_id": "test_request_id",
        "correlation_id": "test_correlation_id",
        "user_id": "test_user_id",
        "timestamp": datetime.now(),
        "source": "test",
        "environment": "test"
    }

@pytest.fixture
def test_files(tmp_path) -> Generator[Dict[str, str], None, None]:
    """Create temporary test files."""
    files = {
        "test_file1.txt": "Test content 1\n",
        "test_file2.txt": "Test content 2\n",
        "test_file3.txt": "Test content 3\n"
    }
    
    # Create test files
    for filename, content in files.items():
        file_path = tmp_path / filename
        file_path.write_text(content)
    
    yield {
        name: str(tmp_path / name)
        for name in files
    }

@pytest.fixture
def cleanup_files() -> Generator[None, None, None]:
    """Clean up test files after test."""
    yield
    # Cleanup will happen during teardown 