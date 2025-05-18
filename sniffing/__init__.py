"""
Sniffing package for code analysis and testing
"""
from .core.base_sniffer import BaseSniffer
from .core.types import SnifferType, SniffingResult
from .continuous_improvement import ContinuousImprovement, ImprovementSession
from .git_integration import GitIntegration
from .functional_sniffer import FunctionalSniffer

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

__all__ = [
    "BaseSniffer",
    "SnifferType",
    "SniffingResult",
    "ContinuousImprovement",
    "ImprovementSession",
    "GitIntegration",
    "FunctionalSniffer"
]
