import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.smoke
def test_read_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Legal Study API"}

@pytest.mark.smoke
def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.smoke
def test_api_version():
    """Test the API version endpoint."""
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert "version" in response.json()

@pytest.mark.smoke
def test_docs_available():
    """Test that API documentation is available."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

@pytest.mark.smoke
def test_redoc_available():
    """Test that ReDoc documentation is available."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

@pytest.mark.smoke
def test_invalid_endpoint():
    """Test handling of invalid endpoints."""
    response = client.get("/invalid")
    assert response.status_code == 404
    assert "detail" in response.json()

@pytest.mark.smoke
def test_error_handling():
    """Test error handling."""
    response = client.get("/api/v1/error")
    assert response.status_code == 500
    assert "detail" in response.json() 