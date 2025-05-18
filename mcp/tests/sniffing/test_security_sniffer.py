"""
Tests for security domain sniffer.
"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from ...server.sniffing.domains.security import SecuritySniffer
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
        patterns_dir = temp_path / "patterns"
        rules_dir = temp_path / "rules"
        simulations_dir = temp_path / "simulations"

        # Create directories
        patterns_dir.mkdir()
        rules_dir.mkdir()
        simulations_dir.mkdir()

        # Create test config
        config = {
            "domains": {
                "security": {
                    "patterns_path": str(patterns_dir),
                    "rules_path": str(rules_dir),
                    "simulations_path": str(simulations_dir)
                }
            },
            "logging": {
                "level": "DEBUG",
                "format": "%(message)s",
                "file": str(temp_path / "test.log")
            }
        }

        # Create test patterns
        patterns = {
            "sql_injection": {
                "regex": "(SELECT|INSERT|UPDATE|DELETE|DROP).*\\bFROM\\b.*\\bWHERE\\b.*\\b(=|LIKE)\\b.*\\?|'.*\\+",
                "severity": "critical",
                "description": "SQL injection vulnerability"
            },
            "xss": {
                "regex": "\\b(innerHTML|outerHTML|document\\.write)\\b.*\\+",
                "severity": "critical",
                "description": "XSS vulnerability"
            }
        }
        with open(patterns_dir / "security.yaml", "w") as f:
            yaml.safe_dump(patterns, f)

        # Create test rules
        rules = {
            "authentication": {
                "type": "ast",
                "rules": {
                    "password_hash": {
                        "pattern": "password.*=.*hash\\(",
                        "severity": "critical",
                        "message": "Insecure password hashing"
                    }
                }
            }
        }
        with open(rules_dir / "security.yaml", "w") as f:
            yaml.safe_dump(rules, f)

        # Create test simulations
        simulations = {
            "sql_injection_sim": {
                "type": "injection",
                "payloads": ["' OR '1'='1"],
                "targets": ["SELECT.*FROM.*WHERE"]
            }
        }
        with open(simulations_dir / "security.yaml", "w") as f:
            yaml.safe_dump(simulations, f)

        yield MCPConfig(config)

@pytest.fixture
async def sniffer(config: MCPConfig) -> SecuritySniffer:
    """Create test sniffer.

    Args:
        config: Test configuration

    Returns:
        Test sniffer
    """
    sniffer = SecuritySniffer(config)
    await sniffer.start()
    yield sniffer
    await sniffer.stop()

@pytest.mark.asyncio
async def test_sniff_sql_injection(
    sniffer: SecuritySniffer,
    tmp_path: Path
):
    """Test SQL injection detection.

    Args:
        sniffer: Test sniffer
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function getUser(id) {
        return db.query('SELECT * FROM users WHERE id = ' + id);
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) == 1
    assert result["issues"][0]["type"] == "pattern"
    assert result["issues"][0]["name"] == "sql_injection"
    assert result["issues"][0]["severity"] == "critical"

@pytest.mark.asyncio
async def test_sniff_xss(
    sniffer: SecuritySniffer,
    tmp_path: Path
):
    """Test XSS detection.

    Args:
        sniffer: Test sniffer
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function displayUser(user) {
        element.innerHTML = '<div>' + user.name + '</div>';
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) == 1
    assert result["issues"][0]["type"] == "pattern"
    assert result["issues"][0]["name"] == "xss"
    assert result["issues"][0]["severity"] == "critical"

@pytest.mark.asyncio
async def test_sniff_password_hash(
    sniffer: SecuritySniffer,
    tmp_path: Path
):
    """Test password hash detection.

    Args:
        sniffer: Test sniffer
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function createUser(user) {
        user.password = hash(user.password);
        return db.insert(user);
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) == 1
    assert result["issues"][0]["type"] == "rule"
    assert result["issues"][0]["name"] == "password_hash"
    assert result["issues"][0]["severity"] == "critical"

@pytest.mark.asyncio
async def test_sniff_multiple_issues(
    sniffer: SecuritySniffer,
    tmp_path: Path
):
    """Test multiple issue detection.

    Args:
        sniffer: Test sniffer
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function createUser(user) {
        user.password = hash(user.password);
        const query = 'SELECT * FROM users WHERE id = ' + user.id;
        element.innerHTML = '<div>' + user.name + '</div>';
        return db.query(query);
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) == 3
    assert {issue["name"] for issue in result["issues"]} == {
        "password_hash",
        "sql_injection",
        "xss"
    }

@pytest.mark.asyncio
async def test_sniff_no_issues(
    sniffer: SecuritySniffer,
    tmp_path: Path
):
    """Test no issue detection.

    Args:
        sniffer: Test sniffer
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function getUser(id) {
        return db.query('SELECT * FROM users WHERE id = ?', [id]);
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Check result
    assert result["status"] == "completed"
    assert len(result["issues"]) == 0

@pytest.mark.asyncio
async def test_analyze_result(
    sniffer: SecuritySniffer,
    tmp_path: Path
):
    """Test result analysis.

    Args:
        sniffer: Test sniffer
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function createUser(user) {
        user.password = hash(user.password);
        const query = 'SELECT * FROM users WHERE id = ' + user.id;
        element.innerHTML = '<div>' + user.name + '</div>';
        return db.query(query);
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Run analysis
    analysis = await sniffer.analyze_result(str(test_file), result)

    # Check analysis
    assert analysis["status"] == "failed"
    assert analysis["summary"]["total"] == 3
    assert analysis["summary"]["critical"] == 3
    assert len(analysis["recommendations"]) == 3

@pytest.mark.asyncio
async def test_fix_issues(
    sniffer: SecuritySniffer,
    tmp_path: Path
):
    """Test issue fixing.

    Args:
        sniffer: Test sniffer
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function createUser(user) {
        user.password = hash(user.password);
        const query = 'SELECT * FROM users WHERE id = ' + user.id;
        element.innerHTML = '<div>' + user.name + '</div>';
        return db.query(query);
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Run fixes
    fixes = await sniffer.fix_issues(str(test_file), result["issues"])

    # Check fixes
    assert fixes["status"] == "completed"
    assert len(fixes["applied"]) == 3
    assert len(fixes["failed"]) == 0

    # Check fixed file
    fixed_content = test_file.read_text()
    assert "bcrypt.hash" in fixed_content
    assert "WHERE id = ?" in fixed_content
    assert "textContent" in fixed_content

@pytest.mark.asyncio
async def test_metrics(sniffer: SecuritySniffer):
    """Test metrics collection.

    Args:
        sniffer: Test sniffer
    """
    # Get initial metrics
    metrics = sniffer.get_metrics()
    assert metrics["active_jobs"] == 0
    assert metrics["stored_results"] == 0
    assert metrics["domain"] == "security"
    assert metrics["status"] == "running"
