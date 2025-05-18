"""
Tests for CI/CD integration.
"""
import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from ...server.sniffing.ci_cd import CICDIntegration
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
            "ci_cd": {
                "enabled": True,
                "providers": {
                    "github": {
                        "enabled": True,
                        "token": "test_token",
                        "owner": "test_owner",
                        "repo": "test_repo",
                        "branch": "main"
                    },
                    "gitlab": {
                        "enabled": True,
                        "token": "test_token",
                        "project_id": "test_project",
                        "branch": "main"
                    }
                },
                "actions": {
                    "on_push": True,
                    "on_pull_request": True,
                    "on_merge": True
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
async def ci_cd(config: MCPConfig) -> CICDIntegration:
    """Create test CI/CD integration.

    Args:
        config: Test configuration

    Returns:
        Test CI/CD integration
    """
    ci_cd = CICDIntegration(config)
    await ci_cd.start()
    yield ci_cd
    await ci_cd.stop()

@pytest.mark.asyncio
async def test_github_push(
    ci_cd: CICDIntegration,
    tmp_path: Path
):
    """Test GitHub push event.

    Args:
        ci_cd: Test CI/CD integration
        tmp_path: Temporary directory
    """
    # Create test event
    event = {
        "provider": "github",
        "type": "push",
        "branch": "main",
        "commit": "test_commit",
        "files": [
            {
                "path": "test.js",
                "content": """
                function getUser(id) {
                    return db.query('SELECT * FROM users WHERE id = ' + id);
                }
                """
            }
        ]
    }

    # Process event
    result = await ci_cd.process_event(event)

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) > 0
    assert result["provider"] == "github"
    assert result["type"] == "push"

@pytest.mark.asyncio
async def test_github_pull_request(
    ci_cd: CICDIntegration,
    tmp_path: Path
):
    """Test GitHub pull request event.

    Args:
        ci_cd: Test CI/CD integration
        tmp_path: Temporary directory
    """
    # Create test event
    event = {
        "provider": "github",
        "type": "pull_request",
        "branch": "feature",
        "base": "main",
        "number": 1,
        "files": [
            {
                "path": "test.js",
                "content": """
                function getUser(id) {
                    return db.query('SELECT * FROM users WHERE id = ?', [id]);
                }
                """
            }
        ]
    }

    # Process event
    result = await ci_cd.process_event(event)

    # Check result
    assert result["status"] == "completed"
    assert len(result["issues"]) == 0
    assert result["provider"] == "github"
    assert result["type"] == "pull_request"

@pytest.mark.asyncio
async def test_gitlab_push(
    ci_cd: CICDIntegration,
    tmp_path: Path
):
    """Test GitLab push event.

    Args:
        ci_cd: Test CI/CD integration
        tmp_path: Temporary directory
    """
    # Create test event
    event = {
        "provider": "gitlab",
        "type": "push",
        "branch": "main",
        "commit": "test_commit",
        "files": [
            {
                "path": "test.js",
                "content": """
                function getUser(id) {
                    return db.query('SELECT * FROM users WHERE id = ' + id);
                }
                """
            }
        ]
    }

    # Process event
    result = await ci_cd.process_event(event)

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) > 0
    assert result["provider"] == "gitlab"
    assert result["type"] == "push"

@pytest.mark.asyncio
async def test_gitlab_merge_request(
    ci_cd: CICDIntegration,
    tmp_path: Path
):
    """Test GitLab merge request event.

    Args:
        ci_cd: Test CI/CD integration
        tmp_path: Temporary directory
    """
    # Create test event
    event = {
        "provider": "gitlab",
        "type": "merge_request",
        "branch": "feature",
        "target": "main",
        "number": 1,
        "files": [
            {
                "path": "test.js",
                "content": """
                function getUser(id) {
                    return db.query('SELECT * FROM users WHERE id = ?', [id]);
                }
                """
            }
        ]
    }

    # Process event
    result = await ci_cd.process_event(event)

    # Check result
    assert result["status"] == "completed"
    assert len(result["issues"]) == 0
    assert result["provider"] == "gitlab"
    assert result["type"] == "merge_request"

@pytest.mark.asyncio
async def test_github_status(
    ci_cd: CICDIntegration,
    tmp_path: Path
):
    """Test GitHub status update.

    Args:
        ci_cd: Test CI/CD integration
        tmp_path: Temporary directory
    """
    # Create test status
    status = {
        "provider": "github",
        "commit": "test_commit",
        "state": "failure",
        "description": "Security issues found",
        "context": "security/sniffing"
    }

    # Update status
    result = await ci_cd.update_status(status)

    # Check result
    assert result["status"] == "completed"
    assert result["provider"] == "github"
    assert result["commit"] == "test_commit"

@pytest.mark.asyncio
async def test_gitlab_status(
    ci_cd: CICDIntegration,
    tmp_path: Path
):
    """Test GitLab status update.

    Args:
        ci_cd: Test CI/CD integration
        tmp_path: Temporary directory
    """
    # Create test status
    status = {
        "provider": "gitlab",
        "commit": "test_commit",
        "state": "failed",
        "description": "Security issues found",
        "name": "security/sniffing"
    }

    # Update status
    result = await ci_cd.update_status(status)

    # Check result
    assert result["status"] == "completed"
    assert result["provider"] == "gitlab"
    assert result["commit"] == "test_commit"

@pytest.mark.asyncio
async def test_github_comment(
    ci_cd: CICDIntegration,
    tmp_path: Path
):
    """Test GitHub comment creation.

    Args:
        ci_cd: Test CI/CD integration
        tmp_path: Temporary directory
    """
    # Create test comment
    comment = {
        "provider": "github",
        "type": "pull_request",
        "number": 1,
        "body": "Security issues found:\n- SQL injection vulnerability"
    }

    # Create comment
    result = await ci_cd.create_comment(comment)

    # Check result
    assert result["status"] == "completed"
    assert result["provider"] == "github"
    assert result["type"] == "pull_request"

@pytest.mark.asyncio
async def test_gitlab_comment(
    ci_cd: CICDIntegration,
    tmp_path: Path
):
    """Test GitLab comment creation.

    Args:
        ci_cd: Test CI/CD integration
        tmp_path: Temporary directory
    """
    # Create test comment
    comment = {
        "provider": "gitlab",
        "type": "merge_request",
        "number": 1,
        "body": "Security issues found:\n- SQL injection vulnerability"
    }

    # Create comment
    result = await ci_cd.create_comment(comment)

    # Check result
    assert result["status"] == "completed"
    assert result["provider"] == "gitlab"
    assert result["type"] == "merge_request"

@pytest.mark.asyncio
async def test_report_generation(
    ci_cd: CICDIntegration,
    tmp_path: Path
):
    """Test report generation.

    Args:
        ci_cd: Test CI/CD integration
        tmp_path: Temporary directory
    """
    # Create test results
    results = []
    for i in range(3):
        result = {
            "file": f"test_{i}.js",
            "status": "completed",
            "timestamp": "2024-01-01T00:00:00",
            "issues": []
        }
        results.append(result)

    # Generate report
    report = await ci_cd.generate_report(results)

    # Check report
    assert report["status"] == "completed"
    assert len(report["results"]) == 3
    assert "summary" in report
    assert "recommendations" in report

@pytest.mark.asyncio
async def test_metrics(ci_cd: CICDIntegration):
    """Test metrics collection.

    Args:
        ci_cd: Test CI/CD integration
    """
    # Get initial metrics
    metrics = ci_cd.get_metrics()
    assert metrics["active_jobs"] == 0
    assert metrics["event_count"] == 0
    assert metrics["status_count"] == 0
    assert metrics["comment_count"] == 0
    assert metrics["status"] == "running"
    assert "providers" in metrics
