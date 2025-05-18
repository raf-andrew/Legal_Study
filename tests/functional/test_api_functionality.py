"""
Comprehensive functional test suite for API endpoints.
Follows medical-grade verification standards with detailed reporting.
"""
import pytest
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import requests
from fastapi.testclient import TestClient
import logging

from sniffing.mcp.server.routes import app

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test client
client = TestClient(app)

# Test data directory
TEST_DATA_DIR = Path("tests/functional/test_data")
TEST_REPORTS_DIR = Path("reports/functional_tests")

# Ensure directories exist
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)
TEST_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

class TestReport:
    """Medical-grade test report generator."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = datetime.now()
        self.results: List[Dict] = []
        self.verification_steps: List[Dict] = []

    def add_verification_step(self, step: str, status: str, details: Dict):
        """Add a verification step with detailed status."""
        self.verification_steps.append({
            "step": step,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })

    def add_result(self, endpoint: str, method: str, status_code: int, response: Dict):
        """Add a test result with full details."""
        self.results.append({
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response": response,
            "timestamp": datetime.now().isoformat()
        })

    def save_report(self):
        """Save detailed test report."""
        report = {
            "test_name": self.test_name,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "verification_steps": self.verification_steps,
            "results": self.results,
            "summary": {
                "total_steps": len(self.verification_steps),
                "passed_steps": sum(1 for step in self.verification_steps if step["status"] == "passed"),
                "failed_steps": sum(1 for step in self.verification_steps if step["status"] == "failed")
            }
        }

        report_file = TEST_REPORTS_DIR / f"{self.test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        return report_file

@pytest.mark.functional
def test_ai_endpoints():
    """Test AI-related endpoints with comprehensive verification."""
    report = TestReport("ai_endpoints_test")

    # Test /ai/models endpoint
    report.add_verification_step(
        "Verify /ai/models endpoint availability",
        "in_progress",
        {"endpoint": "/ai/models", "method": "GET"}
    )

    response = client.get("/ai/models")
    assert response.status_code == 200
    data = response.json()

    report.add_result("/ai/models", "GET", response.status_code, data)
    report.add_verification_step(
        "Verify /ai/models response structure",
        "passed" if "models" in data else "failed",
        {"expected": "models key in response", "actual": list(data.keys())}
    )

    # Test /ai/health endpoint
    report.add_verification_step(
        "Verify /ai/health endpoint",
        "in_progress",
        {"endpoint": "/ai/health", "method": "GET"}
    )

    response = client.get("/ai/health")
    assert response.status_code == 200
    data = response.json()

    report.add_result("/ai/health", "GET", response.status_code, data)
    report.add_verification_step(
        "Verify /ai/health response structure",
        "passed" if all(k in data for k in ["status", "timestamp", "version"]) else "failed",
        {"expected": ["status", "timestamp", "version"], "actual": list(data.keys())}
    )

    # Test /ai/process endpoint
    test_prompt = {"text": "Test prompt", "model": "gpt-4"}
    report.add_verification_step(
        "Verify /ai/process endpoint",
        "in_progress",
        {"endpoint": "/ai/process", "method": "POST", "payload": test_prompt}
    )

    response = client.post("/ai/process", json=test_prompt)
    assert response.status_code == 200
    data = response.json()

    report.add_result("/ai/process", "POST", response.status_code, data)
    report.add_verification_step(
        "Verify /ai/process response structure",
        "passed" if all(k in data for k in ["response", "model", "processing_time"]) else "failed",
        {"expected": ["response", "model", "processing_time"], "actual": list(data.keys())}
    )

    # Save report
    report_file = report.save_report()
    logger.info(f"AI endpoints test report saved to {report_file}")

@pytest.mark.functional
def test_error_handling_endpoints():
    """Test error handling endpoints with comprehensive verification."""
    report = TestReport("error_handling_endpoints_test")

    # Test /error-handling/health endpoint
    report.add_verification_step(
        "Verify /error-handling/health endpoint",
        "in_progress",
        {"endpoint": "/error-handling/health", "method": "GET"}
    )

    response = client.get("/error-handling/health")
    assert response.status_code == 200
    data = response.json()

    report.add_result("/error-handling/health", "GET", response.status_code, data)
    report.add_verification_step(
        "Verify /error-handling/health response structure",
        "passed" if all(k in data for k in ["status", "timestamp", "version"]) else "failed",
        {"expected": ["status", "timestamp", "version"], "actual": list(data.keys())}
    )

    # Test /error-handling/log endpoint
    test_error = {
        "level": "error",
        "message": "Test error message",
        "context": {"test": "context"}
    }
    report.add_verification_step(
        "Verify /error-handling/log endpoint",
        "in_progress",
        {"endpoint": "/error-handling/log", "method": "POST", "payload": test_error}
    )

    response = client.post("/error-handling/log", json=test_error)
    assert response.status_code == 200
    data = response.json()

    report.add_result("/error-handling/log", "POST", response.status_code, data)
    report.add_verification_step(
        "Verify /error-handling/log response structure",
        "passed" if all(k in data for k in ["status", "error_id", "logged_at"]) else "failed",
        {"expected": ["status", "error_id", "logged_at"], "actual": list(data.keys())}
    )

    # Save report
    report_file = report.save_report()
    logger.info(f"Error handling endpoints test report saved to {report_file}")

@pytest.mark.functional
def test_monitoring_endpoints():
    """Test monitoring endpoints with comprehensive verification."""
    report = TestReport("monitoring_endpoints_test")

    # Test /monitoring/health endpoint
    report.add_verification_step(
        "Verify /monitoring/health endpoint",
        "in_progress",
        {"endpoint": "/monitoring/health", "method": "GET"}
    )

    response = client.get("/monitoring/health")
    assert response.status_code == 200
    data = response.json()

    report.add_result("/monitoring/health", "GET", response.status_code, data)
    report.add_verification_step(
        "Verify /monitoring/health response structure",
        "passed" if all(k in data for k in ["status", "timestamp", "version"]) else "failed",
        {"expected": ["status", "timestamp", "version"], "actual": list(data.keys())}
    )

    # Test /monitoring/system endpoint
    report.add_verification_step(
        "Verify /monitoring/system endpoint",
        "in_progress",
        {"endpoint": "/monitoring/system", "method": "GET"}
    )

    response = client.get("/monitoring/system")
    assert response.status_code == 200
    data = response.json()

    report.add_result("/monitoring/system", "GET", response.status_code, data)
    report.add_verification_step(
        "Verify /monitoring/system response structure",
        "passed" if "metrics" in data and all(k in data["metrics"] for k in ["cpu_usage", "memory_usage", "disk_usage"]) else "failed",
        {"expected": ["cpu_usage", "memory_usage", "disk_usage"], "actual": list(data.get("metrics", {}).keys())}
    )

    # Save report
    report_file = report.save_report()
    logger.info(f"Monitoring endpoints test report saved to {report_file}")
