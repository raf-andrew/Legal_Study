"""Base formatter for health check output."""

from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseFormatter(ABC):
    """Base class for health check output formatters."""
    
    @abstractmethod
    def format_output(self, data: Dict[str, Any]) -> str:
        """Format health check output.
        
        Args:
            data: Health check data to format
            
        Returns:
            Formatted output string
        """
        pass
    
    @abstractmethod
    def format_error(self, error: str) -> str:
        """Format error message.
        
        Args:
            error: Error message to format
            
        Returns:
            Formatted error string
        """
        pass 