"""Unit tests for mock API service."""
import pytest
import yaml
from typing import Dict, Any
from ..mocks.services.api import MockAPIService

@pytest.fixture
def config() -> Dict[str, Any]:
    """Load test configuration."""
    with open(".config/mock.yaml") as f:
        config = yaml.safe_load(f)
    return config["api"]

@pytest.fixture
def api_service(config) -> MockAPIService:
    """Create mock API service instance."""
    return MockAPIService("test_api", config)

def test_service_initialization(api_service):
    """Test service initialization."""
    assert api_service.name == "test_api"
    assert api_service._routes == {}
    assert api_service._responses == {}
    assert api_service._default_headers == {"Content-Type": "application/json"}

def test_service_start(api_service):
    """Test service start."""
    api_service.start()
    assert "/health" in api_service._routes
    assert "/api/v1/version" in api_service._routes
    assert "/api/v1/error" in api_service._routes
    assert "/api/v1/protected" in api_service._routes
    assert "/api/v1/search" in api_service._routes
    assert "/api/v1/comment" in api_service._routes

def test_service_stop(api_service):
    """Test service stop."""
    api_service.start()
    assert len(api_service._routes) > 0
    assert len(api_service._responses) > 0
    
    api_service.stop()
    assert len(api_service._routes) == 0
    assert len(api_service._responses) == 0

def test_service_reset(api_service):
    """Test service reset."""
    api_service.start()
    original_routes = dict(api_service._routes)
    original_responses = dict(api_service._responses)
    
    # Modify state
    api_service._routes.clear()
    api_service._responses.clear()
    
    # Reset
    api_service.reset()
    assert api_service._routes == original_routes
    assert api_service._responses == original_responses

def test_add_route(api_service):
    """Test adding a route."""
    route_config = {
        "methods": ["GET", "POST"],
        "auth_required": True,
        "params": {"required": ["id"]},
        "headers": {"X-Test": "test"},
        "status_code": 201
    }
    
    api_service.add_route("/test", route_config)
    route = api_service.get_route("/test")
    
    assert route is not None
    assert route["methods"] == ["GET", "POST"]
    assert route["auth_required"] is True
    assert route["params"] == {"required": ["id"]}
    assert route["headers"] == {"X-Test": "test"}
    assert route["status_code"] == 201

def test_add_responses(api_service):
    """Test adding responses."""
    responses = [
        {
            "status_code": 200,
            "headers": {"X-Test": "test"},
            "body": {"message": "Success"}
        },
        {
            "status_code": 400,
            "headers": {},
            "body": {"error": "Bad Request"}
        }
    ]
    
    api_service.add_responses("/test", responses)
    response = api_service.get_response("/test")
    
    assert response is not None
    assert response["status_code"] == 200
    assert response["headers"] == {"X-Test": "test"}
    assert response["body"] == {"message": "Success"}

def test_handle_request_not_found(api_service):
    """Test handling request for non-existent route."""
    status_code, headers, body = api_service.handle_request("/nonexistent")
    
    assert status_code == 404
    assert headers == {"Content-Type": "application/json"}
    assert body["error"] == "Not Found"

def test_handle_request_method_not_allowed(api_service):
    """Test handling request with invalid method."""
    api_service.start()
    status_code, headers, body = api_service.handle_request("/health", method="POST")
    
    assert status_code == 405
    assert headers == {"Content-Type": "application/json"}
    assert body["error"] == "Method Not Allowed"

def test_handle_request_unauthorized(api_service):
    """Test handling request requiring authentication."""
    api_service.start()
    status_code, headers, body = api_service.handle_request("/api/v1/protected")
    
    assert status_code == 401
    assert headers == {"Content-Type": "application/json"}
    assert body["error"] == "Unauthorized"

def test_handle_request_missing_params(api_service):
    """Test handling request with missing parameters."""
    api_service.start()
    status_code, headers, body = api_service.handle_request(
        "/api/v1/search",
        method="POST",
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert status_code == 400
    assert headers == {"Content-Type": "application/json"}
    assert body["error"] == "Bad Request"

def test_handle_request_success(api_service):
    """Test handling successful request."""
    api_service.start()
    status_code, headers, body = api_service.handle_request("/health")
    
    assert status_code == 200
    assert headers == {"Content-Type": "application/json"}
    assert body["status"] == "healthy"

def test_handle_request_with_auth(api_service):
    """Test handling request with valid authentication."""
    api_service.start()
    status_code, headers, body = api_service.handle_request(
        "/api/v1/protected",
        headers={"Authorization": "Bearer test_token"}
    )
    
    assert status_code == 200
    assert headers == {"Content-Type": "application/json"}
    assert body["message"] == "Access granted"

def test_handle_request_with_params(api_service):
    """Test handling request with parameters."""
    api_service.start()
    status_code, headers, body = api_service.handle_request(
        "/api/v1/search",
        method="POST",
        headers={"Authorization": "Bearer test_token"},
        params={"query": "test"}
    )
    
    assert status_code == 200
    assert headers == {"Content-Type": "application/json"}
    assert "results" in body
    assert body["total"] == 2

def test_metrics_recording(api_service):
    """Test metrics recording."""
    api_service.start()
    api_service.handle_request("/health")
    
    metrics = api_service.get_metrics()
    assert metrics["total_calls"] == 1
    assert metrics["total_errors"] == 0

def test_error_recording(api_service):
    """Test error recording."""
    api_service.start()
    api_service.handle_request("/api/v1/error")
    
    errors = api_service.get_errors()
    assert len(errors) == 0  # No actual errors, just a 500 response

def test_call_recording(api_service):
    """Test call recording."""
    api_service.start()
    api_service.handle_request("/health")
    
    calls = api_service.get_calls()
    assert len(calls) == 1
    assert calls[0]["method"] == "handle_request"
    assert calls[0]["args"] == ("/health", "GET") 