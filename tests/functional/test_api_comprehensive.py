"""
Comprehensive API functional tests with medical-grade verification
"""
import pytest
import requests
import time
import statistics
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

# Test configuration
API_BASE_URL = "http://test-api:8000"
TEST_TIMEOUT = 30  # seconds
PERFORMANCE_SAMPLES = 100
CONCURRENT_REQUESTS = 10

class TestAPIComprehensive:
    """Comprehensive API test suite with medical-grade verification"""

    @pytest.fixture(scope="class")
    def api_client(self):
        """Create API client fixture"""
        return requests.Session()

    @pytest.fixture(scope="class")
    def test_data(self) -> Dict[str, Any]:
        """Generate comprehensive test data"""
        return {
            "timestamp": datetime.now().isoformat(),
            "test_id": "comprehensive_test_001",
            "verification_level": "medical_grade",
            "test_environment": {
                "python_version": "3.9",
                "platform": "linux",
                "test_runner": "pytest"
            }
        }

    def measure_performance(self, func, *args, **kwargs) -> Dict[str, float]:
        """Measure performance metrics for a function"""
        times = []
        for _ in range(PERFORMANCE_SAMPLES):
            start_time = time.time()
            func(*args, **kwargs)
            times.append(time.time() - start_time)

        return {
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0
        }

    def test_health_check_comprehensive(self, api_client):
        """Comprehensive health check verification"""
        # Basic health check
        response = api_client.get(
            f"{API_BASE_URL}/health",
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

        # Performance measurement
        perf_metrics = self.measure_performance(
            api_client.get,
            f"{API_BASE_URL}/health",
            timeout=TEST_TIMEOUT
        )
        assert perf_metrics["mean"] < 0.1  # 100ms threshold

        # Concurrent requests
        with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
            futures = [
                executor.submit(
                    api_client.get,
                    f"{API_BASE_URL}/health",
                    timeout=TEST_TIMEOUT
                )
                for _ in range(CONCURRENT_REQUESTS)
            ]
            responses = [f.result() for f in futures]
            assert all(r.status_code == 200 for r in responses)

    def test_error_handling_comprehensive(self, api_client):
        """Comprehensive error handling verification"""
        # Test various error scenarios
        error_scenarios = [
            {
                "level": "error",
                "message": "Test error message",
                "context": {"test_id": "error_test_001"}
            },
            {
                "level": "warning",
                "message": "Test warning message",
                "context": {"test_id": "warning_test_001"}
            },
            {
                "level": "critical",
                "message": "Test critical message",
                "context": {"test_id": "critical_test_001"}
            }
        ]

        for scenario in error_scenarios:
            response = api_client.post(
                f"{API_BASE_URL}/error-handling/log",
                json=scenario,
                timeout=TEST_TIMEOUT
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "logged"
            assert "error_id" in data
            assert "logged_at" in data

        # Test error recovery
        recovery_data = {
            "error_id": "test_recovery_001",
            "action": "retry",
            "context": {"test_id": "recovery_test_001"}
        }
        response = api_client.post(
            f"{API_BASE_URL}/error-handling/recover",
            json=recovery_data,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "recovery_started"
        assert "recovery_id" in data

    def test_monitoring_comprehensive(self, api_client):
        """Comprehensive monitoring verification"""
        # Test system metrics
        response = api_client.get(
            f"{API_BASE_URL}/monitoring/system",
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        metrics = data["metrics"]
        assert all(key in metrics for key in ["cpu_usage", "memory_usage", "disk_usage"])
        assert all(0 <= value <= 100 for value in metrics.values())

        # Test application metrics
        response = api_client.get(
            f"{API_BASE_URL}/monitoring/application",
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        metrics = data["metrics"]
        assert all(key in metrics for key in [
            "requests_per_second",
            "average_response_time",
            "error_rate"
        ])

        # Test performance metrics
        response = api_client.get(
            f"{API_BASE_URL}/monitoring/performance",
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        metrics = data["metrics"]
        assert all(key in metrics for key in ["throughput", "latency", "concurrency"])
        assert all(0 <= value for value in metrics.values())

    def test_alert_configuration_comprehensive(self, api_client):
        """Comprehensive alert configuration verification"""
        # Test various alert configurations
        alert_configs = [
            {
                "metric": "cpu_usage",
                "threshold": 80.0,
                "condition": ">",
                "duration": "5m",
                "severity": "warning",
                "channels": ["email", "slack"]
            },
            {
                "metric": "memory_usage",
                "threshold": 90.0,
                "condition": ">",
                "duration": "2m",
                "severity": "critical",
                "channels": ["email", "slack", "pager"]
            },
            {
                "metric": "error_rate",
                "threshold": 0.01,
                "condition": ">",
                "duration": "1m",
                "severity": "error",
                "channels": ["email"]
            }
        ]

        for config in alert_configs:
            response = api_client.post(
                f"{API_BASE_URL}/monitoring/alerts",
                json=config,
                timeout=TEST_TIMEOUT
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "created"
            assert "alert_id" in data
            assert "created_at" in data

        # Test alert history
        response = api_client.get(
            f"{API_BASE_URL}/monitoring/alerts/history",
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert len(data["alerts"]) > 0

    def test_resource_metrics_comprehensive(self, api_client):
        """Comprehensive resource metrics verification"""
        # Test resource metrics
        response = api_client.get(
            f"{API_BASE_URL}/monitoring/resources",
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        metrics = data["metrics"]
        assert all(key in metrics for key in [
            "cpu_cores",
            "total_memory",
            "available_memory"
        ])

        # Verify resource metrics
        assert metrics["cpu_cores"] > 0
        assert metrics["total_memory"] > 0
        assert metrics["available_memory"] > 0
        assert metrics["available_memory"] <= metrics["total_memory"]

        # Test performance under load
        with ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
            futures = [
                executor.submit(
                    api_client.get,
                    f"{API_BASE_URL}/monitoring/resources",
                    timeout=TEST_TIMEOUT
                )
                for _ in range(CONCURRENT_REQUESTS)
            ]
            responses = [f.result() for f in futures]
            assert all(r.status_code == 200 for r in responses)

    def test_error_patterns_comprehensive(self, api_client):
        """Comprehensive error pattern verification"""
        # Test error pattern detection
        response = api_client.get(
            f"{API_BASE_URL}/error-handling/patterns",
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "patterns" in data
        patterns = data["patterns"]
        assert len(patterns) > 0

        # Verify pattern structure
        for pattern in patterns:
            assert all(key in pattern for key in [
                "pattern",
                "count",
                "first_seen",
                "last_seen"
            ])
            assert pattern["count"] > 0
            assert pattern["first_seen"] <= pattern["last_seen"]

    def test_aggregate_metrics_comprehensive(self, api_client):
        """Comprehensive aggregate metrics verification"""
        # Test metric aggregation
        response = api_client.get(
            f"{API_BASE_URL}/monitoring/aggregate",
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "aggregated_metrics" in data
        metrics = data["aggregated_metrics"]
        assert all(key in metrics for key in [
            "total_requests",
            "average_latency",
            "error_rate"
        ])

        # Verify metric values
        assert metrics["total_requests"] > 0
        assert 0 <= metrics["average_latency"] <= 1.0
        assert 0 <= metrics["error_rate"] <= 1.0
