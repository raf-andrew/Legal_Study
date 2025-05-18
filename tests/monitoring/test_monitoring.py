"""
Monitoring Tests
Tests for system and application monitoring functionality.
"""

import os
import pytest
import requests
from datetime import datetime
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 5  # seconds

def test_monitoring_service_health():
    """Test monitoring service health endpoint."""
    response = requests.get(f"{API_BASE_URL}/api/v1/monitoring/health", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "last_updated" in data

def test_system_metrics():
    """Test system metrics collection."""
    response = requests.get(f"{API_BASE_URL}/api/v1/monitoring/system", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    
    assert "metrics" in data
    metrics = data["metrics"]
    
    # Check essential system metrics
    assert "cpu_usage" in metrics
    assert "memory_usage" in metrics
    assert "disk_usage" in metrics
    assert "network_traffic" in metrics
    
    # Verify metric values
    assert 0 <= metrics["cpu_usage"] <= 100
    assert 0 <= metrics["memory_usage"] <= 100
    assert 0 <= metrics["disk_usage"] <= 100
    assert isinstance(metrics["network_traffic"], dict)

def test_application_metrics():
    """Test application metrics collection."""
    response = requests.get(f"{API_BASE_URL}/api/v1/monitoring/application", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    
    assert "metrics" in data
    metrics = data["metrics"]
    
    # Check essential application metrics
    assert "request_count" in metrics
    assert "response_time" in metrics
    assert "error_rate" in metrics
    assert "active_users" in metrics
    
    # Verify metric values
    assert metrics["request_count"] >= 0
    assert metrics["response_time"] >= 0
    assert 0 <= metrics["error_rate"] <= 1
    assert metrics["active_users"] >= 0

def test_performance_metrics():
    """Test performance metrics collection."""
    response = requests.get(f"{API_BASE_URL}/api/v1/monitoring/performance", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    
    assert "metrics" in data
    metrics = data["metrics"]
    
    # Check essential performance metrics
    assert "throughput" in metrics
    assert "latency" in metrics
    assert "concurrent_requests" in metrics
    assert "queue_size" in metrics
    
    # Verify metric values
    assert metrics["throughput"] >= 0
    assert metrics["latency"] >= 0
    assert metrics["concurrent_requests"] >= 0
    assert metrics["queue_size"] >= 0

def test_resource_metrics():
    """Test resource usage metrics."""
    response = requests.get(f"{API_BASE_URL}/api/v1/monitoring/resources", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    
    assert "metrics" in data
    metrics = data["metrics"]
    
    # Check essential resource metrics
    assert "cpu_cores" in metrics
    assert "memory_total" in metrics
    assert "disk_total" in metrics
    assert "network_interfaces" in metrics
    
    # Verify metric values
    assert metrics["cpu_cores"] > 0
    assert metrics["memory_total"] > 0
    assert metrics["disk_total"] > 0
    assert isinstance(metrics["network_interfaces"], list)

def test_alert_configuration():
    """Test alert configuration functionality."""
    # Test alert settings
    test_alert = {
        "metric": "cpu_usage",
        "threshold": 80,
        "condition": ">",
        "duration": "5m",
        "severity": "warning",
        "channels": ["email", "slack"]
    }
    
    response = requests.post(
        f"{API_BASE_URL}/api/v1/monitoring/alerts",
        json=test_alert,
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    assert "alert_id" in data

def test_alert_history():
    """Test alert history functionality."""
    response = requests.get(
        f"{API_BASE_URL}/api/v1/monitoring/alerts/history",
        params={"timeframe": "24h"},
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert isinstance(data["alerts"], list)
    
    # Check alert details
    if len(data["alerts"]) > 0:
        alert = data["alerts"][0]
        assert "id" in alert
        assert "metric" in alert
        assert "threshold" in alert
        assert "triggered_at" in alert
        assert "resolved_at" in alert

def test_metric_aggregation():
    """Test metric aggregation functionality."""
    response = requests.get(
        f"{API_BASE_URL}/api/v1/monitoring/aggregate",
        params={
            "metric": "cpu_usage",
            "interval": "5m",
            "timeframe": "1h"
        },
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    assert "aggregated_metrics" in data
    assert isinstance(data["aggregated_metrics"], list)
    
    # Check aggregation details
    if len(data["aggregated_metrics"]) > 0:
        metric = data["aggregated_metrics"][0]
        assert "timestamp" in metric
        assert "value" in metric
        assert "count" in metric

def test_metric_validation():
    """Test metric validation and error handling."""
    invalid_metrics = [
        {},  # Empty metric
        {"name": "invalid"},  # Invalid metric name
        {"value": 100},  # Missing metric name
        {"name": "cpu_usage", "value": "invalid"}  # Invalid value type
    ]
    
    for metric in invalid_metrics:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/monitoring/metrics",
            json=metric,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "message" in data

def test_metric_rate_limiting():
    """Test metric collection rate limiting."""
    # Make multiple requests quickly
    responses = []
    for _ in range(10):
        response = requests.post(
            f"{API_BASE_URL}/api/v1/monitoring/metrics",
            json={
                "name": "test_metric",
                "value": 100
            },
            timeout=TEST_TIMEOUT
        )
        responses.append(response)
    
    # Check rate limit headers
    assert "X-RateLimit-Limit" in responses[-1].headers
    assert "X-RateLimit-Remaining" in responses[-1].headers
    assert "X-RateLimit-Reset" in responses[-1].headers
    
    # Verify some requests were rate limited
    assert any(r.status_code == 429 for r in responses)

def test_metric_retention():
    """Test metric data retention."""
    response = requests.get(
        f"{API_BASE_URL}/api/v1/monitoring/retention",
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 200
    data = response.json()
    
    assert "retention_policies" in data
    policies = data["retention_policies"]
    
    # Check policy details
    assert isinstance(policies, dict)
    assert "raw_metrics" in policies
    assert "aggregated_metrics" in policies
    assert "alerts" in policies
    
    # Verify policy values
    assert policies["raw_metrics"] > 0
    assert policies["aggregated_metrics"] > 0
    assert policies["alerts"] > 0 