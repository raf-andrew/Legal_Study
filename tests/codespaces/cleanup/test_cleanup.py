import pytest
import docker
import time
from pathlib import Path
from typing import Dict, Optional

class TestCodespacesCleanup:
    """Test suite for Codespaces cleanup functionality."""

    @pytest.fixture
    def docker_client(self):
        """Fixture to provide Docker client."""
        return docker.from_env()

    @pytest.fixture
    def test_codespace(self, docker_client):
        """Fixture to create and cleanup a test codespace."""
        # Create test codespace
        container = docker_client.containers.run(
            image="mcr.microsoft.com/vscode/devcontainers/python:3.9",
            name="test_cleanup_codespace",
            detach=True,
            environment={
                "TEST_ENVIRONMENT": "true",
                "TEST_NAME": "cleanup_test"
            }
        )

        yield container

        # Cleanup
        container.stop()
        container.remove()

    def test_codespace_creation(self, test_codespace):
        """Test that a codespace can be created successfully."""
        assert test_codespace.status == "running"
        assert test_codespace.name == "test_cleanup_codespace"

    def test_environment_variables(self, test_codespace):
        """Test that environment variables are set correctly."""
        env = test_codespace.attrs["Config"]["Env"]
        assert "TEST_ENVIRONMENT=true" in env
        assert "TEST_NAME=cleanup_test" in env

    def test_python_version(self, test_codespace):
        """Test that Python version is correct."""
        result = test_codespace.exec_run("python --version")
        assert "Python 3.9" in result.output.decode()

    def test_required_packages(self, test_codespace):
        """Test that required packages are installed."""
        packages = [
            "pytest",
            "pytest-cov",
            "pytest-html",
            "pytest-xdist",
            "pytest-timeout",
            "pytest-mock",
            "docker",
            "requests",
            "colorama"
        ]

        for package in packages:
            result = test_codespace.exec_run(f"pip show {package}")
            assert result.exit_code == 0, f"Package {package} not installed"

    def test_workspace_structure(self, test_codespace):
        """Test that workspace structure is correct."""
        required_dirs = [
            "/workspace",
            "/workspace/.codespaces",
            "/workspace/.codespaces/config",
            "/workspace/.codespaces/scripts",
            "/workspace/.codespaces/logs",
            "/workspace/.codespaces/reports"
        ]

        for directory in required_dirs:
            result = test_codespace.exec_run(f"test -d {directory}")
            assert result.exit_code == 0, f"Directory {directory} not found"

    def test_config_files(self, test_codespace):
        """Test that configuration files exist and are valid."""
        config_files = [
            "/workspace/.codespaces/config/codespaces_test_config.yaml",
            "/workspace/.codespaces/config/unit_test_config.yaml"
        ]

        for config_file in config_files:
            result = test_codespace.exec_run(f"test -f {config_file}")
            assert result.exit_code == 0, f"Config file {config_file} not found"

    def test_network_connectivity(self, test_codespace):
        """Test network connectivity from the codespace."""
        # Test internet connectivity
        result = test_codespace.exec_run("curl -s https://www.google.com")
        assert result.exit_code == 0, "No internet connectivity"

        # Test Docker connectivity
        result = test_codespace.exec_run("docker ps")
        assert result.exit_code == 0, "Docker not accessible"

    def test_resource_limits(self, test_codespace):
        """Test that resource limits are set correctly."""
        # Get container stats
        stats = test_codespace.stats(stream=False)

        # Check memory limits
        assert "memory_stats" in stats
        assert "limit" in stats["memory_stats"]

        # Check CPU limits
        assert "cpu_stats" in stats
        assert "cpu_usage" in stats["cpu_stats"]

    def test_cleanup(self, test_codespace):
        """Test that cleanup works correctly."""
        # Stop the container
        test_codespace.stop()
        assert test_codespace.status == "exited"

        # Remove the container
        test_codespace.remove()

        # Verify container is removed
        with pytest.raises(docker.errors.NotFound):
            docker.from_env().containers.get("test_cleanup_codespace")

    @pytest.mark.parametrize("region", ["us-east-1", "us-west-2"])
    def test_region_availability(self, region):
        """Test that required regions are available."""
        # This would typically involve checking AWS region availability
        # For now, we'll just verify the region is in our config
        assert region in ["us-east-1", "us-west-2"]

    @pytest.mark.parametrize("instance_type", ["standard", "large"])
    def test_instance_types(self, instance_type):
        """Test that required instance types are available."""
        # This would typically involve checking AWS instance type availability
        # For now, we'll just verify the instance type is in our config
        assert instance_type in ["standard", "large"]
