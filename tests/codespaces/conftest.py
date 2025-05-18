import pytest
import docker
from pathlib import Path
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/codespaces_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

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

def pytest_configure(config):
    """Configure pytest for Codespaces tests."""
    # Register custom markers
    config.addinivalue_line("markers", "codespaces: Codespaces infrastructure tests")
    config.addinivalue_line("markers", "environment: Environment setup tests")
    config.addinivalue_line("markers", "configuration: Configuration tests")
    config.addinivalue_line("markers", "deployment: Deployment tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "cleanup: Cleanup tests")

# Disable or override base_url fixture for Codespaces tests
@pytest.fixture(scope="session", autouse=True)
def base_url():
    # Prevent pytest-base-url/pytest-tornado from injecting their base_url fixture
    return None
