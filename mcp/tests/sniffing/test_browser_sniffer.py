"""
Tests for browser domain sniffer.
"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml

from ...server.sniffing.domains.browser import BrowserSniffer
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
                "browser": {
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
            "performance": {
                "regex": "\\b(setTimeout|setInterval)\\b.*\\b(\\d{4,}|[1-9]\\d{3,})\\b",
                "severity": "high",
                "description": "Long timeout detected"
            },
            "memory_leak": {
                "regex": "\\b(addEventListener)\\b.*\\b(removeEventListener)\\b",
                "severity": "high",
                "description": "Potential memory leak"
            }
        }
        with open(patterns_dir / "browser.yaml", "w") as f:
            yaml.safe_dump(patterns, f)

        # Create test rules
        rules = {
            "performance": {
                "type": "ast",
                "rules": {
                    "dom_manipulation": {
                        "pattern": "document\\.getElementById\\(\\.\\*\\)\\.innerHTML",
                        "severity": "medium",
                        "message": "Inefficient DOM manipulation"
                    }
                }
            }
        }
        with open(rules_dir / "browser.yaml", "w") as f:
            yaml.safe_dump(rules, f)

        # Create test simulations
        simulations = {
            "performance_sim": {
                "type": "performance",
                "thresholds": {
                    "load_time": 1000,
                    "memory_usage": 50,
                    "cpu_usage": 80
                }
            }
        }
        with open(simulations_dir / "browser.yaml", "w") as f:
            yaml.safe_dump(simulations, f)

        yield MCPConfig(config)

@pytest.fixture
async def sniffer(config: MCPConfig) -> BrowserSniffer:
    """Create test sniffer.

    Args:
        config: Test configuration

    Returns:
        Test sniffer
    """
    sniffer = BrowserSniffer(config)
    await sniffer.start()
    yield sniffer
    await sniffer.stop()

@pytest.mark.asyncio
async def test_sniff_performance(
    sniffer: BrowserSniffer,
    tmp_path: Path
):
    """Test performance issue detection.

    Args:
        sniffer: Test sniffer
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function heavyOperation() {
        setTimeout(() => {
            console.log('Heavy operation');
        }, 5000);
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) == 1
    assert result["issues"][0]["type"] == "pattern"
    assert result["issues"][0]["name"] == "performance"
    assert result["issues"][0]["severity"] == "high"

@pytest.mark.asyncio
async def test_sniff_memory_leak(
    sniffer: BrowserSniffer,
    tmp_path: Path
):
    """Test memory leak detection.

    Args:
        sniffer: Test sniffer
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function addHandler() {
        element.addEventListener('click', handler);
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) == 1
    assert result["issues"][0]["type"] == "pattern"
    assert result["issues"][0]["name"] == "memory_leak"
    assert result["issues"][0]["severity"] == "high"

@pytest.mark.asyncio
async def test_sniff_dom_manipulation(
    sniffer: BrowserSniffer,
    tmp_path: Path
):
    """Test DOM manipulation detection.

    Args:
        sniffer: Test sniffer
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function updateContent() {
        document.getElementById('content').innerHTML = 'New content';
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) == 1
    assert result["issues"][0]["type"] == "rule"
    assert result["issues"][0]["name"] == "dom_manipulation"
    assert result["issues"][0]["severity"] == "medium"

@pytest.mark.asyncio
async def test_sniff_multiple_issues(
    sniffer: BrowserSniffer,
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
    function problematicCode() {
        setTimeout(() => {
            document.getElementById('content').innerHTML = 'New content';
        }, 5000);
        element.addEventListener('click', handler);
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) == 3
    assert {issue["name"] for issue in result["issues"]} == {
        "performance",
        "memory_leak",
        "dom_manipulation"
    }

@pytest.mark.asyncio
async def test_sniff_no_issues(
    sniffer: BrowserSniffer,
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
    function goodCode() {
        setTimeout(() => {
            console.log('Quick operation');
        }, 100);
        const content = document.getElementById('content');
        content.textContent = 'New content';
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Check result
    assert result["status"] == "completed"
    assert len(result["issues"]) == 0

@pytest.mark.asyncio
async def test_analyze_result(
    sniffer: BrowserSniffer,
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
    function problematicCode() {
        setTimeout(() => {
            document.getElementById('content').innerHTML = 'New content';
        }, 5000);
        element.addEventListener('click', handler);
    }
    """)

    # Run sniffing
    result = await sniffer.sniff_file(str(test_file))

    # Run analysis
    analysis = await sniffer.analyze_result(str(test_file), result)

    # Check analysis
    assert analysis["status"] == "failed"
    assert analysis["summary"]["total"] == 3
    assert analysis["summary"]["high"] == 2
    assert analysis["summary"]["medium"] == 1
    assert len(analysis["recommendations"]) == 3

@pytest.mark.asyncio
async def test_fix_issues(
    sniffer: BrowserSniffer,
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
    function problematicCode() {
        setTimeout(() => {
            document.getElementById('content').innerHTML = 'New content';
        }, 5000);
        element.addEventListener('click', handler);
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
    assert "1000" in fixed_content
    assert "textContent" in fixed_content
    assert "removeEventListener" in fixed_content

@pytest.mark.asyncio
async def test_performance_simulation(
    sniffer: BrowserSniffer,
    tmp_path: Path
):
    """Test performance simulation.

    Args:
        sniffer: Test sniffer
        tmp_path: Temporary directory
    """
    # Create test file
    test_file = tmp_path / "test.js"
    test_file.write_text("""
    function heavyOperation() {
        const data = new Array(1000000).fill(0);
        data.forEach(item => {
            console.log(item);
        });
    }
    """)

    # Run simulation
    result = await sniffer.run_simulation(
        str(test_file),
        "performance_sim"
    )

    # Check result
    assert result["status"] == "failed"
    assert len(result["issues"]) > 0
    assert result["metrics"]["cpu_usage"] > 80
    assert result["metrics"]["memory_usage"] > 50

@pytest.mark.asyncio
async def test_metrics(sniffer: BrowserSniffer):
    """Test metrics collection.

    Args:
        sniffer: Test sniffer
    """
    # Get initial metrics
    metrics = sniffer.get_metrics()
    assert metrics["active_jobs"] == 0
    assert metrics["stored_results"] == 0
    assert metrics["domain"] == "browser"
    assert metrics["status"] == "running"
