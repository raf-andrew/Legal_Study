import pytest
import yaml
import json
from pathlib import Path
from typing import Dict, Any

class TestCodespacesConfiguration:
    """Test suite for Codespaces configuration validation."""

    @pytest.fixture
    def config_path(self) -> Path:
        """Fixture to provide the path to configuration files."""
        return Path(".codespaces/config")

    @pytest.fixture
    def test_config(self) -> Dict[str, Any]:
        """Fixture to provide test configuration."""
        return {
            "environment": {
                "python_version": "3.9",
                "use_venv": True,
                "test_prefix": "test_",
                "dependencies": [
                    "pytest",
                    "pytest-cov",
                    "pytest-html"
                ]
            },
            "isolation": {
                "use_docker": True,
                "cleanup_after_test": True,
                "preserve_logs": True
            },
            "codespaces": {
                "test_environment": "test",
                "production_environment": "prod",
                "regions": ["us-east-1", "us-west-2"],
                "instance_types": ["standard", "large"]
            }
        }

    def test_config_file_exists(self, config_path):
        """Test that configuration files exist."""
        assert (config_path / "codespaces_test_config.yaml").exists()
        assert (config_path / "unit_test_config.yaml").exists()

    def test_config_file_format(self, config_path):
        """Test that configuration files are valid YAML."""
        for config_file in config_path.glob("*.yaml"):
            with open(config_file) as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {config_file}: {e}")

    def test_required_sections(self, config_path):
        """Test that configuration files contain required sections."""
        required_sections = [
            "environment",
            "isolation",
            "codespaces",
            "test_categories",
            "reporting",
            "logging",
            "error_handling",
            "cleanup",
            "security"
        ]

        with open(config_path / "codespaces_test_config.yaml") as f:
            config = yaml.safe_load(f)
            for section in required_sections:
                assert section in config, f"Missing required section: {section}"

    def test_environment_config(self, test_config):
        """Test environment configuration validation."""
        env_config = test_config["environment"]

        assert isinstance(env_config["python_version"], str)
        assert isinstance(env_config["use_venv"], bool)
        assert isinstance(env_config["test_prefix"], str)
        assert isinstance(env_config["dependencies"], list)
        assert all(isinstance(dep, str) for dep in env_config["dependencies"])

    def test_isolation_config(self, test_config):
        """Test isolation configuration validation."""
        isolation_config = test_config["isolation"]

        assert isinstance(isolation_config["use_docker"], bool)
        assert isinstance(isolation_config["cleanup_after_test"], bool)
        assert isinstance(isolation_config["preserve_logs"], bool)

    def test_codespaces_config(self, test_config):
        """Test codespaces configuration validation."""
        codespaces_config = test_config["codespaces"]

        assert isinstance(codespaces_config["test_environment"], str)
        assert isinstance(codespaces_config["production_environment"], str)
        assert isinstance(codespaces_config["regions"], list)
        assert isinstance(codespaces_config["instance_types"], list)
        assert all(isinstance(region, str) for region in codespaces_config["regions"])
        assert all(isinstance(instance, str) for instance in codespaces_config["instance_types"])

    def test_config_validation(self, config_path):
        """Test configuration validation rules."""
        with open(config_path / "codespaces_test_config.yaml") as f:
            config = yaml.safe_load(f)

            # Test environment validation
            assert config["environment"]["python_version"] in ["3.8", "3.9", "3.10"]
            assert isinstance(config["environment"]["use_venv"], bool)
            assert config["environment"]["test_prefix"].endswith("_")

            # Test isolation validation
            assert isinstance(config["isolation"]["use_docker"], bool)
            assert isinstance(config["isolation"]["cleanup_after_test"], bool)
            assert isinstance(config["isolation"]["preserve_logs"], bool)

            # Test codespaces validation
            assert config["codespaces"]["test_environment"] != config["codespaces"]["production_environment"]
            assert len(config["codespaces"]["regions"]) > 0
            assert len(config["codespaces"]["instance_types"]) > 0

    def test_config_dependencies(self, config_path):
        """Test configuration dependencies and relationships."""
        with open(config_path / "codespaces_test_config.yaml") as f:
            config = yaml.safe_load(f)

            # Test that if use_docker is True, cleanup_after_test is also True
            if config["isolation"]["use_docker"]:
                assert config["isolation"]["cleanup_after_test"]

            # Test that test environment is different from production
            assert config["codespaces"]["test_environment"] != config["codespaces"]["production_environment"]

            # Test that test prefix is used in test environment
            assert config["environment"]["test_prefix"] in config["codespaces"]["test_environment"]

    def test_config_security(self, config_path):
        """Test security-related configuration."""
        with open(config_path / "codespaces_test_config.yaml") as f:
            config = yaml.safe_load(f)

            # Test security settings
            assert "security" in config
            assert isinstance(config["security"]["scan_dependencies"], bool)
            assert isinstance(config["security"]["check_vulnerabilities"], bool)
            assert isinstance(config["security"]["validate_requirements"], bool)

            # Test credentials configuration
            assert "test_credentials" in config["security"]
            assert isinstance(config["security"]["test_credentials"]["use_mock"], bool)
            assert isinstance(config["security"]["test_credentials"]["mock_credentials"], list)

    def test_config_reporting(self, config_path):
        """Test reporting configuration."""
        with open(config_path / "codespaces_test_config.yaml") as f:
            config = yaml.safe_load(f)

            # Test reporting settings
            assert "reporting" in config
            assert isinstance(config["reporting"]["directory"], str)
            assert isinstance(config["reporting"]["formats"], list)
            assert all(format in ["html", "xml", "json"] for format in config["reporting"]["formats"])

            # Test HTML reporting
            assert "html" in config["reporting"]
            assert isinstance(config["reporting"]["html"]["self_contained"], bool)

            # Test JUnit reporting
            assert "junit" in config["reporting"]
            assert isinstance(config["reporting"]["junit"]["output"], str)

            # Test coverage reporting
            assert "coverage" in config["reporting"]
            assert isinstance(config["reporting"]["coverage"]["output"], str)
            assert isinstance(config["reporting"]["coverage"]["formats"], list)
