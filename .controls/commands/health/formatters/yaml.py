"""YAML formatter for health check output."""

import yaml
from typing import Any, Dict
from .base import BaseFormatter

class YAMLFormatter(BaseFormatter):
    """YAML formatter for health check output."""
    
    def format_output(self, data: Dict[str, Any]) -> str:
        """Format health check output as YAML.
        
        Args:
            data: Health check data to format
            
        Returns:
            YAML formatted string
        """
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    
    def format_error(self, error: str) -> str:
        """Format error message as YAML.
        
        Args:
            error: Error message to format
            
        Returns:
            YAML formatted error string
        """
        return yaml.dump({
            "status": "error",
            "error": error
        }, default_flow_style=False, sort_keys=False) 