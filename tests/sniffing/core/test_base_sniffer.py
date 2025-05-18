import pytest
from sniffing.core.base_sniffer import BaseSniffer
from sniffing.core.types import SnifferType, SniffingResult
from typing import Dict, Any, List

class TestSniffer(BaseSniffer):
    """Concrete implementation of BaseSniffer for testing"""

    def analyze(self):
        return {'test': 'result'}

    def report(self):
        return "Test Report"

    def get_sniffer_type(self) -> SnifferType:
        return SnifferType.CORE

    def fix_issues(self, issues: List[Dict[str, Any]]) -> bool:
        return True

    def sniff(self) -> SniffingResult:
        result = SniffingResult(self.get_sniffer_type())
        result.add_issue({'test': 'issue'})
        return result

class TestBaseSniffer:
    def test_initialization(self):
        """Test that BaseSniffer initializes correctly"""
        sniffer = TestSniffer()
        assert sniffer is not None
        assert hasattr(sniffer, 'analyze')
        assert hasattr(sniffer, 'report')

    def test_analyze_method(self):
        """Test analyze method implementation"""
        sniffer = TestSniffer()
        result = sniffer.analyze()
        assert result == {'test': 'result'}

    def test_report_method(self):
        """Test report method implementation"""
        sniffer = TestSniffer()
        result = sniffer.report()
        assert result == "Test Report"

    def test_get_sniffer_type(self):
        """Test get_sniffer_type method"""
        sniffer = TestSniffer()
        result = sniffer.get_sniffer_type()
        assert result == SnifferType.CORE

    def test_fix_issues(self):
        """Test fix_issues method"""
        sniffer = TestSniffer()
        result = sniffer.fix_issues([{'test': 'issue'}])
        assert result is True

    def test_sniff(self):
        """Test sniff method"""
        sniffer = TestSniffer()
        result = sniffer.sniff()
        assert isinstance(result, SniffingResult)
        assert result.sniffer_type == SnifferType.CORE
        assert len(result.issues) == 1
