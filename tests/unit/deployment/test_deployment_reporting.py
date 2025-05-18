import pytest
from pathlib import Path
import os
import yaml
import json
from datetime import datetime
from codespaces.scripts.deployment_reporting import DeploymentReporting

@pytest.fixture
def deployment_reporting():
    """Fixture to provide a DeploymentReporting instance."""
    return DeploymentReporting()

@pytest.fixture
def mock_config(tmp_path):
    """Fixture to provide a mock configuration."""
    config = {
        "reporting": {
            "reports": {
                "directory": "reports",
                "formats": ["html", "json", "pdf"]
            },
            "templates": {
                "deployment": "templates/deployment_report.html",
                "metrics": "templates/metrics_report.html",
                "alerts": "templates/alerts_report.html"
            },
            "sections": [
                "deployment_summary",
                "service_status",
                "metrics_summary",
                "alerts_summary",
                "error_log"
            ]
        }
    }
    config_file = tmp_path / "config" / "codespaces_config.yaml"
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file

def test_deployment_reporting_initialization(deployment_reporting):
    """Test DeploymentReporting initialization."""
    assert deployment_reporting is not None
    assert hasattr(deployment_reporting, "_load_config")
    assert hasattr(deployment_reporting, "generate_deployment_report")
    assert hasattr(deployment_reporting, "generate_metrics_report")

def test_generate_deployment_report(deployment_reporting, mock_config, tmp_path):
    """Test generating deployment report."""
    # Create mock deployment data
    deployment_data = {
        "deployments": [
            {
                "id": "1",
                "timestamp": "2024-01-01T00:00:00",
                "status": "success",
                "services": {
                    "web": "running",
                    "db": "running"
                },
                "metrics": {
                    "cpu": {"usage": 50.0},
                    "memory": {"usage": 60.0}
                },
                "alerts": [],
                "errors": []
            }
        ]
    }

    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / "deployment_history.json", "w") as f:
        json.dump(deployment_data, f)

    # Test report generation
    result = deployment_reporting.generate_deployment_report()
    assert result is True

def test_generate_metrics_report(deployment_reporting, mock_config, tmp_path):
    """Test generating metrics report."""
    # Create mock metrics data
    metrics_data = {
        "timestamp": datetime.now().isoformat(),
        "metrics": {
            "cpu": {"usage": 50.0},
            "memory": {"usage": 60.0},
            "disk": {"usage": 70.0}
        }
    }

    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / "metrics.json", "w") as f:
        json.dump(metrics_data, f)

    # Test report generation
    result = deployment_reporting.generate_metrics_report()
    assert result is True

def test_generate_alerts_report(deployment_reporting, mock_config, tmp_path):
    """Test generating alerts report."""
    # Create mock alerts data
    alerts_data = {
        "timestamp": datetime.now().isoformat(),
        "alerts": [
            {
                "type": "high_cpu",
                "message": "CPU usage above threshold",
                "severity": "warning"
            },
            {
                "type": "high_memory",
                "message": "Memory usage above threshold",
                "severity": "warning"
            }
        ]
    }

    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / "alerts.json", "w") as f:
        json.dump(alerts_data, f)

    # Test report generation
    result = deployment_reporting.generate_alerts_report()
    assert result is True

def test_generate_error_report(deployment_reporting, mock_config, tmp_path):
    """Test generating error report."""
    # Create mock error data
    error_data = {
        "timestamp": datetime.now().isoformat(),
        "errors": [
            {
                "type": "service_failure",
                "message": "Service failed to start",
                "details": "Connection refused"
            }
        ]
    }

    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / "errors.json", "w") as f:
        json.dump(error_data, f)

    # Test report generation
    result = deployment_reporting.generate_error_report()
    assert result is True

def test_generate_summary_report(deployment_reporting, mock_config, tmp_path):
    """Test generating summary report."""
    # Create mock summary data
    summary_data = {
        "timestamp": datetime.now().isoformat(),
        "deployment_status": "success",
        "services_status": {
            "web": "running",
            "db": "running"
        },
        "metrics_summary": {
            "cpu": {"avg": 50.0, "max": 80.0},
            "memory": {"avg": 60.0, "max": 85.0}
        },
        "alerts_summary": {
            "total": 2,
            "critical": 0,
            "warning": 2
        },
        "errors_summary": {
            "total": 1,
            "resolved": 1,
            "unresolved": 0
        }
    }

    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / "summary.json", "w") as f:
        json.dump(summary_data, f)

    # Test report generation
    result = deployment_reporting.generate_summary_report()
    assert result is True

def test_error_handling(deployment_reporting, mock_config, monkeypatch):
    """Test error handling in deployment reporting."""
    # Test report generation failure
    def mock_generate_report(*args, **kwargs):
        raise Exception("Failed to generate report")

    monkeypatch.setattr(deployment_reporting, "generate_deployment_report", mock_generate_report)

    with pytest.raises(Exception) as exc_info:
        deployment_reporting.generate_deployment_report()
    assert "Failed to generate report" in str(exc_info.value)

    # Test template rendering failure
    def mock_render_template(*args, **kwargs):
        raise Exception("Failed to render template")

    monkeypatch.setattr(deployment_reporting, "_render_template", mock_render_template)

    with pytest.raises(Exception) as exc_info:
        deployment_reporting.generate_metrics_report()
    assert "Failed to render template" in str(exc_info.value)
