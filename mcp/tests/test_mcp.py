"""
MCP test suite.
"""
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pytest
import yaml
from aiohttp import web

from ..server.analyzer import MCPAnalyzer
from ..server.fixer import MCPFixer
from ..server.isolator import MCPIsolator
from ..server.orchestrator import MCPOrchestrator
from ..utils.api import APIIntegration
from ..utils.ci_cd import CICDIntegration
from ..utils.config import MCPConfig
from ..utils.git import GitIntegration
from ..utils.logging import setup_logger

logger = logging.getLogger("mcp_test")

@pytest.fixture
async def config() -> MCPConfig:
    """Create test configuration.

    Returns:
        Test configuration
    """
    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    return MCPConfig(str(config_path))

@pytest.fixture
async def orchestrator(config: MCPConfig) -> MCPOrchestrator:
    """Create test orchestrator.

    Args:
        config: Test configuration

    Returns:
        Test orchestrator
    """
    # Create orchestrator
    orchestrator = MCPOrchestrator(config)
    await orchestrator.start()
    yield orchestrator
    await orchestrator.stop()

@pytest.fixture
async def isolator(config: MCPConfig) -> MCPIsolator:
    """Create test isolator.

    Args:
        config: Test configuration

    Returns:
        Test isolator
    """
    # Create isolator
    isolator = MCPIsolator(config)
    await isolator.start()
    yield isolator
    await isolator.stop()

@pytest.fixture
async def analyzer(config: MCPConfig) -> MCPAnalyzer:
    """Create test analyzer.

    Args:
        config: Test configuration

    Returns:
        Test analyzer
    """
    # Create analyzer
    analyzer = MCPAnalyzer(config)
    await analyzer.start()
    yield analyzer
    await analyzer.stop()

@pytest.fixture
async def fixer(config: MCPConfig) -> MCPFixer:
    """Create test fixer.

    Args:
        config: Test configuration

    Returns:
        Test fixer
    """
    # Create fixer
    fixer = MCPFixer(config)
    await fixer.start()
    yield fixer
    await fixer.stop()

@pytest.fixture
async def api(config: MCPConfig) -> APIIntegration:
    """Create test API integration.

    Args:
        config: Test configuration

    Returns:
        Test API integration
    """
    # Create API integration
    api = APIIntegration(config)
    await api.start()
    yield api
    await api.stop()

@pytest.fixture
async def ci_cd(config: MCPConfig) -> CICDIntegration:
    """Create test CI/CD integration.

    Args:
        config: Test configuration

    Returns:
        Test CI/CD integration
    """
    # Create CI/CD integration
    ci_cd = CICDIntegration(config)
    await ci_cd.start()
    yield ci_cd
    await ci_cd.stop()

@pytest.fixture
def git(config: MCPConfig) -> GitIntegration:
    """Create test Git integration.

    Args:
        config: Test configuration

    Returns:
        Test Git integration
    """
    # Create Git integration
    return GitIntegration(config)

@pytest.mark.asyncio
async def test_orchestrator(
    orchestrator: MCPOrchestrator,
    config: MCPConfig
):
    """Test orchestrator.

    Args:
        orchestrator: Test orchestrator
        config: Test configuration
    """
    # Schedule job
    job_id = await orchestrator.schedule_job(
        "sniff",
        files=["test_file.py"],
        domains=["security"],
        priority=1
    )
    assert job_id is not None

    # Get job status
    status = await orchestrator.get_job_status(job_id)
    assert status is not None
    assert status["status"] in ["queued", "running", "completed", "failed"]

    # Get metrics
    metrics = orchestrator.get_metrics()
    assert metrics is not None
    assert "jobs" in metrics

@pytest.mark.asyncio
async def test_isolator(
    isolator: MCPIsolator,
    config: MCPConfig
):
    """Test isolator.

    Args:
        isolator: Test isolator
        config: Test configuration
    """
    # Create isolation
    isolation_id = await isolator.create_isolation(
        files=["test_file.py"],
        domains=["security"]
    )
    assert isolation_id is not None

    # Get isolation status
    status = await isolator.get_isolation_status(isolation_id)
    assert status is not None
    assert status["status"] in ["created", "running", "completed", "failed"]

    # Get metrics
    metrics = isolator.get_metrics()
    assert metrics is not None
    assert "isolations" in metrics

@pytest.mark.asyncio
async def test_analyzer(
    analyzer: MCPAnalyzer,
    config: MCPConfig
):
    """Test analyzer.

    Args:
        analyzer: Test analyzer
        config: Test configuration
    """
    # Create analysis
    analysis_id = await analyzer.create_analysis(
        job_id="test_job",
        domains=["security"]
    )
    assert analysis_id is not None

    # Get analysis status
    status = await analyzer.get_analysis_status(analysis_id)
    assert status is not None
    assert status["status"] in ["created", "running", "completed", "failed"]

    # Get metrics
    metrics = analyzer.get_metrics()
    assert metrics is not None
    assert "analyses" in metrics

@pytest.mark.asyncio
async def test_fixer(
    fixer: MCPFixer,
    config: MCPConfig
):
    """Test fixer.

    Args:
        fixer: Test fixer
        config: Test configuration
    """
    # Create fixes
    fix_id = await fixer.create_fixes(
        analysis_id="test_analysis",
        domains=["security"]
    )
    assert fix_id is not None

    # Get fix status
    status = await fixer.get_fix_status(fix_id)
    assert status is not None
    assert status["status"] in ["created", "running", "completed", "failed"]

    # Get metrics
    metrics = fixer.get_metrics()
    assert metrics is not None
    assert "fixes" in metrics

@pytest.mark.asyncio
async def test_api(
    api: APIIntegration,
    config: MCPConfig
):
    """Test API integration.

    Args:
        api: Test API integration
        config: Test configuration
    """
    # Test endpoint
    results = await api.test_endpoint(
        "GET",
        "http://localhost:8001/test",
        expected_status=404
    )
    assert results is not None
    assert results["metrics"]["success"] is True

    # Get metrics
    metrics = api.get_metrics()
    assert metrics is not None
    assert "metrics" in metrics

@pytest.mark.asyncio
async def test_ci_cd(
    ci_cd: CICDIntegration,
    config: MCPConfig
):
    """Test CI/CD integration.

    Args:
        ci_cd: Test CI/CD integration
        config: Test configuration
    """
    # Run pipeline
    results = await ci_cd.run_pipeline(
        pipeline={
            "stages": {
                "test": {
                    "steps": {
                        "test": {
                            "type": "test",
                            "test_type": "unit"
                        }
                    }
                }
            }
        },
        context={}
    )
    assert results is not None
    assert results["status"] in ["completed", "failed"]

    # Get metrics
    metrics = ci_cd.get_metrics()
    assert metrics is not None
    assert "metrics" in metrics

def test_git(
    git: GitIntegration,
    config: MCPConfig
):
    """Test Git integration.

    Args:
        git: Test Git integration
        config: Test configuration
    """
    # Get changed files
    files = git.get_changed_files()
    assert isinstance(files, list)

    # Get current branch
    branch = git.get_current_branch()
    assert branch is not None

    # Get metrics
    metrics = git.get_status()
    assert metrics is not None
    assert "branch" in metrics

@pytest.mark.asyncio
async def test_full_pipeline(
    orchestrator: MCPOrchestrator,
    isolator: MCPIsolator,
    analyzer: MCPAnalyzer,
    fixer: MCPFixer,
    config: MCPConfig
):
    """Test full pipeline.

    Args:
        orchestrator: Test orchestrator
        isolator: Test isolator
        analyzer: Test analyzer
        fixer: Test fixer
        config: Test configuration
    """
    # Schedule job
    job_id = await orchestrator.schedule_job(
        "sniff",
        files=["test_file.py"],
        domains=["security"],
        priority=1
    )
    assert job_id is not None

    # Wait for job completion
    while True:
        status = await orchestrator.get_job_status(job_id)
        if status["status"] in ["completed", "failed"]:
            break
        await asyncio.sleep(1)

    # Create analysis
    analysis_id = await analyzer.create_analysis(
        job_id=job_id,
        domains=["security"]
    )
    assert analysis_id is not None

    # Wait for analysis completion
    while True:
        status = await analyzer.get_analysis_status(analysis_id)
        if status["status"] in ["completed", "failed"]:
            break
        await asyncio.sleep(1)

    # Create fixes
    fix_id = await fixer.create_fixes(
        analysis_id=analysis_id,
        domains=["security"]
    )
    assert fix_id is not None

    # Wait for fix completion
    while True:
        status = await fixer.get_fix_status(fix_id)
        if status["status"] in ["completed", "failed"]:
            break
        await asyncio.sleep(1)

    # Get metrics
    metrics = {
        "orchestrator": orchestrator.get_metrics(),
        "isolator": isolator.get_metrics(),
        "analyzer": analyzer.get_metrics(),
        "fixer": fixer.get_metrics()
    }
    assert all(m is not None for m in metrics.values())
