from enum import Enum
from typing import Dict, Any, List

class SnifferType(Enum):
    """Types of sniffers available"""
    CORE = "core"
    FUNCTIONAL = "functional"
    SECURITY = "security"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"

class SniffingResult:
    """Result of a sniffing operation"""

    def __init__(self, sniffer_type: SnifferType):
        self.sniffer_type = sniffer_type
        self.issues: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}
        self.recommendations: List[str] = []

    def add_issue(self, issue: Dict[str, Any]):
        """Add an issue to the results"""
        self.issues.append(issue)

    def add_metric(self, name: str, value: Any):
        """Add a metric to the results"""
        self.metrics[name] = value

    def add_recommendation(self, recommendation: str):
        """Add a recommendation to the results"""
        self.recommendations.append(recommendation)
