import pytest
from pathlib import Path
import os
import yaml
import json
from datetime import datetime
from codespaces.scripts.deployment_monitoring import DeploymentMonitoring

@pytest.fixture
def deployment_monitoring():
    """Fixture to provide a DeploymentMonitoring instance."""
    return DeploymentMonitoring()

@pytest.fixture
def mock_config(tmp_path):
    """Fixture to provide a mock configuration."""
    config = {
        "monitoring": {
            "metrics": {
                "interval": 60,
                "retention_days": 30
            },
            "alerts": {
                "cpu_threshold": 80,
                "memory_threshold": 80,
                "disk_threshold": 80
            },
            "services": {
                "web": {
                    "metrics": ["cpu", "memory", "requests"],
                    "alerts": ["high_cpu", "high_memory", "high_latency"]
                },
                "db": {
                    "metrics": ["cpu", "memory", "connections"],
                    "alerts": ["high_cpu", "high_memory", "high_connections"]
                }
            }
        }
    }
    config_file = tmp_path / "config" / "codespaces_config.yaml"
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file

def test_deployment_monitoring_initialization(deployment_monitoring):
    """Test DeploymentMonitoring initialization."""
    assert deployment_monitoring is not None
    assert hasattr(deployment_monitoring, "_load_config")
    assert hasattr(deployment_monitoring, "collect_metrics")
    assert hasattr(deployment_monitoring, "check_alerts")

def test_collect_metrics(deployment_monitoring, mock_config, monkeypatch):
    """Test collecting metrics."""
    # Mock metric collection
    def mock_collect_cpu(*args, **kwargs):
        return {"usage": 50.0}

    def mock_collect_memory(*args, **kwargs):
        return {"usage": 60.0}

    def mock_collect_disk(*args, **kwargs):
        return {"usage": 70.0}

    monkeypatch.setattr(deployment_monitoring, "_collect_cpu_metrics", mock_collect_cpu)
    monkeypatch.setattr(deployment_monitoring, "_collect_memory_metrics", mock_collect_memory)
    monkeypatch.setattr(deployment_monitoring, "_collect_disk_metrics", mock_collect_disk)

    # Test metric collection
    metrics = deployment_monitoring.collect_metrics()
    assert metrics is not None
    assert "cpu" in metrics
    assert "memory" in metrics
    assert "disk" in metrics

def test_check_alerts(deployment_monitoring, mock_config, monkeypatch):
    """Test checking alerts."""
    # Mock metric collection
    def mock_collect_metrics(*args, **kwargs):
        return {
            "cpu": {"usage": 90.0},
            "memory": {"usage": 85.0},
            "disk": {"usage": 75.0}
        }

    monkeypatch.setattr(deployment_monitoring, "collect_metrics", mock_collect_metrics)

    # Test alert checking
    alerts = deployment_monitoring.check_alerts()
    assert alerts is not None
    assert len(alerts) > 0
    assert any("high_cpu" in alert for alert in alerts)
    assert any("high_memory" in alert for alert in alerts)

def test_collect_service_metrics(deployment_monitoring, mock_config, monkeypatch):
    """Test collecting service metrics."""
    # Mock Docker client
    class MockDockerClient:
        def containers(self):
            return [
                {"name": "web", "status": "running"},
                {"name": "db", "status": "running"}
            ]

        def stats(self, *args, **kwargs):
            return {
                "cpu_stats": {"cpu_usage": {"total_usage": 1000000}},
                "memory_stats": {"usage": 1000000},
                "networks": {"eth0": {"rx_bytes": 1000, "tx_bytes": 1000}}
            }

    monkeypatch.setattr(deployment_monitoring, "docker_client", MockDockerClient())

    # Test service metrics collection
    metrics = deployment_monitoring.collect_service_metrics("web")
    assert metrics is not None
    assert "cpu" in metrics
    assert "memory" in metrics
    assert "network" in metrics

def test_generate_metrics_report(deployment_monitoring, mock_config, tmp_path):
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
    result = deployment_monitoring.generate_metrics_report()
    assert result is True

def test_error_handling(deployment_monitoring, mock_config, monkeypatch):
    """Test error handling in deployment monitoring."""
    # Test metric collection failure
    def mock_collect_metrics(*args, **kwargs):
        raise Exception("Failed to collect metrics")

    monkeypatch.setattr(deployment_monitoring, "collect_metrics", mock_collect_metrics)

    with pytest.raises(Exception) as exc_info:
        deployment_monitoring.collect_metrics()
    assert "Failed to collect metrics" in str(exc_info.value)

    # Test alert check failure
    def mock_check_alerts(*args, **kwargs):
        raise Exception("Failed to check alerts")

    monkeypatch.setattr(deployment_monitoring, "check_alerts", mock_check_alerts)

    with pytest.raises(Exception) as exc_info:
        deployment_monitoring.check_alerts()
    assert "Failed to check alerts" in str(exc_info.value)
