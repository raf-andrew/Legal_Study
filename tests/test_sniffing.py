"""
Test suite for sniffing infrastructure.
"""
import asyncio
import json
import os
import pytest
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from sniffing.core.base_sniffer import BaseSniffer, SnifferType, SniffingResult
from sniffing.mcp.server.mcp_server import MCPServer
from sniffing.mcp.orchestration.sniffing_loop import SniffingLoop
from sniffing.domains.security.security_sniffer import SecuritySniffer
from sniffing.domains.browser.browser_sniffer import BrowserSniffer
from sniffing.domains.functional.functional_sniffer import FunctionalSniffer
from sniffing.domains.unit.unit_sniffer import UnitSniffer
from sniffing.domains.documentation.documentation_sniffer import DocumentationSniffer

# Test configuration
TEST_CONFIG = {
    "mcp": {
        "host": "localhost",
        "port": 8000,
        "auto_fix": True,
        "report_path": "test_reports",
        "metrics_path": "test_metrics",
        "alerts_path": "test_alerts",
        "health_path": "test_health"
    },
    "ai": {
        "model_path": "test_models",
        "model": "microsoft/codebert-base",
        "confidence_threshold": 0.8
    },
    "sniffing": {
        "report_path": "test_reports",
        "parallel": True,
        "max_workers": 2
    }
}

@pytest.fixture
async def mcp_server():
    """Create MCP server instance."""
    server = MCPServer(TEST_CONFIG)
    yield server
    await server.stop()

@pytest.fixture
async def sniffing_loop():
    """Create sniffing loop instance."""
    loop = SniffingLoop(TEST_CONFIG["sniffing"])
    yield loop
    await loop.stop()

@pytest.fixture
def test_file(tmp_path):
    """Create a test file with known issues."""
    file_content = '''
def process_user_input(user_input):
    """Process user input.

    Args:
        user_input: The user input to process.
    """
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_input}"

    # XSS vulnerability
    document.innerHTML = user_input

    # Command injection vulnerability
    os.system(f"process {user_input}")

    # Missing return section in docstring
    return query
'''
    file_path = tmp_path / "test_file.py"
    file_path.write_text(file_content)
    return file_path

class TestSniffingInfrastructure:
    """Test sniffing infrastructure components."""

    async def test_single_file_sniffing(self, mcp_server, test_file):
        """Test sniffing a single file."""
        # Add file to sniffing
        result = await mcp_server.run_file_sniffing(str(test_file), ["security"])

        # Verify result
        assert result["status"] == "success"
        assert len(result["issues"]) > 0

        # Check for security issues
        security_issues = [i for i in result["issues"] if i["type"] in ["sql_injection", "xss", "command_injection"]]
        assert len(security_issues) == 3

    async def test_continuous_sniffing(self, sniffing_loop, test_file):
        """Test continuous sniffing."""
        # Start sniffing loop
        await sniffing_loop.start()

        # Add file to continuous sniffing
        await sniffing_loop.add_file(str(test_file))

        # Wait for processing
        await asyncio.sleep(2)

        # Check results cache
        assert str(test_file) in sniffing_loop.results_cache
        result = sniffing_loop.results_cache[str(test_file)]["result"]
        assert result["status"] == "success"
        assert len(result["issues"]) > 0

    async def test_domain_specific_sniffing(self, mcp_server, test_file):
        """Test domain-specific sniffing."""
        # Test security sniffing
        security_result = await mcp_server.run_domain_sniffing("security", [str(test_file)])
        assert security_result["status"] == "success"
        assert len(security_result["issues"]) > 0

        # Test documentation sniffing
        doc_result = await mcp_server.run_domain_sniffing("documentation", [str(test_file)])
        assert doc_result["status"] == "success"
        assert any(i["type"] == "missing_sections" for i in doc_result["issues"])

    async def test_report_generation(self, mcp_server, test_file):
        """Test report generation."""
        # Run sniffing
        await mcp_server.run_file_sniffing(str(test_file), ["security", "documentation"])

        # Check report files
        report_dir = Path(TEST_CONFIG["mcp"]["report_path"])
        assert report_dir.exists()

        # Check security report
        security_reports = list(report_dir.glob("security/*.json"))
        assert len(security_reports) > 0

        # Check documentation report
        doc_reports = list(report_dir.glob("documentation/*.json"))
        assert len(doc_reports) > 0

    async def test_issue_fixing(self, mcp_server, test_file):
        """Test automated issue fixing."""
        # Run initial sniffing
        result = await mcp_server.run_file_sniffing(str(test_file), ["security"])
        assert len(result["issues"]) > 0

        # Fix issues
        fix_result = await mcp_server.fix_issues(result["issues"])
        assert fix_result["status"] == "success"

        # Verify fixes
        verify_result = await mcp_server.run_file_sniffing(str(test_file), ["security"])
        assert len(verify_result["issues"]) < len(result["issues"])

    async def test_compliance_validation(self, mcp_server, test_file):
        """Test compliance validation."""
        # Run security sniffing with compliance checks
        result = await mcp_server.run_domain_sniffing("security", [str(test_file)])

        # Check compliance metrics
        assert "compliance" in result["metrics"]
        compliance_score = result["metrics"]["compliance"]["compliance_score"]
        assert isinstance(compliance_score, (int, float))

    async def test_performance_metrics(self, mcp_server, test_file):
        """Test performance metrics collection."""
        # Run sniffing with performance tracking
        result = await mcp_server.run_file_sniffing(str(test_file), ["security"])

        # Check metrics
        assert "execution_time" in result["metrics"]
        assert result["metrics"]["execution_time"] > 0

    async def test_concurrent_sniffing(self, mcp_server, tmp_path):
        """Test concurrent sniffing operations."""
        # Create multiple test files
        files = []
        for i in range(5):
            file_path = tmp_path / f"test_file_{i}.py"
            file_path.write_text("def test(): pass")
            files.append(str(file_path))

        # Run concurrent sniffing
        tasks = [
            mcp_server.run_file_sniffing(f, ["security"])
            for f in files
        ]
        results = await asyncio.gather(*tasks)

        # Verify all completed
        assert len(results) == len(files)
        assert all(r["status"] == "success" for r in results)

    async def test_error_handling(self, mcp_server):
        """Test error handling."""
        # Test with non-existent file
        result = await mcp_server.run_file_sniffing("non_existent.py", ["security"])
        assert result["status"] == "error"

        # Test with invalid domain
        result = await mcp_server.run_domain_sniffing("invalid_domain", ["test.py"])
        assert result["status"] == "error"

    async def test_result_caching(self, sniffing_loop, test_file):
        """Test result caching."""
        # Run initial sniffing
        await sniffing_loop.add_file(str(test_file))
        await asyncio.sleep(1)

        # Check cache
        assert str(test_file) in sniffing_loop.results_cache
        cached_result = sniffing_loop.results_cache[str(test_file)]
        assert "timestamp" in cached_result
        assert "result" in cached_result

    async def test_monitoring_integration(self, mcp_server, test_file):
        """Test monitoring system integration."""
        # Run sniffing
        await mcp_server.run_file_sniffing(str(test_file), ["security"])

        # Check metric files
        metrics_dir = Path(TEST_CONFIG["mcp"]["metrics_path"])
        assert metrics_dir.exists()
        assert any(metrics_dir.glob("*.json"))

        # Check alert files
        alerts_dir = Path(TEST_CONFIG["mcp"]["alerts_path"])
        assert alerts_dir.exists()

        # Check health files
        health_dir = Path(TEST_CONFIG["mcp"]["health_path"])
        assert health_dir.exists()
