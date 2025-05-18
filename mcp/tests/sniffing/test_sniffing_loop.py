"""
Tests for sniffing loop.
"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from ...server.sniffing.loop import SniffingLoop
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
        domains_dir = temp_path / "domains"
        reports_dir = temp_path / "reports"

        # Create directories
        domains_dir.mkdir()
        reports_dir.mkdir()

        # Create test config
        config = {
            "domains": {
                "security": {
                    "enabled": True,
                    "patterns_path": str(domains_dir / "security" / "patterns"),
                    "rules_path": str(domains_dir / "security" / "rules"),
                    "simulations_path": str(domains_dir / "security" / "simulations")
                },
                "browser": {
                    "enabled": True,
                    "patterns_path": str(domains_dir / "browser" / "patterns"),
                    "rules_path": str(domains_dir / "browser" / "rules"),
                    "simulations_path": str(domains_dir / "browser" / "simulations")
                }
            },
            "report_path": str(reports_dir),
            "logging": {
                "level": "DEBUG",
                "format": "%(message)s",
                "file": str(temp_path / "test.log")
            }
        }

        # Create domain directories
        for domain in ["security", "browser"]:
            domain_dir = domains_dir / domain
            domain_dir.mkdir()
            (domain_dir / "patterns").mkdir()
            (domain_dir / "rules").mkdir()
            (domain_dir / "simulations").mkdir()

        yield MCPConfig(config)

@pytest.fixture
async def loop(config: MCPConfig) -> SniffingLoop:
    """Create test sniffing loop.

    Args:
        config: Test configuration

    Returns:
        Test sniffing loop
    """
    loop = SniffingLoop(config)
    await loop.start()
    yield loop
    await loop.stop()

@pytest.mark.asyncio
async def test_add_file(
    loop: SniffingLoop,
    tmp_path: Path
):
    """Test adding file to queue.

    Args:
        loop: Test sniffing loop
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("console.log('test');")

    # Add file
    job_id = await loop.add_file(str(test_file))

    # Check job
    assert job_id is not None
    assert job_id in loop.active_jobs

@pytest.mark.asyncio
async def test_process_file(
    loop: SniffingLoop,
    tmp_path: Path
):
    """Test file processing.

    Args:
        loop: Test sniffing loop
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function getUser(id) {
        return db.query('SELECT * FROM users WHERE id = ' + id);
    }
    """)

    # Add file
    job_id = await loop.add_file(str(test_file))

    # Wait for processing
    while job_id in loop.active_jobs:
        await asyncio.sleep(0.1)

    # Check result
    assert test_file in loop.results_cache
    result = loop.results_cache[test_file]["result"]
    assert result["status"] == "failed"
    assert len(result["issues"]) > 0

@pytest.mark.asyncio
async def test_process_multiple_files(
    loop: SniffingLoop,
    tmp_path: Path
):
    """Test multiple file processing.

    Args:
        loop: Test sniffing loop
        tmp_path: Temporary directory
    """
    # Create test files
    files = []
    for i in range(3):
        test_file = tmp_path / f"test_{i}.js"
        test_file.write_text(f"console.log('test {i}');")
        files.append(test_file)

    # Add files
    job_ids = []
    for file in files:
        job_id = await loop.add_file(str(file))
        job_ids.append(job_id)

    # Wait for processing
    while any(job_id in loop.active_jobs for job_id in job_ids):
        await asyncio.sleep(0.1)

    # Check results
    for file in files:
        assert str(file) in loop.results_cache
        result = loop.results_cache[str(file)]["result"]
        assert result["status"] == "completed"

@pytest.mark.asyncio
async def test_process_specific_domains(
    loop: SniffingLoop,
    tmp_path: Path
):
    """Test domain-specific processing.

    Args:
        loop: Test sniffing loop
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function getUser(id) {
        return db.query('SELECT * FROM users WHERE id = ' + id);
    }
    """)

    # Add file with specific domains
    job_id = await loop.add_file(
        str(test_file),
        domains=["security"]
    )

    # Wait for processing
    while job_id in loop.active_jobs:
        await asyncio.sleep(0.1)

    # Check result
    assert str(test_file) in loop.results_cache
    result = loop.results_cache[str(test_file)]["result"]
    assert "security" in result
    assert "browser" not in result

@pytest.mark.asyncio
async def test_file_locking(
    loop: SniffingLoop,
    tmp_path: Path
):
    """Test file locking mechanism.

    Args:
        loop: Test sniffing loop
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("console.log('test');")

    # Add file multiple times
    job_ids = []
    for _ in range(3):
        job_id = await loop.add_file(str(test_file))
        job_ids.append(job_id)

    # Wait for processing
    while any(job_id in loop.active_jobs for job_id in job_ids):
        await asyncio.sleep(0.1)

    # Check lock cleanup
    assert str(test_file) not in loop.file_locks

@pytest.mark.asyncio
async def test_result_caching(
    loop: SniffingLoop,
    tmp_path: Path
):
    """Test result caching.

    Args:
        loop: Test sniffing loop
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("console.log('test');")

    # Add file
    job_id = await loop.add_file(str(test_file))

    # Wait for processing
    while job_id in loop.active_jobs:
        await asyncio.sleep(0.1)

    # Check cache
    assert str(test_file) in loop.results_cache
    cached_result = loop.results_cache[str(test_file)]
    assert "result" in cached_result
    assert "timestamp" in cached_result

@pytest.mark.asyncio
async def test_domain_queues(
    loop: SniffingLoop,
    tmp_path: Path
):
    """Test domain queues.

    Args:
        loop: Test sniffing loop
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function getUser(id) {
        return db.query('SELECT * FROM users WHERE id = ' + id);
    }
    """)

    # Add file
    job_id = await loop.add_file(str(test_file))

    # Wait for processing
    while job_id in loop.active_jobs:
        await asyncio.sleep(0.1)

    # Check domain queues
    for domain in ["security", "browser"]:
        assert domain in loop.domain_queues
        assert loop.domain_queues[domain].empty()

@pytest.mark.asyncio
async def test_metrics(loop: SniffingLoop):
    """Test metrics collection.

    Args:
        loop: Test sniffing loop
    """
    # Get initial metrics
    metrics = loop.get_metrics()
    assert metrics["active_jobs"] == 0
    assert metrics["queued_files"] == 0
    assert metrics["cached_results"] == 0
    assert metrics["file_locks"] == 0
    assert "domain_queues" in metrics

@pytest.mark.asyncio
async def test_error_handling(
    loop: SniffingLoop,
    tmp_path: Path
):
    """Test error handling.

    Args:
        loop: Test sniffing loop
        tmp_path: Temporary directory
    """
    # Create invalid file
    test_file = tmp_path / "test.js"
    test_file.write_text("invalid { syntax")

    # Add file
    job_id = await loop.add_file(str(test_file))

    # Wait for processing
    while job_id in loop.active_jobs:
        await asyncio.sleep(0.1)

    # Check result
    assert str(test_file) in loop.results_cache
    result = loop.results_cache[str(test_file)]["result"]
    assert result["status"] == "failed"
    assert "error" in result
