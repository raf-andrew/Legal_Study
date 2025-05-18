"""Mock API service implementation."""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from ..base import BaseMockService

logger = logging.getLogger(__name__)

class MockAPIService(BaseMockService):
    """Mock API service."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self._routes: Dict[str, Dict[str, Any]] = {}
        self._responses: Dict[str, List[Dict[str, Any]]] = {}
        self._default_headers = {
            "Content-Type": "application/json"
        }

    def _start(self):
        """Start the mock API service."""
        self._load_routes()
        self._load_responses()

    def _stop(self):
        """Stop the mock API service."""
        self._routes.clear()
        self._responses.clear()

    def _reset(self):
        """Reset the mock API service."""
        super()._reset()
        self._routes.clear()
        self._responses.clear()
        self._load_routes()
        self._load_responses()

    def _load_routes(self):
        """Load API routes from configuration."""
        routes = self.state.config.get("routes", {})
        for path, config in routes.items():
            self.add_route(path, config)

    def _load_responses(self):
        """Load API responses from configuration."""
        responses = self.state.config.get("responses", {})
        for path, response_list in responses.items():
            self.add_responses(path, response_list)

    def add_route(self, path: str, config: Dict[str, Any]):
        """Add an API route."""
        self._routes[path] = {
            "methods": config.get("methods", ["GET"]),
            "auth_required": config.get("auth_required", False),
            "params": config.get("params", {}),
            "headers": config.get("headers", {}),
            "status_code": config.get("status_code", 200)
        }
        self.logger.info(f"Added route: {path}")

    def add_responses(self, path: str, responses: List[Dict[str, Any]]):
        """Add responses for a route."""
        self._responses[path] = responses
        self.logger.info(f"Added {len(responses)} responses for route: {path}")

    def get_route(self, path: str) -> Optional[Dict[str, Any]]:
        """Get route configuration."""
        return self._routes.get(path)

    def get_response(self, path: str, index: int = 0) -> Optional[Dict[str, Any]]:
        """Get response for a route."""
        responses = self._responses.get(path, [])
        if not responses:
            return None
        return responses[index % len(responses)]

    def handle_request(self, path: str, method: str = "GET", 
                      params: Optional[Dict[str, Any]] = None,
                      headers: Optional[Dict[str, Any]] = None,
                      body: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any], Dict[str, Any]]:
        """Handle an API request."""
        try:
            # Record the request
            self.state.record_call("handle_request", (path, method), {
                "params": params,
                "headers": headers,
                "body": body
            })

            # Get route configuration
            route = self.get_route(path)
            if not route:
                return 404, self._default_headers, {
                    "error": "Not Found",
                    "message": f"Route not found: {path}"
                }

            # Check method
            if method not in route["methods"]:
                return 405, self._default_headers, {
                    "error": "Method Not Allowed",
                    "message": f"Method not allowed: {method}"
                }

            # Check authentication
            if route["auth_required"]:
                auth_header = headers.get("Authorization") if headers else None
                if not auth_header:
                    return 401, self._default_headers, {
                        "error": "Unauthorized",
                        "message": "Authentication required"
                    }

            # Validate parameters
            if params:
                required_params = route["params"].get("required", [])
                for param in required_params:
                    if param not in params:
                        return 400, self._default_headers, {
                            "error": "Bad Request",
                            "message": f"Missing required parameter: {param}"
                        }

            # Get response
            response = self.get_response(path)
            if not response:
                return 500, self._default_headers, {
                    "error": "Internal Server Error",
                    "message": "No response configured"
                }

            # Return response
            status_code = response.get("status_code", route["status_code"])
            headers = {**self._default_headers, **response.get("headers", {})}
            body = response.get("body", {})

            return status_code, headers, body

        except Exception as e:
            self.state.record_error(e, {
                "path": path,
                "method": method,
                "params": params,
                "headers": headers,
                "body": body
            })
            return 500, self._default_headers, {
                "error": "Internal Server Error",
                "message": str(e)
            }

    def _configure(self, config: Dict[str, Any]):
        """Configure the mock API service."""
        super()._configure(config)
        self._reset()  # Reload routes and responses 