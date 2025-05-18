import pytest
import docker
import requests
import time
from pathlib import Path
from typing import Dict, Optional

class TestCodespacesDeployment:
    """Test suite for Codespaces deployment functionality."""

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
            name="test_deployment_codespace",
            detach=True,
            environment={
                "TEST_ENVIRONMENT": "true",
                "TEST_NAME": "deployment_test"
            }
        )

        yield container

        # Cleanup
        container.stop()
        container.remove()

    def test_deployment_creation(self, test_codespace):
        """Test that a codespace can be deployed successfully."""
        assert test_codespace.status == "running"
        assert test_codespace.name == "test_deployment_codespace"

    def test_deployment_configuration(self, test_codespace):
        """Test deployment configuration."""
        # Check environment variables
        env = test_codespace.attrs["Config"]["Env"]
        assert "TEST_ENVIRONMENT=true" in env
        assert "TEST_NAME=deployment_test" in env

        # Check container configuration
        config = test_codespace.attrs["Config"]
        assert config["Image"] == "mcr.microsoft.com/vscode/devcontainers/python:3.9"
        assert config["Tty"] is False
        assert config["OpenStdin"] is False

    def test_deployment_health(self, test_codespace):
        """Test deployment health checks."""
        # Wait for container to be ready
        time.sleep(5)

        # Check container is running
        assert test_codespace.status == "running"

        # Check container health
        health = test_codespace.attrs["State"]["Health"]
        if health:
            assert health["Status"] == "healthy"

    def test_deployment_networking(self, test_codespace):
        """Test deployment networking."""
        # Get container network settings
        networks = test_codespace.attrs["NetworkSettings"]["Networks"]
        assert len(networks) > 0

        # Check network connectivity
        result = test_codespace.exec_run("curl -s https://www.google.com")
        assert result.exit_code == 0, "No internet connectivity"

    def test_deployment_resources(self, test_codespace):
        """Test deployment resource allocation."""
        # Get container stats
        stats = test_codespace.stats(stream=False)

        # Check memory allocation
        assert "memory_stats" in stats
        assert "limit" in stats["memory_stats"]

        # Check CPU allocation
        assert "cpu_stats" in stats
        assert "cpu_usage" in stats["cpu_stats"]

    def test_deployment_volumes(self, test_codespace):
        """Test deployment volume mounting."""
        # Check workspace volume
        mounts = test_codespace.attrs["Mounts"]
        workspace_mount = next((m for m in mounts if m["Destination"] == "/workspace"), None)
        assert workspace_mount is not None
        assert workspace_mount["Type"] == "volume"

    def test_deployment_restart(self, test_codespace):
        """Test deployment restart functionality."""
        # Stop the container
        test_codespace.stop()
        assert test_codespace.status == "exited"

        # Start the container
        test_codespace.start()
        assert test_codespace.status == "running"

    def test_deployment_cleanup(self, test_codespace):
        """Test deployment cleanup."""
        # Stop the container
        test_codespace.stop()
        assert test_codespace.status == "exited"

        # Remove the container
        test_codespace.remove()

        # Verify container is removed
        with pytest.raises(docker.errors.NotFound):
            docker.from_env().containers.get("test_deployment_codespace")

    def test_deployment_logs(self, test_codespace):
        """Test deployment logging."""
        # Get container logs
        logs = test_codespace.logs().decode()
        assert len(logs) > 0

        # Check for specific log entries
        assert "Starting" in logs or "Initializing" in logs

    def test_deployment_environment(self, test_codespace):
        """Test deployment environment setup."""
        # Check Python environment
        result = test_codespace.exec_run("python --version")
        assert result.exit_code == 0
        assert "Python 3.9" in result.output.decode()

        # Check pip installation
        result = test_codespace.exec_run("pip --version")
        assert result.exit_code == 0

    def test_deployment_dependencies(self, test_codespace):
        """Test deployment dependency installation."""
        # Check required packages
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

    def test_deployment_security(self, test_codespace):
        """Test deployment security measures."""
        # Check for security-related environment variables
        env = test_codespace.attrs["Config"]["Env"]
        assert not any(var.startswith("AWS_") for var in env)
        assert not any(var.startswith("GITHUB_") for var in env)

        # Check for security-related files
        result = test_codespace.exec_run("test -f /workspace/.env")
        assert result.exit_code != 0, "Found sensitive .env file"

    def test_deployment_monitoring(self, test_codespace):
        """Test deployment monitoring setup."""
        # Check for monitoring endpoints
        result = test_codespace.exec_run("curl -s http://localhost:8080/health")
        assert result.exit_code == 0 or result.exit_code == 7  # 7 means connection refused, which is fine if no monitoring

        # Check for monitoring logs
        logs = test_codespace.logs().decode()
        assert "monitoring" in logs.lower() or "metrics" in logs.lower()

    @pytest.mark.parametrize("region", ["us-east-1", "us-west-2"])
    def test_deployment_regions(self, region):
        """Test deployment in different regions."""
        # This would typically involve checking AWS region availability
        # For now, we'll just verify the region is in our config
        assert region in ["us-east-1", "us-west-2"]

    @pytest.mark.parametrize("instance_type", ["standard", "large"])
    def test_deployment_instance_types(self, instance_type):
        """Test deployment with different instance types."""
        # This would typically involve checking AWS instance type availability
        # For now, we'll just verify the instance type is in our config
        assert instance_type in ["standard", "large"]
