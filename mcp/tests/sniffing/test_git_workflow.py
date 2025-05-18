"""
Tests for Git workflow integration.
"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml
from git import Repo

from ...server.sniffing.workflow import GitWorkflow
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
        git_dir = temp_path / "git"
        reports_dir = temp_path / "reports"

        # Create directories
        git_dir.mkdir()
        reports_dir.mkdir()

        # Initialize test repo
        repo = Repo.init(git_dir)
        config_file = git_dir / "config.yaml"
        config_file.write_text("test: true")
        repo.index.add([str(config_file)])
        repo.index.commit("Initial commit")

        # Create test config
        config = {
            "git": {
                "repo_path": str(git_dir),
                "main_branch": "main",
                "hooks": {
                    "pre_commit": True,
                    "pre_push": True
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
async def workflow(config: MCPConfig) -> GitWorkflow:
    """Create test Git workflow.

    Args:
        config: Test configuration

    Returns:
        Test Git workflow
    """
    workflow = GitWorkflow(config)
    await workflow.start()
    yield workflow
    await workflow.stop()

@pytest.mark.asyncio
async def test_install_hooks(
    workflow: GitWorkflow,
    tmp_path: Path
):
    """Test installing Git hooks.

    Args:
        workflow: Test Git workflow
        tmp_path: Temporary directory
    """
    # Install hooks
    await workflow.install_hooks()

    # Check hooks
    hooks_dir = Path(workflow.config.git["repo_path"]) / ".git" / "hooks"
    assert (hooks_dir / "pre-commit").exists()
    assert (hooks_dir / "pre-push").exists()

@pytest.mark.asyncio
async def test_pre_commit_hook(
    workflow: GitWorkflow,
    tmp_path: Path
):
    """Test pre-commit hook.

    Args:
        workflow: Test Git workflow
        tmp_path: Temporary directory
    """
    # Create test file
    repo_path = Path(workflow.config.git["repo_path"])
    test_file = repo_path / "test.js"
    test_file.write_text("""
    function getUser(id) {
        return db.query('SELECT * FROM users WHERE id = ' + id);
    }
    """)

    # Add file
    repo = Repo(repo_path)
    repo.index.add([str(test_file)])

    # Run pre-commit
    result = await workflow.run_pre_commit()

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) > 0
    assert not repo.index.diff("HEAD")

@pytest.mark.asyncio
async def test_pre_push_hook(
    workflow: GitWorkflow,
    tmp_path: Path
):
    """Test pre-push hook.

    Args:
        workflow: Test Git workflow
        tmp_path: Temporary directory
    """
    # Create test file
    repo_path = Path(workflow.config.git["repo_path"])
    test_file = repo_path / "test.js"
    test_file.write_text("""
    function getUser(id) {
        return db.query('SELECT * FROM users WHERE id = ?', [id]);
    }
    """)

    # Add and commit file
    repo = Repo(repo_path)
    repo.index.add([str(test_file)])
    repo.index.commit("Add test file")

    # Run pre-push
    result = await workflow.run_pre_push()

    # Check result
    assert result["status"] == "completed"
    assert len(result["issues"]) == 0

@pytest.mark.asyncio
async def test_sniff_staged_files(
    workflow: GitWorkflow,
    tmp_path: Path
):
    """Test sniffing staged files.

    Args:
        workflow: Test Git workflow
        tmp_path: Temporary directory
    """
    # Create test files
    repo_path = Path(workflow.config.git["repo_path"])
    files = []
    for i in range(3):
        test_file = repo_path / f"test_{i}.js"
        test_file.write_text(f"console.log('test {i}');")
        files.append(test_file)

    # Stage files
    repo = Repo(repo_path)
    repo.index.add([str(file) for file in files])

    # Run sniffing
    results = await workflow.sniff_staged_files()

    # Check results
    assert len(results) == 3
    assert all(result["status"] == "completed" for result in results)

@pytest.mark.asyncio
async def test_sniff_committed_files(
    workflow: GitWorkflow,
    tmp_path: Path
):
    """Test sniffing committed files.

    Args:
        workflow: Test Git workflow
        tmp_path: Temporary directory
    """
    # Create test files
    repo_path = Path(workflow.config.git["repo_path"])
    files = []
    for i in range(3):
        test_file = repo_path / f"test_{i}.js"
        test_file.write_text(f"console.log('test {i}');")
        files.append(test_file)

    # Add and commit files
    repo = Repo(repo_path)
    repo.index.add([str(file) for file in files])
    repo.index.commit("Add test files")

    # Run sniffing
    results = await workflow.sniff_committed_files()

    # Check results
    assert len(results) == 3
    assert all(result["status"] == "completed" for result in results)

@pytest.mark.asyncio
async def test_sniff_branch_files(
    workflow: GitWorkflow,
    tmp_path: Path
):
    """Test sniffing branch files.

    Args:
        workflow: Test Git workflow
        tmp_path: Temporary directory
    """
    # Create test files
    repo_path = Path(workflow.config.git["repo_path"])
    files = []
    for i in range(3):
        test_file = repo_path / f"test_{i}.js"
        test_file.write_text(f"console.log('test {i}');")
        files.append(test_file)

    # Create branch and add files
    repo = Repo(repo_path)
    repo.git.checkout("-b", "feature")
    repo.index.add([str(file) for file in files])
    repo.index.commit("Add test files")

    # Run sniffing
    results = await workflow.sniff_branch_files("feature")

    # Check results
    assert len(results) == 3
    assert all(result["status"] == "completed" for result in results)

@pytest.mark.asyncio
async def test_fix_branch_issues(
    workflow: GitWorkflow,
    tmp_path: Path
):
    """Test fixing branch issues.

    Args:
        workflow: Test Git workflow
        tmp_path: Temporary directory
    """
    # Create test file
    repo_path = Path(workflow.config.git["repo_path"])
    test_file = repo_path / "test.js"
    test_file.write_text("""
    function getUser(id) {
        return db.query('SELECT * FROM users WHERE id = ' + id);
    }
    """)

    # Create branch and add file
    repo = Repo(repo_path)
    repo.git.checkout("-b", "feature")
    repo.index.add([str(test_file)])
    repo.index.commit("Add test file")

    # Run fixes
    result = await workflow.fix_branch_issues("feature")

    # Check result
    assert result["status"] == "completed"
    assert len(result["fixes"]) > 0
    assert "WHERE id = ?" in test_file.read_text()

@pytest.mark.asyncio
async def test_report_generation(
    workflow: GitWorkflow,
    tmp_path: Path
):
    """Test report generation.

    Args:
        workflow: Test Git workflow
        tmp_path: Temporary directory
    """
    # Create test file
    repo_path = Path(workflow.config.git["repo_path"])
    test_file = repo_path / "test.js"
    test_file.write_text("""
    function getUser(id) {
        return db.query('SELECT * FROM users WHERE id = ' + id);
    }
    """)

    # Add and commit file
    repo = Repo(repo_path)
    repo.index.add([str(test_file)])
    repo.index.commit("Add test file")

    # Generate report
    report = await workflow.generate_report("main")

    # Check report
    assert report["branch"] == "main"
    assert report["status"] == "failed"
    assert len(report["issues"]) > 0
    assert len(report["recommendations"]) > 0

@pytest.mark.asyncio
async def test_metrics(workflow: GitWorkflow):
    """Test metrics collection.

    Args:
        workflow: Test Git workflow
    """
    # Get initial metrics
    metrics = workflow.get_metrics()
    assert metrics["active_jobs"] == 0
    assert metrics["hook_queue"] == 0
    assert metrics["status"] == "running"
    assert "hooks" in metrics
