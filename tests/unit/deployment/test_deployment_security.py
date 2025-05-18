import pytest
from pathlib import Path
import os
import yaml
import json
from datetime import datetime
from codespaces.scripts.deployment_security import DeploymentSecurity

@pytest.fixture
def deployment_security():
    """Fixture to provide a DeploymentSecurity instance."""
    return DeploymentSecurity()

@pytest.fixture
def mock_config(tmp_path):
    """Fixture to provide a mock configuration."""
    config = {
        "security": {
            "vulnerability_scanning": {
                "enabled": True,
                "interval": 3600,
                "severity_threshold": "high"
            },
            "dependency_checking": {
                "enabled": True,
                "interval": 86400,
                "package_managers": ["pip", "npm"]
            },
            "access_control": {
                "enabled": True,
                "roles": ["admin", "developer", "viewer"],
                "permissions": {
                    "admin": ["*"],
                    "developer": ["read", "write"],
                    "viewer": ["read"]
                }
            },
            "encryption": {
                "enabled": True,
                "algorithm": "AES-256-GCM",
                "key_rotation": 30
            }
        }
    }
    config_file = tmp_path / "config" / "codespaces_config.yaml"
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file

def test_deployment_security_initialization(deployment_security):
    """Test DeploymentSecurity initialization."""
    assert deployment_security is not None
    assert hasattr(deployment_security, "_load_config")
    assert hasattr(deployment_security, "scan_vulnerabilities")
    assert hasattr(deployment_security, "check_dependencies")

def test_scan_vulnerabilities(deployment_security, mock_config, monkeypatch):
    """Test scanning for vulnerabilities."""
    # Mock vulnerability scanner
    def mock_scan(*args, **kwargs):
        return {
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": [
                {
                    "id": "CVE-2024-0001",
                    "severity": "high",
                    "package": "package1",
                    "version": "1.0.0",
                    "description": "Test vulnerability"
                }
            ]
        }

    monkeypatch.setattr(deployment_security, "_run_vulnerability_scan", mock_scan)

    # Test vulnerability scanning
    result = deployment_security.scan_vulnerabilities()
    assert result is not None
    assert "vulnerabilities" in result
    assert len(result["vulnerabilities"]) > 0

def test_check_dependencies(deployment_security, mock_config, monkeypatch):
    """Test checking dependencies."""
    # Mock dependency checker
    def mock_check(*args, **kwargs):
        return {
            "timestamp": datetime.now().isoformat(),
            "dependencies": {
                "package1": {
                    "version": "1.0.0",
                    "latest": "1.1.0",
                    "vulnerabilities": []
                },
                "package2": {
                    "version": "2.0.0",
                    "latest": "2.1.0",
                    "vulnerabilities": [
                        {
                            "id": "CVE-2024-0002",
                            "severity": "medium",
                            "description": "Test vulnerability"
                        }
                    ]
                }
            }
        }

    monkeypatch.setattr(deployment_security, "_check_dependencies", mock_check)

    # Test dependency checking
    result = deployment_security.check_dependencies()
    assert result is not None
    assert "dependencies" in result
    assert len(result["dependencies"]) > 0

def test_check_access_control(deployment_security, mock_config, monkeypatch):
    """Test checking access control."""
    # Mock access control checker
    def mock_check(*args, **kwargs):
        return {
            "timestamp": datetime.now().isoformat(),
            "access_control": {
                "roles": {
                    "admin": ["*"],
                    "developer": ["read", "write"],
                    "viewer": ["read"]
                },
                "users": {
                    "user1": ["admin"],
                    "user2": ["developer"],
                    "user3": ["viewer"]
                }
            }
        }

    monkeypatch.setattr(deployment_security, "_check_access_control", mock_check)

    # Test access control checking
    result = deployment_security.check_access_control()
    assert result is not None
    assert "access_control" in result
    assert "roles" in result["access_control"]
    assert "users" in result["access_control"]

def test_check_encryption(deployment_security, mock_config, monkeypatch):
    """Test checking encryption."""
    # Mock encryption checker
    def mock_check(*args, **kwargs):
        return {
            "timestamp": datetime.now().isoformat(),
            "encryption": {
                "algorithm": "AES-256-GCM",
                "key_rotation": 30,
                "status": "active"
            }
        }

    monkeypatch.setattr(deployment_security, "_check_encryption", mock_check)

    # Test encryption checking
    result = deployment_security.check_encryption()
    assert result is not None
    assert "encryption" in result
    assert "algorithm" in result["encryption"]
    assert "status" in result["encryption"]

def test_generate_security_report(deployment_security, mock_config, tmp_path):
    """Test generating security report."""
    # Create mock security data
    security_data = {
        "timestamp": datetime.now().isoformat(),
        "vulnerabilities": [
            {
                "id": "CVE-2024-0001",
                "severity": "high",
                "package": "package1",
                "version": "1.0.0",
                "description": "Test vulnerability"
            }
        ],
        "dependencies": {
            "package1": {
                "version": "1.0.0",
                "latest": "1.1.0",
                "vulnerabilities": []
            }
        },
        "access_control": {
            "roles": {
                "admin": ["*"],
                "developer": ["read", "write"]
            }
        },
        "encryption": {
            "algorithm": "AES-256-GCM",
            "status": "active"
        }
    }

    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    with open(data_dir / "security.json", "w") as f:
        json.dump(security_data, f)

    # Test report generation
    result = deployment_security.generate_security_report()
    assert result is True

def test_error_handling(deployment_security, mock_config, monkeypatch):
    """Test error handling in deployment security."""
    # Test vulnerability scan failure
    def mock_scan(*args, **kwargs):
        raise Exception("Failed to scan vulnerabilities")

    monkeypatch.setattr(deployment_security, "scan_vulnerabilities", mock_scan)

    with pytest.raises(Exception) as exc_info:
        deployment_security.scan_vulnerabilities()
    assert "Failed to scan vulnerabilities" in str(exc_info.value)

    # Test dependency check failure
    def mock_check(*args, **kwargs):
        raise Exception("Failed to check dependencies")

    monkeypatch.setattr(deployment_security, "check_dependencies", mock_check)

    with pytest.raises(Exception) as exc_info:
        deployment_security.check_dependencies()
    assert "Failed to check dependencies" in str(exc_info.value)
