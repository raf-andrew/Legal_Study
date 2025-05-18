import pytest
from sniffing.functional_sniffer import FunctionalSniffer

class TestFunctionalSniffer:
    def test_initialization(self):
        """Test that FunctionalSniffer initializes correctly"""
        sniffer = FunctionalSniffer()
        assert sniffer is not None
        assert hasattr(sniffer, 'analyze')
        assert hasattr(sniffer, 'report')

    def test_analyze_functional_requirements(self):
        """Test analysis of functional requirements"""
        sniffer = FunctionalSniffer()
        results = sniffer.analyze()
        assert isinstance(results, dict)
        assert 'functional_requirements' in results

    def test_report_generation(self):
        """Test report generation"""
        sniffer = FunctionalSniffer()
        sniffer.analyze()
        report = sniffer.report()
        assert isinstance(report, str)
        assert len(report) > 0
