import pytest
from sniffing.performance_sniffer import PerformanceSniffer
from sniffing.core.types import SnifferType, SniffingResult

class TestPerformanceSniffer:
    def test_initialization(self):
        """Test that PerformanceSniffer initializes correctly"""
        sniffer = PerformanceSniffer()
        assert sniffer is not None
        assert hasattr(sniffer, 'analyze')
        assert hasattr(sniffer, 'report')
        assert sniffer.get_sniffer_type() == SnifferType.PERFORMANCE

    def test_analyze_performance_metrics(self):
        """Test analysis of performance metrics"""
        sniffer = PerformanceSniffer()
        results = sniffer.analyze()
        assert isinstance(results, dict)
        assert 'performance_metrics' in results
        assert 'bottlenecks' in results

    def test_report_generation(self):
        """Test report generation"""
        sniffer = PerformanceSniffer()
        sniffer.analyze()
        report = sniffer.report()
        assert isinstance(report, str)
        assert len(report) > 0
        assert "Performance Analysis Report" in report

    def test_sniff_performance_issues(self):
        """Test sniffing for performance issues"""
        sniffer = PerformanceSniffer()
        result = sniffer.sniff()
        assert isinstance(result, SniffingResult)
        assert result.sniffer_type == SnifferType.PERFORMANCE
        assert hasattr(result, 'issues')
        assert hasattr(result, 'metrics')
        assert hasattr(result, 'recommendations')
