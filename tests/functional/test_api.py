"""
Functional tests for API endpoints
"""
import pytest
import requests
from datetime import datetime
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://test-api:8000"
TEST_TIMEOUT = 30  # seconds

class TestAPI:
    """API functional test suite"""

    @pytest.fixture(scope="class")
    def api_client(self):
        """Create API client fixture"""
        return requests.Session()

    @pytest.fixture(scope="class")
    def test_data(self) -> Dict[str, Any]:
        """Generate test data"""
        return {
            "timestamp": datetime.now().isoformat(),
            "test_id": "functional_test_001"
        }

    def test_health_check(self, api_client):
        """Test API health check endpoint"""
        response = api_client.get(
            f"{API_BASE_URL}/health",
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_error_handling(self, api_client):
        """Test error handling endpoints"""
        # Test error logging
        error_data = {
            "level": "error",
            "message": "Test error message",
            "context": {
                "test_id": "error_test_001",
                "timestamp": datetime.now().isoformat()
            }
        }

        response = api_client.post(
            f"{API_BASE_URL}/error-handling/log",
            json=error_data,
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "logged"
        assert "error_id" in data
        assert "logged_at" in data

    def test_monitoring_metrics(self, api_client):
        """Test monitoring endpoints"""
        # Test system metrics
        response = api_client.get(
            f"{API_BASE_URL}/monitoring/system",
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        metrics = data["metrics"]
        assert "cpu_usage" in metrics
        assert "memory_usage" in metrics
        assert "disk_usage" in metrics

        # Test application metrics
        response = api_client.get(
            f"{API_BASE_URL}/monitoring/application",
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        metrics = data["metrics"]
        assert "requests_per_second" in metrics
        assert "average_response_time" in metrics
        assert "error_rate" in metrics

    def test_alert_configuration(self, api_client):
        """Test alert configuration"""
        alert_config = {
            "metric": "cpu_usage",
            "threshold": 80.0,
            "condition": ">",
            "duration": "5m",
            "severity": "warning",
            "channels": ["email", "slack"]
        }

        response = api_client.post(
            f"{API_BASE_URL}/monitoring/alerts",
            json=alert_config,
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert "alert_id" in data
        assert "created_at" in data

    def test_performance_metrics(self, api_client):
        """Test performance metrics collection"""
        response = api_client.get(
            f"{API_BASE_URL}/monitoring/performance",
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        metrics = data["metrics"]
        assert "throughput" in metrics
        assert "latency" in metrics
        assert "concurrency" in metrics

        # Verify metrics are within acceptable ranges
        assert 0 <= metrics["throughput"] <= 10000
        assert 0 <= metrics["latency"] <= 1.0
        assert 0 <= metrics["concurrency"] <= 100

    def test_resource_metrics(self, api_client):
        """Test resource usage metrics"""
        response = api_client.get(
            f"{API_BASE_URL}/monitoring/resources",
            timeout=TEST_TIMEOUT
        )

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        metrics = data["metrics"]
        assert "cpu_cores" in metrics
        assert "total_memory" in metrics
        assert "available_memory" in metrics

        # Verify resource metrics
        assert metrics["cpu_cores"] > 0
        assert metrics["total_memory"] > 0
        assert metrics["available_memory"] > 0
        assert metrics["available_memory"] <= metrics["total_memory"]
