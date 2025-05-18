"""
Tests for sniffing result manager.
"""
import asyncio
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from ...server.sniffing.manager import ResultManager
from ...utils.config import MCPConfig

@pytest.fixture
def config() -> MCPConfig:
    """Create test configuration.

    Returns:
        Test configuration
    """
    # Create temp directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        reports_dir = temp_path / "reports"
        reports_dir.mkdir()

        # Create test config
        config = {
            "report_path": str(reports_dir),
            "domains": {
                "security": {
                    "enabled": True,
                    "report_format": "json"
                },
                "browser": {
                    "enabled": True,
                    "report_format": "yaml"
                }
            },
            "logging": {
                "level": "DEBUG",
                "format": "%(message)s",
                "file": str(temp_path / "test.log")
            }
        }

        yield MCPConfig(config)

@pytest.fixture
async def manager(config: MCPConfig) -> ResultManager:
    """Create test result manager.

    Args:
        config: Test configuration

    Returns:
        Test result manager
    """
    manager = ResultManager(config)
    await manager.start()
    yield manager
    await manager.stop()

@pytest.mark.asyncio
async def test_store_result(
    manager: ResultManager,
    tmp_path: Path
):
    """Test storing result.

    Args:
        manager: Test result manager
        tmp_path: Temporary directory
    """
    # Create test result
    test_file = tmp_path / "test.js"
    result = {
        "file": str(test_file),
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "issues": []
    }

    # Store result
    job_id = await manager.store_result(result)

    # Check job
    assert job_id is not None
    assert job_id in manager.active_jobs

    # Wait for processing
    while job_id in manager.active_jobs:
        await asyncio.sleep(0.1)

    # Check report file
    report_file = Path(manager.config.report_path) / "test.json"
    assert report_file.exists()
    with open(report_file) as f:
        stored_result = json.load(f)
        assert stored_result == result

@pytest.mark.asyncio
async def test_store_multiple_results(
    manager: ResultManager,
    tmp_path: Path
):
    """Test storing multiple results.

    Args:
        manager: Test result manager
        tmp_path: Temporary directory
    """
    # Create test results
    results = []
    for i in range(3):
        test_file = tmp_path / f"test_{i}.js"
        result = {
            "file": str(test_file),
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "issues": []
        }
        results.append(result)

    # Store results
    job_ids = []
    for result in results:
        job_id = await manager.store_result(result)
        job_ids.append(job_id)

    # Wait for processing
    while any(job_id in manager.active_jobs for job_id in job_ids):
        await asyncio.sleep(0.1)

    # Check report files
    for i in range(3):
        report_file = Path(manager.config.report_path) / f"test_{i}.json"
        assert report_file.exists()
        with open(report_file) as f:
            stored_result = json.load(f)
            assert stored_result == results[i]

@pytest.mark.asyncio
async def test_store_domain_result(
    manager: ResultManager,
    tmp_path: Path
):
    """Test storing domain-specific result.

    Args:
        manager: Test result manager
        tmp_path: Temporary directory
    """
    # Create test result
    test_file = tmp_path / "test.js"
    result = {
        "file": str(test_file),
        "domain": "security",
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "issues": []
    }

    # Store result
    job_id = await manager.store_result(result)

    # Wait for processing
    while job_id in manager.active_jobs:
        await asyncio.sleep(0.1)

    # Check report file
    report_file = Path(manager.config.report_path) / "security" / "test.json"
    assert report_file.exists()
    with open(report_file) as f:
        stored_result = json.load(f)
        assert stored_result == result

@pytest.mark.asyncio
async def test_store_yaml_result(
    manager: ResultManager,
    tmp_path: Path
):
    """Test storing YAML result.

    Args:
        manager: Test result manager
        tmp_path: Temporary directory
    """
    # Create test result
    test_file = tmp_path / "test.js"
    result = {
        "file": str(test_file),
        "domain": "browser",
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "issues": []
    }

    # Store result
    job_id = await manager.store_result(result)

    # Wait for processing
    while job_id in manager.active_jobs:
        await asyncio.sleep(0.1)

    # Check report file
    report_file = Path(manager.config.report_path) / "browser" / "test.yaml"
    assert report_file.exists()
    with open(report_file) as f:
        stored_result = yaml.safe_load(f)
        assert stored_result == result

@pytest.mark.asyncio
async def test_load_result(
    manager: ResultManager,
    tmp_path: Path
):
    """Test loading result.

    Args:
        manager: Test result manager
        tmp_path: Temporary directory
    """
    # Create test result
    test_file = tmp_path / "test.js"
    result = {
        "file": str(test_file),
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "issues": []
    }

    # Store result
    job_id = await manager.store_result(result)

    # Wait for processing
    while job_id in manager.active_jobs:
        await asyncio.sleep(0.1)

    # Load result
    loaded_result = await manager.load_result(str(test_file))
    assert loaded_result == result

@pytest.mark.asyncio
async def test_load_domain_result(
    manager: ResultManager,
    tmp_path: Path
):
    """Test loading domain-specific result.

    Args:
        manager: Test result manager
        tmp_path: Temporary directory
    """
    # Create test result
    test_file = tmp_path / "test.js"
    result = {
        "file": str(test_file),
        "domain": "security",
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "issues": []
    }

    # Store result
    job_id = await manager.store_result(result)

    # Wait for processing
    while job_id in manager.active_jobs:
        await asyncio.sleep(0.1)

    # Load result
    loaded_result = await manager.load_result(
        str(test_file),
        domain="security"
    )
    assert loaded_result == result

@pytest.mark.asyncio
async def test_load_yaml_result(
    manager: ResultManager,
    tmp_path: Path
):
    """Test loading YAML result.

    Args:
        manager: Test result manager
        tmp_path: Temporary directory
    """
    # Create test result
    test_file = tmp_path / "test.js"
    result = {
        "file": str(test_file),
        "domain": "browser",
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "issues": []
    }

    # Store result
    job_id = await manager.store_result(result)

    # Wait for processing
    while job_id in manager.active_jobs:
        await asyncio.sleep(0.1)

    # Load result
    loaded_result = await manager.load_result(
        str(test_file),
        domain="browser"
    )
    assert loaded_result == result

@pytest.mark.asyncio
async def test_delete_result(
    manager: ResultManager,
    tmp_path: Path
):
    """Test deleting result.

    Args:
        manager: Test result manager
        tmp_path: Temporary directory
    """
    # Create test result
    test_file = tmp_path / "test.js"
    result = {
        "file": str(test_file),
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "issues": []
    }

    # Store result
    job_id = await manager.store_result(result)

    # Wait for processing
    while job_id in manager.active_jobs:
        await asyncio.sleep(0.1)

    # Delete result
    await manager.delete_result(str(test_file))

    # Check report file
    report_file = Path(manager.config.report_path) / "test.json"
    assert not report_file.exists()

@pytest.mark.asyncio
async def test_list_results(
    manager: ResultManager,
    tmp_path: Path
):
    """Test listing results.

    Args:
        manager: Test result manager
        tmp_path: Temporary directory
    """
    # Create test results
    results = []
    for i in range(3):
        test_file = tmp_path / f"test_{i}.js"
        result = {
            "file": str(test_file),
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "issues": []
        }
        results.append(result)

    # Store results
    job_ids = []
    for result in results:
        job_id = await manager.store_result(result)
        job_ids.append(job_id)

    # Wait for processing
    while any(job_id in manager.active_jobs for job_id in job_ids):
        await asyncio.sleep(0.1)

    # List results
    result_files = await manager.list_results()
    assert len(result_files) == 3
    assert all(f"test_{i}.json" in result_files for i in range(3))

@pytest.mark.asyncio
async def test_list_domain_results(
    manager: ResultManager,
    tmp_path: Path
):
    """Test listing domain-specific results.

    Args:
        manager: Test result manager
        tmp_path: Temporary directory
    """
    # Create test results
    results = []
    for i in range(3):
        test_file = tmp_path / f"test_{i}.js"
        result = {
            "file": str(test_file),
            "domain": "security",
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "issues": []
        }
        results.append(result)

    # Store results
    job_ids = []
    for result in results:
        job_id = await manager.store_result(result)
        job_ids.append(job_id)

    # Wait for processing
    while any(job_id in manager.active_jobs for job_id in job_ids):
        await asyncio.sleep(0.1)

    # List results
    result_files = await manager.list_results(domain="security")
    assert len(result_files) == 3
    assert all(f"test_{i}.json" in result_files for i in range(3))

@pytest.mark.asyncio
async def test_metrics(manager: ResultManager):
    """Test metrics collection.

    Args:
        manager: Test result manager
    """
    # Get initial metrics
    metrics = manager.get_metrics()
    assert metrics["active_jobs"] == 0
    assert metrics["stored_results"] == 0
    assert metrics["report_queue"] == 0
    assert metrics["status"] == "running"
