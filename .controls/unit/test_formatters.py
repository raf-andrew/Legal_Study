"""Unit tests for health check formatters."""

import json
import yaml
from datetime import datetime
from typing import Dict, Any

import pytest
from ..commands.health.formatters.json import JSONFormatter
from ..commands.health.formatters.yaml import YAMLFormatter
from ..commands.health.formatters.text import TextFormatter

@pytest.fixture
def sample_data() -> Dict[str, Any]:
    """Create sample health check data."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "services": {
                "status": "healthy",
                "details": {
                    "healthy": True,
                    "services": {
                        "api": {
                            "status": "healthy",
                            "started_at": datetime.now().isoformat(),
                            "total_calls": 10,
                            "total_errors": 0
                        }
                    }
                }
            }
        },
        "report": {
            "summary": {
                "total_checks": 1,
                "healthy_checks": 1,
                "unhealthy_checks": 0,
                "error_checks": 0,
                "health_percentage": 100.0
            },
            "recommendations": []
        }
    }

@pytest.fixture
def error_data() -> str:
    """Create sample error message."""
    return "Test error message"

def test_json_formatter_output(sample_data):
    """Test JSON formatter output."""
    formatter = JSONFormatter()
    output = formatter.format_output(sample_data)
    
    # Verify output is valid JSON
    data = json.loads(output)
    assert data["status"] == sample_data["status"]
    assert data["timestamp"] == sample_data["timestamp"]
    assert "checks" in data
    assert "report" in data

def test_json_formatter_error(error_data):
    """Test JSON formatter error output."""
    formatter = JSONFormatter()
    output = formatter.format_error(error_data)
    
    # Verify error output
    data = json.loads(output)
    assert data["status"] == "error"
    assert data["error"] == error_data

def test_yaml_formatter_output(sample_data):
    """Test YAML formatter output."""
    formatter = YAMLFormatter()
    output = formatter.format_output(sample_data)
    
    # Verify output is valid YAML
    data = yaml.safe_load(output)
    assert data["status"] == sample_data["status"]
    assert data["timestamp"] == sample_data["timestamp"]
    assert "checks" in data
    assert "report" in data

def test_yaml_formatter_error(error_data):
    """Test YAML formatter error output."""
    formatter = YAMLFormatter()
    output = formatter.format_error(error_data)
    
    # Verify error output
    data = yaml.safe_load(output)
    assert data["status"] == "error"
    assert data["error"] == error_data

def test_text_formatter_output(sample_data):
    """Test text formatter output."""
    formatter = TextFormatter()
    output = formatter.format_output(sample_data)
    
    # Verify output structure
    assert "Health Check Report" in output
    assert f"Status: {sample_data['status']}" in output
    assert f"Timestamp: {sample_data['timestamp']}" in output
    assert "Services:" in output
    assert "Report Summary:" in output
    assert "Recommendations:" in output

def test_text_formatter_error(error_data):
    """Test text formatter error output."""
    formatter = TextFormatter()
    output = formatter.format_error(error_data)
    
    # Verify error output
    assert "Health Check Error" in output
    assert "Status: error" in output
    assert f"Error: {error_data}" in output

def test_formatter_with_complex_data():
    """Test formatters with complex data structure."""
    data = {
        "status": "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "services": {
                "status": "unhealthy",
                "details": {
                    "healthy": False,
                    "services": {
                        "api": {
                            "status": "healthy",
                            "started_at": datetime.now().isoformat(),
                            "total_calls": 10,
                            "total_errors": 0
                        },
                        "database": {
                            "status": "unhealthy",
                            "started_at": datetime.now().isoformat(),
                            "total_calls": 5,
                            "total_errors": 2,
                            "errors": [
                                {"error": "Connection failed", "timestamp": datetime.now().isoformat()}
                            ]
                        }
                    }
                }
            }
        },
        "report": {
            "summary": {
                "total_checks": 2,
                "healthy_checks": 1,
                "unhealthy_checks": 1,
                "error_checks": 0,
                "health_percentage": 50.0
            },
            "recommendations": [
                "Check database connection settings",
                "Verify database service is running"
            ]
        }
    }
    
    # Test JSON formatter
    json_output = JSONFormatter().format_output(data)
    assert json.loads(json_output)["status"] == "unhealthy"
    
    # Test YAML formatter
    yaml_output = YAMLFormatter().format_output(data)
    assert yaml.safe_load(yaml_output)["status"] == "unhealthy"
    
    # Test text formatter
    text_output = TextFormatter().format_output(data)
    assert "Status: unhealthy" in text_output
    assert "Check database connection settings" in text_output 