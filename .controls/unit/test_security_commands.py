"""Unit tests for security commands."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from ..commands.security import (
    SecurityScanCommand,
    SecurityAuditCommand,
    SecurityFixCommand,
    SecurityReportCommand
)
from ..commands.registry import CommandRegistry
from ..commands.executor import CommandExecutor

@pytest.fixture
def scan_command() -> SecurityScanCommand:
    """Create a security scan command instance."""
    return SecurityScanCommand()

@pytest.fixture
def audit_command() -> SecurityAuditCommand:
    """Create a security audit command instance."""
    return SecurityAuditCommand()

@pytest.fixture
def fix_command() -> SecurityFixCommand:
    """Create a security fix command instance."""
    return SecurityFixCommand()

@pytest.fixture
def report_command() -> SecurityReportCommand:
    """Create a security report command instance."""
    return SecurityReportCommand()

@pytest.fixture
def registry() -> CommandRegistry:
    """Create a command registry instance."""
    return CommandRegistry()

@pytest.fixture
def executor(registry: CommandRegistry) -> CommandExecutor:
    """Create a command executor instance."""
    return CommandExecutor(registry)

def test_scan_command_initialization(scan_command: SecurityScanCommand):
    """Test security scan command initialization."""
    assert scan_command.name == "security:scan"
    assert scan_command.description == "Scan system security"
    assert scan_command.logger.name == "command.security:scan"

def test_audit_command_initialization(audit_command: SecurityAuditCommand):
    """Test security audit command initialization."""
    assert audit_command.name == "security:audit"
    assert audit_command.description == "Audit system security"
    assert audit_command.logger.name == "command.security:audit"

def test_fix_command_initialization(fix_command: SecurityFixCommand):
    """Test security fix command initialization."""
    assert fix_command.name == "security:fix"
    assert fix_command.description == "Fix security issues"
    assert fix_command.logger.name == "command.security:fix"

def test_report_command_initialization(report_command: SecurityReportCommand):
    """Test security report command initialization."""
    assert report_command.name == "security:report"
    assert report_command.description == "Generate security report"
    assert report_command.logger.name == "command.security:report"

def test_scan_command_execute(scan_command: SecurityScanCommand):
    """Test security scan command execution."""
    with patch.object(scan_command.logger, "info") as mock_info:
        result = scan_command.execute({})
        assert result == 0
        assert mock_info.call_count == 2
        mock_info.assert_any_call("Running security scan...")
        mock_info.assert_any_call("Security scan completed successfully")

def test_audit_command_execute(audit_command: SecurityAuditCommand):
    """Test security audit command execution."""
    with patch.object(audit_command.logger, "info") as mock_info:
        result = audit_command.execute({})
        assert result == 0
        assert mock_info.call_count == 2
        mock_info.assert_any_call("Running security audit...")
        mock_info.assert_any_call("Security audit completed successfully")

def test_fix_command_execute(fix_command: SecurityFixCommand):
    """Test security fix command execution."""
    with patch.object(fix_command.logger, "info") as mock_info:
        result = fix_command.execute({})
        assert result == 0
        assert mock_info.call_count == 2
        mock_info.assert_any_call("Running security fixes...")
        mock_info.assert_any_call("Security fixes completed successfully")

def test_report_command_execute(report_command: SecurityReportCommand):
    """Test security report command execution."""
    with patch.object(report_command.logger, "info") as mock_info:
        result = report_command.execute({})
        assert result == 0
        assert mock_info.call_count == 2
        mock_info.assert_any_call("Generating security report...")
        mock_info.assert_any_call("Security report generated successfully")

def test_scan_command_help(scan_command: SecurityScanCommand):
    """Test security scan command help text."""
    help_text = scan_command.get_help()
    assert help_text == "Scan system security and report any issues"

def test_audit_command_help(audit_command: SecurityAuditCommand):
    """Test security audit command help text."""
    help_text = audit_command.get_help()
    assert help_text == "Audit system security and report any issues"

def test_fix_command_help(fix_command: SecurityFixCommand):
    """Test security fix command help text."""
    help_text = fix_command.get_help()
    assert help_text == "Fix security issues and report any problems"

def test_report_command_help(report_command: SecurityReportCommand):
    """Test security report command help text."""
    help_text = report_command.get_help()
    assert help_text == "Generate security report and save to file"

def test_scan_command_usage(scan_command: SecurityScanCommand):
    """Test security scan command usage text."""
    usage = scan_command.get_usage()
    assert usage == "security:scan [options]"

def test_audit_command_usage(audit_command: SecurityAuditCommand):
    """Test security audit command usage text."""
    usage = audit_command.get_usage()
    assert usage == "security:audit [options]"

def test_fix_command_usage(fix_command: SecurityFixCommand):
    """Test security fix command usage text."""
    usage = fix_command.get_usage()
    assert usage == "security:fix [options]"

def test_report_command_usage(report_command: SecurityReportCommand):
    """Test security report command usage text."""
    usage = report_command.get_usage()
    assert usage == "security:report [options]"

def test_scan_command_examples(scan_command: SecurityScanCommand):
    """Test security scan command examples."""
    examples = scan_command.get_examples()
    assert len(examples) == 3
    assert "security:scan" in examples
    assert "security:scan --verbose" in examples
    assert "security:scan --service api" in examples

def test_audit_command_examples(audit_command: SecurityAuditCommand):
    """Test security audit command examples."""
    examples = audit_command.get_examples()
    assert len(examples) == 3
    assert "security:audit" in examples
    assert "security:audit --verbose" in examples
    assert "security:audit --service api" in examples

def test_fix_command_examples(fix_command: SecurityFixCommand):
    """Test security fix command examples."""
    examples = fix_command.get_examples()
    assert len(examples) == 3
    assert "security:fix" in examples
    assert "security:fix --verbose" in examples
    assert "security:fix --service api" in examples

def test_report_command_examples(report_command: SecurityReportCommand):
    """Test security report command examples."""
    examples = report_command.get_examples()
    assert len(examples) == 3
    assert "security:report" in examples
    assert "security:report --verbose" in examples
    assert "security:report --service api" in examples

def test_scan_command_registration(registry: CommandRegistry):
    """Test security scan command registration."""
    registry.register(SecurityScanCommand)
    command = registry.get_command("security:scan")
    assert command is not None
    assert command.__name__ == "SecurityScanCommand"

def test_audit_command_registration(registry: CommandRegistry):
    """Test security audit command registration."""
    registry.register(SecurityAuditCommand)
    command = registry.get_command("security:audit")
    assert command is not None
    assert command.__name__ == "SecurityAuditCommand"

def test_fix_command_registration(registry: CommandRegistry):
    """Test security fix command registration."""
    registry.register(SecurityFixCommand)
    command = registry.get_command("security:fix")
    assert command is not None
    assert command.__name__ == "SecurityFixCommand"

def test_report_command_registration(registry: CommandRegistry):
    """Test security report command registration."""
    registry.register(SecurityReportCommand)
    command = registry.get_command("security:report")
    assert command is not None
    assert command.__name__ == "SecurityReportCommand"

def test_scan_command_execution(executor: CommandExecutor):
    """Test security scan command execution through executor."""
    executor.registry.register(SecurityScanCommand)
    with patch("logging.Logger.info") as mock_info:
        result = executor.execute("security:scan", {})
        assert result == 0
        assert mock_info.call_count >= 2
        mock_info.assert_any_call("Running security scan...")
        mock_info.assert_any_call("Security scan completed successfully")

def test_audit_command_execution(executor: CommandExecutor):
    """Test security audit command execution through executor."""
    executor.registry.register(SecurityAuditCommand)
    with patch("logging.Logger.info") as mock_info:
        result = executor.execute("security:audit", {})
        assert result == 0
        assert mock_info.call_count >= 2
        mock_info.assert_any_call("Running security audit...")
        mock_info.assert_any_call("Security audit completed successfully")

def test_fix_command_execution(executor: CommandExecutor):
    """Test security fix command execution through executor."""
    executor.registry.register(SecurityFixCommand)
    with patch("logging.Logger.info") as mock_info:
        result = executor.execute("security:fix", {})
        assert result == 0
        assert mock_info.call_count >= 2
        mock_info.assert_any_call("Running security fixes...")
        mock_info.assert_any_call("Security fixes completed successfully")

def test_report_command_execution(executor: CommandExecutor):
    """Test security report command execution through executor."""
    executor.registry.register(SecurityReportCommand)
    with patch("logging.Logger.info") as mock_info:
        result = executor.execute("security:report", {})
        assert result == 0
        assert mock_info.call_count >= 2
        mock_info.assert_any_call("Generating security report...")
        mock_info.assert_any_call("Security report generated successfully")

def test_scan_command_validation(scan_command: SecurityScanCommand):
    """Test security scan command argument validation."""
    assert scan_command.validate({}) is True
    assert scan_command.validate({"verbose": True}) is True
    assert scan_command.validate({"service": "api"}) is True

def test_audit_command_validation(audit_command: SecurityAuditCommand):
    """Test security audit command argument validation."""
    assert audit_command.validate({}) is True
    assert audit_command.validate({"verbose": True}) is True
    assert audit_command.validate({"service": "api"}) is True

def test_fix_command_validation(fix_command: SecurityFixCommand):
    """Test security fix command argument validation."""
    assert fix_command.validate({}) is True
    assert fix_command.validate({"verbose": True}) is True
    assert fix_command.validate({"service": "api"}) is True

def test_report_command_validation(report_command: SecurityReportCommand):
    """Test security report command argument validation."""
    assert report_command.validate({}) is True
    assert report_command.validate({"verbose": True}) is True
    assert report_command.validate({"service": "api"}) is True 