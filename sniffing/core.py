"""
Core sniffing functionality and base classes for the testing infrastructure.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

class SnifferType(Enum):
    """Types of sniffers available in the system."""
    FUNCTIONAL = "functional"
    UNIT = "unit"
    API = "api"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"
    CODE_QUALITY = "code_quality"

@dataclass
class SniffingResult:
    """Represents the result of a sniffing operation."""
    sniffer_type: SnifferType
    timestamp: datetime
    status: bool
    metrics: Dict[str, Any]
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    audit_trail: Dict[str, Any]

class BaseSniffer(ABC):
    """Base class for all sniffers in the system."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results: List[SniffingResult] = []
        self.workspace_path = Path(config.get("workspace_path", "."))

    @abstractmethod
    def sniff(self) -> SniffingResult:
        """Execute the sniffing operation."""
        pass

    @abstractmethod
    def fix_issues(self, issues: List[Dict[str, Any]]) -> bool:
        """Attempt to automatically fix detected issues."""
        pass

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report of sniffing results."""
        return {
            "sniffer_type": self.get_sniffer_type().value,
            "execution_time": datetime.now().isoformat(),
            "results": [vars(result) for result in self.results],
            "summary": self._generate_summary()
        }

    @abstractmethod
    def get_sniffer_type(self) -> SnifferType:
        """Return the type of this sniffer."""
        pass

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of all sniffing results."""
        return {
            "total_runs": len(self.results),
            "success_rate": sum(1 for r in self.results if r.status) / len(self.results) if self.results else 0,
            "total_issues": sum(len(r.issues) for r in self.results),
            "total_recommendations": sum(len(r.recommendations) for r in self.results)
        }

class SniffingManager:
    """Manages and coordinates all sniffing operations."""

    def __init__(self, config_path: Optional[Path] = None):
        self.sniffers: Dict[SnifferType, BaseSniffer] = {}
        self.config = self._load_config(config_path) if config_path else {}

    def register_sniffer(self, sniffer: BaseSniffer) -> None:
        """Register a new sniffer with the manager."""
        self.sniffers[sniffer.get_sniffer_type()] = sniffer

    def run_all_sniffers(self) -> Dict[SnifferType, SniffingResult]:
        """Execute all registered sniffers and return their results."""
        results = {}
        for sniffer_type, sniffer in self.sniffers.items():
            results[sniffer_type] = sniffer.sniff()
        return results

    def run_sniffer(self, sniffer_type: SnifferType) -> SniffingResult:
        """Execute a specific sniffer and return its results."""
        if sniffer_type not in self.sniffers:
            raise ValueError(f"No sniffer registered for type {sniffer_type}")
        return self.sniffers[sniffer_type].sniff()

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report from all sniffers."""
        return {
            "timestamp": datetime.now().isoformat(),
            "sniffer_reports": {
                sniffer_type.value: sniffer.generate_report()
                for sniffer_type, sniffer in self.sniffers.items()
            }
        }

    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from the specified path."""
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
