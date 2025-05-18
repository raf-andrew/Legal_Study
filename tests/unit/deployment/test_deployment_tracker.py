import pytest
from pathlib import Path
import os
import json
from datetime import datetime
from codespaces.scripts.deployment_tracker import DeploymentTracker

@pytest.fixture
def deployment_tracker():
    """Fixture to provide a DeploymentTracker instance."""
    return DeploymentTracker()

@pytest.fixture
def mock_deployment_data(tmp_path):
    """Fixture to provide mock deployment data."""
    data = {
        "deployments": [
            {
                "id": "1",
                "timestamp": "2024-01-01T00:00:00",
                "status": "success",
                "services": {
                    "service1": "running",
                    "service2": "running"
                },
                "test_results": {
                    "unit": "passed",
                    "integration": "passed"
                },
                "health_checks": {
                    "service1": "healthy",
                    "service2": "healthy"
                },
                "errors": []
            }
        ]
    }
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / "deployment_history.json", "w") as f:
        json.dump(data, f)
    return data_dir / "deployment_history.json"

def test_deployment_tracker_initialization(deployment_tracker):
    """Test DeploymentTracker initialization."""
    assert deployment_tracker is not None
    assert hasattr(deployment_tracker, "start_deployment")
    assert hasattr(deployment_tracker, "update_service_status")
    assert hasattr(deployment_tracker, "record_test_results")

def test_start_deployment(deployment_tracker, tmp_path):
    """Test starting a new deployment."""
    # Test deployment start
    deployment_id = deployment_tracker.start_deployment()
    assert deployment_id is not None

    # Verify deployment data
    data_file = tmp_path / "data" / "deployment_history.json"
    assert data_file.exists()

    with open(data_file) as f:
        data = json.load(f)
        assert "deployments" in data
        assert len(data["deployments"]) > 0
        assert data["deployments"][-1]["id"] == deployment_id

def test_update_service_status(deployment_tracker, mock_deployment_data):
    """Test updating service status."""
    # Test service status update
    result = deployment_tracker.update_service_status("service1", "running")
    assert result is True

    # Verify status update
    with open(mock_deployment_data) as f:
        data = json.load(f)
        assert data["deployments"][-1]["services"]["service1"] == "running"

def test_record_test_results(deployment_tracker, mock_deployment_data):
    """Test recording test results."""
    # Test recording test results
    test_results = {
        "unit": "passed",
        "integration": "passed"
    }
    result = deployment_tracker.record_test_results(test_results)
    assert result is True

    # Verify test results
    with open(mock_deployment_data) as f:
        data = json.load(f)
        assert data["deployments"][-1]["test_results"] == test_results

def test_update_health_checks(deployment_tracker, mock_deployment_data):
    """Test updating health checks."""
    # Test health check update
    health_checks = {
        "service1": "healthy",
        "service2": "healthy"
    }
    result = deployment_tracker.update_health_checks(health_checks)
    assert result is True

    # Verify health checks
    with open(mock_deployment_data) as f:
        data = json.load(f)
        assert data["deployments"][-1]["health_checks"] == health_checks

def test_add_error(deployment_tracker, mock_deployment_data):
    """Test adding error to deployment."""
    # Test adding error
    error = {
        "timestamp": datetime.now().isoformat(),
        "message": "Test error",
        "details": "Error details"
    }
    result = deployment_tracker.add_error(error)
    assert result is True

    # Verify error
    with open(mock_deployment_data) as f:
        data = json.load(f)
        assert len(data["deployments"][-1]["errors"]) > 0
        assert data["deployments"][-1]["errors"][-1]["message"] == "Test error"

def test_complete_deployment(deployment_tracker, mock_deployment_data):
    """Test completing a deployment."""
    # Test deployment completion
    result = deployment_tracker.complete_deployment("success")
    assert result is True

    # Verify completion
    with open(mock_deployment_data) as f:
        data = json.load(f)
        assert data["deployments"][-1]["status"] == "success"

def test_get_deployment_summary(deployment_tracker, mock_deployment_data):
    """Test getting deployment summary."""
    # Test getting summary
    summary = deployment_tracker.get_deployment_summary()
    assert summary is not None
    assert "deployments" in summary
    assert len(summary["deployments"]) > 0

def test_cleanup_old_deployments(deployment_tracker, mock_deployment_data):
    """Test cleaning up old deployments."""
    # Test cleanup
    result = deployment_tracker.cleanup_old_deployments(days=30)
    assert result is True

    # Verify cleanup
    with open(mock_deployment_data) as f:
        data = json.load(f)
        assert len(data["deployments"]) > 0  # Should keep recent deployments
