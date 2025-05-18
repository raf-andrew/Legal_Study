import pytest
from sniffing.security_sniffer import SecuritySniffer
from sniffing.core.types import SnifferType, SniffingResult

class TestSecuritySniffer:
    def test_initialization(self):
        """Test that SecuritySniffer initializes correctly"""
        sniffer = SecuritySniffer()
        assert sniffer is not None
        assert hasattr(sniffer, 'analyze')
        assert hasattr(sniffer, 'report')
        assert sniffer.get_sniffer_type() == SnifferType.SECURITY

    def test_analyze_security_requirements(self):
        """Test analysis of security requirements"""
        sniffer = SecuritySniffer()
        results = sniffer.analyze()
        assert isinstance(results, dict)
        assert 'security_requirements' in results
        assert 'vulnerabilities' in results

    def test_report_generation(self):
        """Test report generation"""
        sniffer = SecuritySniffer()
        sniffer.analyze()
        report = sniffer.report()
        assert isinstance(report, str)
        assert len(report) > 0
        assert "Security Analysis Report" in report

    def test_sniff_security_issues(self):
        """Test sniffing for security issues"""
        sniffer = SecuritySniffer()
        result = sniffer.sniff()
        assert isinstance(result, SniffingResult)
        assert result.sniffer_type == SnifferType.SECURITY
        assert hasattr(result, 'issues')
        assert hasattr(result, 'metrics')
        assert hasattr(result, 'recommendations')
