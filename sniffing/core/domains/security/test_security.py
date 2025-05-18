"""
Tests for security domain components.
"""
import os
import pytest
from pathlib import Path
from typing import Any, Dict

from ....utils.config import SnifferConfig
from .sniffer import SecuritySniffer
from .analyzer import SecurityAnalyzer
from .reporter import SecurityReporter

# Test data
TEST_CONFIG = {
    "global": {
        "enabled": True,
        "parallel_jobs": 1,
        "cache_ttl": 3600,
        "workspace_path": "./test_workspace",
        "report_path": "./test_reports/security"
    },
    "vulnerability_patterns": {
        "test_pattern": {
            "name": "Test Pattern",
            "severity": "high",
            "description": "Test vulnerability pattern",
            "regex": "test_vulnerability",
            "cwe": "CWE-000",
            "cvss": 7.5,
            "references": ["https://test.com"],
            "remediation": "Fix test vulnerability"
        }
    },
    "compliance_rules": {
        "test_rule": {
            "name": "Test Rule",
            "severity": "medium",
            "description": "Test compliance rule",
            "regex": "test_compliance",
            "standard": "TEST",
            "requirement": "TEST-001",
            "references": ["https://test.com"],
            "remediation": "Fix test compliance"
        }
    },
    "attack_patterns": {
        "test_attack": {
            "name": "Test Attack",
            "severity": "high",
            "description": "Test attack pattern",
            "regex": "test_attack",
            "technique": "Test technique",
            "mitre": "T0000",
            "references": ["https://test.com"],
            "remediation": "Fix test attack"
        }
    },
    "monitoring": {
        "enabled": True,
        "collection_interval": 60,
        "metrics_path": "./test_metrics/security",
        "health_check_interval": 300
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "./test_logs/security/{name}.log"
    },
    "report_templates": {
        "html": "security.html",
        "pdf": "security.pdf",
        "csv": "security.csv"
    },
    "model": {
        "name": "microsoft/codebert-base",
        "confidence_threshold": 0.8,
        "max_sequence_length": 512,
        "batch_size": 32
    }
}

@pytest.fixture
async def config() -> SnifferConfig:
    """Create test configuration."""
    return SnifferConfig(TEST_CONFIG)

@pytest.fixture
async def test_file(tmp_path: Path) -> str:
    """Create test file with vulnerabilities."""
    content = """
    # Test file with vulnerabilities
    password = "test123"  # test_compliance
    query = f"SELECT * FROM users WHERE id = {user_id}"  # test_vulnerability
    os.system(f"rm {filename}")  # test_attack
    """
    file_path = tmp_path / "test.py"
    file_path.write_text(content)
    return str(file_path)

@pytest.fixture
async def sniffer(config: SnifferConfig) -> SecuritySniffer:
    """Create security sniffer."""
    return SecuritySniffer(config)

@pytest.fixture
async def analyzer(config: SnifferConfig) -> SecurityAnalyzer:
    """Create security analyzer."""
    return SecurityAnalyzer(config)

@pytest.fixture
async def reporter(config: SnifferConfig) -> SecurityReporter:
    """Create security reporter."""
    return SecurityReporter(config)

@pytest.mark.asyncio
async def test_sniffer_initialization(sniffer: SecuritySniffer):
    """Test sniffer initialization."""
    assert sniffer.domain == "security"
    assert sniffer.vulnerability_patterns
    assert sniffer.compliance_rules
    assert sniffer.attack_simulations

@pytest.mark.asyncio
async def test_analyzer_initialization(analyzer: SecurityAnalyzer):
    """Test analyzer initialization."""
    assert analyzer.domain == "security"
    assert analyzer.vulnerability_patterns
    assert analyzer.compliance_rules
    assert analyzer.attack_patterns

@pytest.mark.asyncio
async def test_reporter_initialization(reporter: SecurityReporter):
    """Test reporter initialization."""
    assert reporter.domain == "security"
    assert reporter.report_templates

@pytest.mark.asyncio
async def test_sniffing_workflow(
    sniffer: SecuritySniffer,
    analyzer: SecurityAnalyzer,
    reporter: SecurityReporter,
    test_file: str
):
    """Test complete sniffing workflow."""
    # Run sniffing
    results = await sniffer._sniff_files([test_file])
    assert results["status"] == "completed"
    assert len(results["issues"]) > 0

    # Run analysis
    analysis = await analyzer._analyze_results(results)
    assert analysis["status"] == "completed"
    assert len(analysis["findings"]) > 0

    # Generate report
    report = await reporter._generate_report(results, analysis)
    assert report["status"] == "completed"
    assert len(report["sections"]) > 0

@pytest.mark.asyncio
async def test_vulnerability_detection(
    sniffer: SecuritySniffer,
    test_file: str
):
    """Test vulnerability detection."""
    results = await sniffer._scan_vulnerabilities([test_file])
    assert results["status"] == "completed"
    assert any(
        "test_vulnerability" in issue.get("code", "")
        for issue in results["issues"]
    )

@pytest.mark.asyncio
async def test_compliance_checking(
    sniffer: SecuritySniffer,
    test_file: str
):
    """Test compliance checking."""
    results = await sniffer._check_compliance([test_file])
    assert results["status"] == "completed"
    assert any(
        "test_compliance" in issue.get("code", "")
        for issue in results["issues"]
    )

@pytest.mark.asyncio
async def test_attack_simulation(
    sniffer: SecuritySniffer,
    test_file: str
):
    """Test attack simulation."""
    results = await sniffer._simulate_attacks([test_file])
    assert results["status"] == "completed"
    assert any(
        "test_attack" in issue.get("code", "")
        for issue in results["issues"]
    )

@pytest.mark.asyncio
async def test_risk_score_calculation(
    analyzer: SecurityAnalyzer
):
    """Test risk score calculation."""
    findings = [
        {
            "severity": "critical",
            "confidence": 0.9
        },
        {
            "severity": "high",
            "confidence": 0.8
        },
        {
            "severity": "medium",
            "confidence": 0.7
        }
    ]
    risk_score = await analyzer._calculate_risk_score(findings)
    assert risk_score["risk_score"] > 0
    assert risk_score["confidence_avg"] > 0

@pytest.mark.asyncio
async def test_report_generation(
    reporter: SecurityReporter
):
    """Test report generation."""
    results = {
        "status": "completed",
        "issues": [
            {
                "id": "TEST-001",
                "type": "vulnerability",
                "severity": "high",
                "description": "Test issue",
                "code": "test code",
                "line": 1
            }
        ]
    }
    analysis = {
        "status": "completed",
        "findings": [
            {
                "id": "TEST-001",
                "type": "vulnerability",
                "severity": "high",
                "confidence": 0.9,
                "description": "Test finding",
                "code": "test code",
                "line": 1
            }
        ],
        "risk_score": {
            "risk_score": 7.5,
            "confidence_avg": 0.9,
            "severity_counts": {
                "critical": 0,
                "high": 1,
                "medium": 0,
                "low": 0
            }
        }
    }
    report = await reporter._generate_report(results, analysis)
    assert report["status"] == "completed"
    assert len(report["sections"]) > 0

@pytest.mark.asyncio
async def test_error_handling(
    sniffer: SecuritySniffer,
    analyzer: SecurityAnalyzer,
    reporter: SecurityReporter
):
    """Test error handling."""
    # Test sniffer error handling
    results = await sniffer._sniff_files(["nonexistent.py"])
    assert results["status"] == "failed"
    assert "error" in results

    # Test analyzer error handling
    analysis = await analyzer._analyze_results({})
    assert analysis["status"] == "failed"
    assert "error" in analysis

    # Test reporter error handling
    report = await reporter._generate_report({}, {})
    assert report["status"] == "failed"
    assert "error" in report
