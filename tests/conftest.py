import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
import os
import logging
from datetime import datetime
import sqlite3
import tempfile
from dotenv import load_dotenv
from app.core.database import Base, get_db
from pydantic_settings import BaseSettings
import sys
from pathlib import Path
import docker

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)

@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    settings.DEBUG = True
    settings.API_V1_STR = "/api/v1"
    return settings

@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    conn = sqlite3.connect(db_path)

    # Create test tables
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    yield conn

    # Clean up
    conn.close()
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Create logs directory if it doesn't exist
    os.makedirs('.logs', exist_ok=True)
    os.makedirs('.errors', exist_ok=True)

    # Log test start
    logger.info(f"Starting test session at {datetime.now()}")

    yield

    # Log test end
    logger.info(f"Ending test session at {datetime.now()}")

@pytest.fixture(scope="function")
def error_logger():
    """Create a logger for test errors."""
    error_logger = logging.getLogger('test_errors')
    error_logger.setLevel(logging.ERROR)

    # Create error log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_handler = logging.FileHandler(f'.errors/test_errors_{timestamp}.log')
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    error_logger.addHandler(error_handler)

    return error_logger

def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest file
    after command line options have been parsed.
    """
    # Load environment variables from .config/environment/env.dev
    load_dotenv('.config/environment/env.dev')

    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "security: Security tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "smoke: Smoke tests")
    config.addinivalue_line("markers", "acid: ACID compliance tests")
    config.addinivalue_line("markers", "chaos: Chaos testing scenarios")

@pytest.fixture(scope="session")
def test_environment():
    """Fixture to verify and provide test environment configuration"""
    return {
        'app_name': os.getenv('APP_NAME'),
        'debug': os.getenv('DEBUG'),
        'testing': os.getenv('TESTING'),
        'api_version': os.getenv('API_VERSION'),
        'database_url': os.getenv('TEST_DATABASE_URL')
    }

@pytest.fixture(scope="session")
def db():
    """Create a fresh database for each test session"""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """Create a test client for each test function"""
    def override_get_db():
        try:
            yield db
        finally:
            db.rollback()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def cleanup_database(db):
    """Clean up database after each test."""
    yield
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())

@pytest.fixture(scope="session")
def api_client():
    """Fixture to provide a test API client"""
    # TODO: Implement API client setup
    yield
    # Cleanup after all tests

@pytest.fixture(scope="function")
def test_data():
    """Fixture to provide test data"""
    return {
        'sample_user': {
            'username': 'test_user',
            'email': 'test@example.com',
            'password': 'test_password'
        },
        'sample_document': {
            'title': 'Test Document',
            'content': 'Test Content'
        }
    }

@pytest.fixture(scope="function")
def chaos_network_conditions():
    """Fixture to simulate various network conditions for chaos testing."""
    import socket
    original_socket = socket.socket

    def delayed_socket(*args, **kwargs):
        import time
        import random
        time.sleep(random.uniform(0.1, 2.0))  # Random delay
        return original_socket(*args, **kwargs)

    socket.socket = delayed_socket
    yield
    socket.socket = original_socket

@pytest.fixture(scope="function")
def chaos_database_conditions(db):
    """Fixture to simulate database issues for chaos testing."""
    def execute_with_chaos(*args, **kwargs):
        import random
        if random.random() < 0.2:  # 20% chance of failure
            raise Exception("Simulated database error")
        return db.execute(*args, **kwargs)

    original_execute = db.execute
    db.execute = execute_with_chaos
    yield db
    db.execute = original_execute

@pytest.fixture(scope="function")
def acid_transaction_checker(db):
    """Fixture to verify ACID properties of database transactions."""
    from contextlib import contextmanager
    import threading

    @contextmanager
    def transaction_checker():
        start_time = datetime.now()
        thread_id = threading.get_ident()

        try:
            yield
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            db.rollback()
            raise
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Transaction completed in {duration}s on thread {thread_id}")

    return transaction_checker

@pytest.fixture(scope="function")
def concurrent_transactions(db):
    """Fixture to test concurrent database access."""
    from concurrent.futures import ThreadPoolExecutor
    import functools

    def run_concurrent(func, times=3):
        with ThreadPoolExecutor(max_workers=times) as executor:
            futures = [executor.submit(func) for _ in range(times)]
            return [f.result() for f in futures]

    return run_concurrent

@pytest.fixture(scope="session")
def performance_metrics():
    """Fixture to track performance metrics during tests."""
    from collections import defaultdict
    import time

    metrics = defaultdict(list)

    def record_metric(name, value):
        metrics[name].append({
            'value': value,
            'timestamp': time.time()
        })

    yield record_metric

    # Log summary statistics
    for name, values in metrics.items():
        avg_value = sum(v['value'] for v in values) / len(values)
        logger.info(f"Performance metric {name}: avg={avg_value:.2f}")

@pytest.fixture(scope="function")
def mock_external_services():
    """Fixture to mock external service dependencies."""
    class MockResponse:
        def __init__(self, status_code=200, json_data=None):
            self.status_code = status_code
            self._json_data = json_data or {}

        def json(self):
            return self._json_data

    return MockResponse

@pytest.fixture(scope="function")
def auth_headers(client, db):
    """Create authentication headers for testing authenticated endpoints"""
    # Register test user
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPass123!",
            "password_confirmation": "TestPass123!"
        }
    )

    # Login to get token
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPass123!"
        }
    )
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="session")
def test_data_dir():
    """Fixture to provide the test data directory."""
    data_dir = project_root / "tests" / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

@pytest.fixture(scope="session")
def test_output_dir():
    """Fixture to provide the test output directory."""
    output_dir = project_root / "tests" / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir

@pytest.fixture(scope="session")
def test_log_dir():
    """Fixture to provide the test log directory."""
    log_dir = project_root / "tests" / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir

@pytest.fixture(scope="function")
def temp_file(test_output_dir):
    """Fixture to provide a temporary file for testing."""
    with tempfile.NamedTemporaryFile(dir=test_output_dir, delete=False) as f:
        yield f.name
    os.unlink(f.name)

@pytest.fixture(scope="function")
def mock_env(monkeypatch):
    """Fixture to provide a mock environment for testing."""
    def mock_getenv(key, default=None):
        mock_env_vars = {
            "TEST_ENV": "test",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG"
        }
        return mock_env_vars.get(key, default)

    monkeypatch.setattr(os, "getenv", mock_getenv)
    return mock_getenv

@pytest.fixture(scope="function")
def mock_logger():
    """Fixture to provide a mock logger for testing."""
    import logging
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.DEBUG)
    return logger

@pytest.fixture(scope="session")
def docker_client():
    """Create a Docker client for testing."""
    return docker.from_env()

@pytest.fixture(scope="session")
def test_workspace():
    """Create a test workspace directory."""
    workspace = Path("test_workspace")
    workspace.mkdir(exist_ok=True)
    yield workspace
    # Cleanup
    for item in workspace.glob("*"):
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            for subitem in item.glob("**/*"):
                if subitem.is_file():
                    subitem.unlink()
            item.rmdir()
    workspace.rmdir()

@pytest.fixture(scope="session")
def test_codespace(docker_client):
    """Create a test codespace container."""
    container = docker_client.containers.run(
        "mcr.microsoft.com/vscode/devcontainers/python:3.9",
        name="test_codespace",
        detach=True,
        remove=True,
        environment={
            "PYTHONPATH": "/workspace",
            "TEST_ENV": "true"
        }
    )
    yield container
    # Cleanup
    container.stop()
    container.remove()
