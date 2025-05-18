import pytest
import yaml
import os
from pathlib import Path

def test_openapi_spec_exists():
    """Test that the OpenAPI specification file exists."""
    api_dir = Path(__file__).parent.parent.parent / '.api'
    assert (api_dir / 'openapi.yaml').exists(), "OpenAPI specification file not found"

def test_openapi_spec_valid():
    """Test that the OpenAPI specification is valid YAML."""
    api_dir = Path(__file__).parent.parent.parent / '.api'
    with open(api_dir / 'openapi.yaml', 'r') as f:
        spec = yaml.safe_load(f)
        assert 'openapi' in spec, "OpenAPI version not specified"
        assert 'info' in spec, "API info not specified"
        assert 'paths' in spec, "API paths not specified"

def test_api_documentation_complete():
    """Test that all required API documentation files exist."""
    api_dir = Path(__file__).parent.parent.parent / '.api'
    required_files = [
        'README.md',
        'api_documentation_checklist.md',
        'endpoint_checklist.md',
        'health_check_api.md',
        'openapi.yaml'
    ]
    for file in required_files:
        assert (api_dir / file).exists(), f"Required API documentation file {file} not found"

def test_api_versioning():
    """Test that API versioning is properly documented."""
    api_dir = Path(__file__).parent.parent.parent / '.api'
    with open(api_dir / 'openapi.yaml', 'r') as f:
        spec = yaml.safe_load(f)
        assert 'servers' in spec, "API servers not specified"
        assert any('/v1' in path for path in spec.get('paths', {})), "No v1 API endpoints found"

def test_api_security():
    """Test that API security is properly documented."""
    api_dir = Path(__file__).parent.parent.parent / '.api'
    with open(api_dir / 'openapi.yaml', 'r') as f:
        spec = yaml.safe_load(f)
        assert 'securitySchemes' in spec.get('components', {}), "Security schemes not specified"
        assert 'BearerAuth' in spec['components']['securitySchemes'], "Bearer authentication not specified"

def test_api_error_handling():
    """Test that API error handling is properly documented."""
    api_dir = Path(__file__).parent.parent.parent / '.api'
    with open(api_dir / 'openapi.yaml', 'r') as f:
        spec = yaml.safe_load(f)
        assert 'Error' in spec.get('components', {}).get('schemas', {}), "Error schema not specified"
        assert 'ErrorResponse' in spec.get('components', {}).get('schemas', {}), "Error response schema not specified"

def test_api_health_check():
    """Test that API health check endpoint is properly documented."""
    api_dir = Path(__file__).parent.parent.parent / '.api'
    with open(api_dir / 'openapi.yaml', 'r') as f:
        spec = yaml.safe_load(f)
        assert '/health' in spec.get('paths', {}), "Health check endpoint not specified"
        health_endpoint = spec['paths']['/health']
        assert 'get' in health_endpoint, "Health check endpoint should be GET"
        assert '200' in health_endpoint['get']['responses'], "Health check success response not specified" 