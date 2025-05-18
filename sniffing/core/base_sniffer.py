"""
Base sniffer implementation.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from .types import SnifferType, SniffingResult

class SnifferType(Enum):
    """Types of sniffers available."""
    SECURITY = "security"
    BROWSER = "browser"
    FUNCTIONAL = "functional"
    UNIT = "unit"
    DOCUMENTATION = "documentation"

class SniffingResult:
    """Result of a sniffing operation."""

    def __init__(
        self,
        file: str,
        sniffer_type: SnifferType,
        status: str = "pending",
        issues: Optional[List[Dict]] = None,
        metrics: Optional[Dict] = None
    ):
        """Initialize sniffing result.

        Args:
            file: File that was sniffed
            sniffer_type: Type of sniffer used
            status: Status of sniffing operation
            issues: List of issues found
            metrics: Metrics collected
        """
        self.file = file
        self.sniffer_type = sniffer_type
        self.status = status
        self.issues = issues or []
        self.metrics = metrics or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        """Convert result to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "file": self.file,
            "sniffer_type": self.sniffer_type.value,
            "status": self.status,
            "issues": self.issues,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat()
        }

class BaseSniffer(ABC):
    """Base class for all code sniffers"""

    def __init__(self):
        """Initialize the base sniffer"""
        self.results = {}

    @abstractmethod
    def analyze(self):
        """Analyze the code and collect results

        This method should be implemented by all subclasses
        """
        raise NotImplementedError("Subclasses must implement analyze()")

    @abstractmethod
    def report(self):
        """Generate a report from the analysis results

        This method should be implemented by all subclasses
        """
        raise NotImplementedError("Subclasses must implement report()")

    @abstractmethod
    def get_sniffer_type(self) -> SnifferType:
        """Get the type of this sniffer

        Returns:
            SnifferType: The type of this sniffer
        """
        raise NotImplementedError("Subclasses must implement get_sniffer_type()")

    @abstractmethod
    def fix_issues(self, issues: List[Dict[str, Any]]) -> bool:
        """Fix detected issues

        Args:
            issues: List of issues to fix

        Returns:
            bool: True if any issues were fixed, False otherwise
        """
        raise NotImplementedError("Subclasses must implement fix_issues()")

    @abstractmethod
    def sniff(self) -> SniffingResult:
        """Execute the sniffing operation

        Returns:
            SniffingResult: Results of the sniffing operation
        """
        raise NotImplementedError("Subclasses must implement sniff()")

    def _setup_directories(self) -> None:
        """Set up necessary directories for the sniffer."""
        self.report_path.mkdir(parents=True, exist_ok=True)
        (self.report_path / self.get_sniffer_type().value).mkdir(parents=True, exist_ok=True)

    async def sniff(self, file: str) -> SniffingResult:
        """Sniff a file.

        Args:
            file: File to sniff

        Returns:
            Sniffing result
        """
        pass

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report of sniffing results."""
        return {
            "sniffer_type": self.get_sniffer_type().value,
            "execution_time": datetime.now().isoformat(),
            "results": [vars(result) for result in self.results],
            "summary": self._generate_summary()
        }

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of all sniffing results."""
        return {
            "total_runs": len(self.results),
            "success_rate": sum(1 for r in self.results if r.status == "completed") / len(self.results) if self.results else 0,
            "total_issues": sum(len(r.issues) for r in self.results),
            "total_recommendations": sum(len(r.recommendations) for r in self.results),
            "average_coverage": sum(r.coverage or 0 for r in self.results) / len(self.results) if self.results else 0
        }

    def save_report(self, report: Dict[str, Any]) -> Path:
        """Save the report to a file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.report_path / self.get_sniffer_type().value / f"report_{timestamp}.json"

        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report_file

    def get_affected_files(self) -> Set[Path]:
        """Get the set of files affected by this sniffer."""
        return set()

    def validate_config(self) -> bool:
        """Validate the sniffer's configuration."""
        return True

    def cleanup(self) -> None:
        """Clean up any resources used by the sniffer."""
        pass
