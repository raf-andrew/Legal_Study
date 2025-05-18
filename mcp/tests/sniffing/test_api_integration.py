"""
Tests for API integration.
"""
import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import aiohttp
import pytest
import yaml
from aiohttp import web

from ...server.sniffing.api import APIIntegration
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
            "api": {
                "host": "localhost",
                "port": 8080,
                "endpoints": {
                    "sniff": "/api/sniff",
                    "analyze": "/api/analyze",
                    "fix": "/api/fix",
                    "report": "/api/report"
                },
                "auth": {
                    "enabled": True,
                    "token": "test_token"
                }
            },
            "report_path": str(reports_dir),
            "logging": {
                "level": "DEBUG",
                "format": "%(message)s",
                "file": str(temp_path / "test.log")
            }
        }

        yield MCPConfig(config)

@pytest.fixture
async def api(config: MCPConfig) -> APIIntegration:
    """Create test API integration.

    Args:
        config: Test configuration

    Returns:
        Test API integration
    """
    api = APIIntegration(config)
    await api.start()
    yield api
    await api.stop()

@pytest.fixture
async def client(api: APIIntegration) -> aiohttp.ClientSession:
    """Create test client.

    Args:
        api: Test API integration

    Returns:
        Test client
    """
    async with aiohttp.ClientSession() as session:
        yield session

@pytest.mark.asyncio
async def test_sniff_endpoint(
    api: APIIntegration,
    client: aiohttp.ClientSession,
    tmp_path: Path
):
    """Test sniff endpoint.

    Args:
        api: Test API integration
        client: Test client
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function getUser(id) {
        return db.query('SELECT * FROM users WHERE id = ' + id);
    }
    """)

    # Send request
    headers = {"Authorization": f"Bearer {api.config.api['auth']['token']}"}
    data = {
        "file": str(test_file),
        "domains": ["security"]
    }
    async with client.post(
        f"http://{api.config.api['host']}:{api.config.api['port']}/api/sniff",
        headers=headers,
        json=data
    ) as response:
        # Check response
        assert response.status == 200
        result = await response.json()
        assert result["status"] == "failed"
        assert len(result["issues"]) > 0

@pytest.mark.asyncio
async def test_analyze_endpoint(
    api: APIIntegration,
    client: aiohttp.ClientSession,
    tmp_path: Path
):
    """Test analyze endpoint.

    Args:
        api: Test API integration
        client: Test client
        tmp_path: Temporary directory
    """
    # Create test result
    test_file = tmp_path / "test.js"
    result = {
        "file": str(test_file),
        "status": "failed",
        "timestamp": "2024-01-01T00:00:00",
        "issues": [
            {
                "type": "pattern",
                "name": "sql_injection",
                "severity": "critical",
                "line": 3
            }
        ]
    }

    # Send request
    headers = {"Authorization": f"Bearer {api.config.api['auth']['token']}"}
    data = {
        "file": str(test_file),
        "result": result
    }
    async with client.post(
        f"http://{api.config.api['host']}:{api.config.api['port']}/api/analyze",
        headers=headers,
        json=data
    ) as response:
        # Check response
        assert response.status == 200
        analysis = await response.json()
        assert analysis["status"] == "failed"
        assert len(analysis["recommendations"]) > 0

@pytest.mark.asyncio
async def test_fix_endpoint(
    api: APIIntegration,
    client: aiohttp.ClientSession,
    tmp_path: Path
):
    """Test fix endpoint.

    Args:
        api: Test API integration
        client: Test client
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function getUser(id) {
        return db.query('SELECT * FROM users WHERE id = ' + id);
    }
    """)

    # Create test issues
    issues = [
        {
            "type": "pattern",
            "name": "sql_injection",
            "severity": "critical",
            "line": 3,
            "fix": {
                "type": "replace",
                "pattern": "id = ' \\+ id",
                "replacement": "id = ?"
            }
        }
    ]

    # Send request
    headers = {"Authorization": f"Bearer {api.config.api['auth']['token']}"}
    data = {
        "file": str(test_file),
        "issues": issues
    }
    async with client.post(
        f"http://{api.config.api['host']}:{api.config.api['port']}/api/fix",
        headers=headers,
        json=data
    ) as response:
        # Check response
        assert response.status == 200
        result = await response.json()
        assert result["status"] == "completed"
        assert len(result["fixes"]) > 0

        # Check file
        assert "WHERE id = ?" in test_file.read_text()

@pytest.mark.asyncio
async def test_report_endpoint(
    api: APIIntegration,
    client: aiohttp.ClientSession,
    tmp_path: Path
):
    """Test report endpoint.

    Args:
        api: Test API integration
        client: Test client
        tmp_path: Temporary directory
    """
    # Create test results
    results = []
    for i in range(3):
        test_file = tmp_path / f"test_{i}.js"
        result = {
            "file": str(test_file),
            "status": "completed",
            "timestamp": "2024-01-01T00:00:00",
            "issues": []
        }
        results.append(result)

    # Send request
    headers = {"Authorization": f"Bearer {api.config.api['auth']['token']}"}
    data = {"results": results}
    async with client.post(
        f"http://{api.config.api['host']}:{api.config.api['port']}/api/report",
        headers=headers,
        json=data
    ) as response:
        # Check response
        assert response.status == 200
        report = await response.json()
        assert report["status"] == "completed"
        assert len(report["results"]) == 3

@pytest.mark.asyncio
async def test_unauthorized_request(
    api: APIIntegration,
    client: aiohttp.ClientSession
):
    """Test unauthorized request.

    Args:
        api: Test API integration
        client: Test client
    """
    # Send request without token
    async with client.post(
        f"http://{api.config.api['host']}:{api.config.api['port']}/api/sniff",
        json={}
    ) as response:
        # Check response
        assert response.status == 401

@pytest.mark.asyncio
async def test_invalid_request(
    api: APIIntegration,
    client: aiohttp.ClientSession
):
    """Test invalid request.

    Args:
        api: Test API integration
        client: Test client
    """
    # Send invalid request
    headers = {"Authorization": f"Bearer {api.config.api['auth']['token']}"}
    async with client.post(
        f"http://{api.config.api['host']}:{api.config.api['port']}/api/sniff",
        headers=headers,
        json={"invalid": "data"}
    ) as response:
        # Check response
        assert response.status == 400

@pytest.mark.asyncio
async def test_not_found(
    api: APIIntegration,
    client: aiohttp.ClientSession
):
    """Test not found endpoint.

    Args:
        api: Test API integration
        client: Test client
    """
    # Send request to invalid endpoint
    headers = {"Authorization": f"Bearer {api.config.api['auth']['token']}"}
    async with client.post(
        f"http://{api.config.api['host']}:{api.config.api['port']}/api/invalid",
        headers=headers,
        json={}
    ) as response:
        # Check response
        assert response.status == 404

@pytest.mark.asyncio
async def test_metrics(api: APIIntegration):
    """Test metrics collection.

    Args:
        api: Test API integration
    """
    # Get initial metrics
    metrics = api.get_metrics()
    assert metrics["active_jobs"] == 0
    assert metrics["request_count"] == 0
    assert metrics["error_count"] == 0
    assert metrics["status"] == "running"
