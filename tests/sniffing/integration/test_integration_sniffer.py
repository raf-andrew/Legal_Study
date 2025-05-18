import pytest
from sniffing.integration_sniffer import IntegrationSniffer
from sniffing.core.types import SnifferType, SniffingResult

class TestIntegrationSniffer:
    def test_initialization(self):
        """Test that IntegrationSniffer initializes correctly"""
        sniffer = IntegrationSniffer()
        assert sniffer is not None
        assert hasattr(sniffer, 'analyze')
        assert hasattr(sniffer, 'report')
        assert sniffer.get_sniffer_type() == SnifferType.INTEGRATION

    def test_analyze_integration_points(self):
        """Test analysis of integration points"""
        sniffer = IntegrationSniffer()
        results = sniffer.analyze()
        assert isinstance(results, dict)
        assert 'integration_points' in results
        assert 'dependencies' in results

    def test_report_generation(self):
        """Test report generation"""
        sniffer = IntegrationSniffer()
        sniffer.analyze()
        report = sniffer.report()
        assert isinstance(report, str)
        assert len(report) > 0
        assert "Integration Analysis Report" in report

    def test_sniff_integration_issues(self):
        """Test sniffing for integration issues"""
        sniffer = IntegrationSniffer()
        result = sniffer.sniff()
        assert isinstance(result, SniffingResult)
        assert result.sniffer_type == SnifferType.INTEGRATION
        assert hasattr(result, 'issues')
        assert hasattr(result, 'metrics')
        assert hasattr(result, 'recommendations')
