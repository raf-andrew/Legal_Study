"""
AI Feature Tests
Tests for AI-related functionality including model initialization, prompt processing,
response handling, and error cases.
"""

import os
import pytest
import requests
from datetime import datetime
from typing import Dict, Any

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 5  # seconds

def test_ai_service_health():
    """Test AI service health endpoint."""
    response = requests.get(f"{API_BASE_URL}/api/v1/ai/health", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_version" in data
    assert "last_updated" in data

def test_model_initialization():
    """Test model initialization and configuration."""
    response = requests.get(f"{API_BASE_URL}/api/v1/ai/models", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], list)
    assert len(data["models"]) > 0
    
    # Check model details
    model = data["models"][0]
    assert "name" in model
    assert "version" in model
    assert "status" in model
    assert model["status"] == "ready"

def test_prompt_processing():
    """Test prompt processing functionality."""
    test_prompts = [
        "What is the capital of France?",
        "Explain quantum computing in simple terms",
        "Write a short poem about technology"
    ]
    
    for prompt in test_prompts:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/ai/process",
            json={"text": prompt, "model": "default"},
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0

def test_prompt_validation():
    """Test prompt validation and error handling."""
    invalid_prompts = [
        "",  # Empty prompt
        " " * 1000,  # Too long
        None,  # Null prompt
        {"invalid": "format"}  # Wrong format
    ]
    
    for prompt in invalid_prompts:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/ai/process",
            json={"text": prompt, "model": "default"},
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "message" in data

def test_model_selection():
    """Test model selection and switching."""
    # Get available models
    response = requests.get(f"{API_BASE_URL}/api/v1/ai/models", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    models = response.json()["models"]
    
    # Test each model
    for model in models:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/ai/process",
            json={"text": "Test prompt", "model": model["name"]},
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "model_used" in data
        assert data["model_used"] == model["name"]

def test_response_quality():
    """Test response quality and consistency."""
    # Test multiple responses for the same prompt
    prompt = "What is 2+2?"
    responses = []
    
    for _ in range(3):
        response = requests.post(
            f"{API_BASE_URL}/api/v1/ai/process",
            json={"text": prompt, "model": "default"},
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        responses.append(data["response"])
    
    # Check response consistency
    assert len(set(responses)) > 0  # Should have at least one unique response
    assert all(len(r) > 0 for r in responses)  # All responses should be non-empty

def test_error_handling():
    """Test error handling in AI service."""
    # Test invalid model
    response = requests.post(
        f"{API_BASE_URL}/api/v1/ai/process",
        json={"text": "Test prompt", "model": "nonexistent_model"},
        timeout=TEST_TIMEOUT
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "message" in data
    
    # Test service unavailable
    response = requests.get(f"{API_BASE_URL}/api/v1/ai/health", timeout=0.1)
    assert response.status_code == 504
    data = response.json()
    assert "error" in data
    assert "message" in data

def test_rate_limiting():
    """Test rate limiting functionality."""
    # Make multiple requests quickly
    responses = []
    for _ in range(10):
        response = requests.post(
            f"{API_BASE_URL}/api/v1/ai/process",
            json={"text": "Test prompt", "model": "default"},
            timeout=TEST_TIMEOUT
        )
        responses.append(response)
    
    # Check rate limit headers
    assert "X-RateLimit-Limit" in responses[-1].headers
    assert "X-RateLimit-Remaining" in responses[-1].headers
    assert "X-RateLimit-Reset" in responses[-1].headers
    
    # Verify some requests were rate limited
    assert any(r.status_code == 429 for r in responses)

def test_concurrent_requests():
    """Test handling of concurrent requests."""
    import concurrent.futures
    
    def make_request():
        return requests.post(
            f"{API_BASE_URL}/api/v1/ai/process",
            json={"text": "Test prompt", "model": "default"},
            timeout=TEST_TIMEOUT
        )
    
    # Make 5 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        responses = [f.result() for f in futures]
    
    # Check all requests were handled
    assert all(r.status_code in [200, 429] for r in responses)
    assert any(r.status_code == 200 for r in responses)

def test_model_metrics():
    """Test model performance metrics."""
    response = requests.get(f"{API_BASE_URL}/api/v1/ai/metrics", timeout=TEST_TIMEOUT)
    assert response.status_code == 200
    data = response.json()
    
    assert "metrics" in data
    metrics = data["metrics"]
    
    # Check essential metrics
    assert "response_time" in metrics
    assert "requests_per_minute" in metrics
    assert "error_rate" in metrics
    assert "model_usage" in metrics
    
    # Verify metric values
    assert metrics["response_time"] >= 0
    assert metrics["requests_per_minute"] >= 0
    assert 0 <= metrics["error_rate"] <= 1
    assert isinstance(metrics["model_usage"], dict) 