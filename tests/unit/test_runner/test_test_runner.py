import pytest
from pathlib import Path
import os
import subprocess
from codespaces.scripts.test_runner import TestRunner

@pytest.fixture
def test_runner():
    """Fixture to provide a TestRunner instance."""
    return TestRunner()

@pytest.fixture
def mock_config(tmp_path):
    """Fixture to provide a mock configuration."""
    config = {
        "test": {
            "directories": {
                "unit": "tests/unit",
                "integration": "tests/integration",
                "e2e": "tests/e2e"
            },
            "reports": {
                "directory": "reports",
                "formats": ["html", "xml", "json"]
            }
        }
    }
    config_file = tmp_path / "config" / "codespaces_config.yaml"
    config_file.parent.mkdir(exist_ok=True)
    with open(config_file, "w") as f:
        yaml.dump(config, f)
    return config_file

def test_test_runner_initialization(test_runner):
    """Test TestRunner initialization."""
    assert test_runner is not None
    assert hasattr(test_runner, "_setup_logging")
    assert hasattr(test_runner, "_load_config")
    assert hasattr(test_runner, "_print_status")

def test_run_unit_tests(test_runner, mock_config, monkeypatch):
    """Test running unit tests."""
    # Mock subprocess.run
    def mock_run(*args, **kwargs):
        class MockResult:
            def __init__(self):
                self.returncode = 0
                self.stdout = "All tests passed"
                self.stderr = ""
        return MockResult()

    monkeypatch.setattr(subprocess, "run", mock_run)

    # Test running unit tests
    result = test_runner.run_unit_tests()
    assert result is True

def test_run_integration_tests(test_runner, mock_config, monkeypatch):
    """Test running integration tests."""
    # Mock subprocess.run
    def mock_run(*args, **kwargs):
        class MockResult:
            def __init__(self):
                self.returncode = 0
                self.stdout = "All tests passed"
                self.stderr = ""
        return MockResult()

    monkeypatch.setattr(subprocess, "run", mock_run)

    # Test running integration tests
    result = test_runner.run_integration_tests()
    assert result is True

def test_run_e2e_tests(test_runner, mock_config, monkeypatch):
    """Test running end-to-end tests."""
    # Mock subprocess.run
    def mock_run(*args, **kwargs):
        class MockResult:
            def __init__(self):
                self.returncode = 0
                self.stdout = "All tests passed"
                self.stderr = ""
        return MockResult()

    monkeypatch.setattr(subprocess, "run", mock_run)

    # Test running e2e tests
    result = test_runner.run_e2e_tests()
    assert result is True

def test_generate_test_report(test_runner, mock_config, tmp_path):
    """Test generating test report."""
    # Create mock test results
    results_dir = tmp_path / "reports"
    results_dir.mkdir(exist_ok=True)

    # Test report generation
    result = test_runner.generate_test_report()
    assert result is True

def test_error_handling(test_runner, mock_config, monkeypatch):
    """Test error handling in test runner."""
    # Mock a failing test run
    def mock_run(*args, **kwargs):
        class MockResult:
            def __init__(self):
                self.returncode = 1
                self.stdout = "Some tests failed"
                self.stderr = "Error details"
        return MockResult()

    monkeypatch.setattr(subprocess, "run", mock_run)

    # Test error handling
    with pytest.raises(Exception) as exc_info:
        test_runner.run_unit_tests()
    assert "Some tests failed" in str(exc_info.value)
