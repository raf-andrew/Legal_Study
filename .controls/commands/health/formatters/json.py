"""JSON formatter for health check output."""

import json
from typing import Any, Dict
from .base import BaseFormatter

class JSONFormatter(BaseFormatter):
    """JSON formatter for health check output."""
    
    def format_output(self, data: Dict[str, Any]) -> str:
        """Format health check output as JSON.
        
        Args:
            data: Health check data to format
            
        Returns:
            JSON formatted string
        """
        return json.dumps(data, indent=2)
    
    def format_error(self, error: str) -> str:
        """Format error message as JSON.
        
        Args:
            error: Error message to format
            
        Returns:
            JSON formatted error string
        """
        return json.dumps({
            "status": "error",
            "error": error
        }, indent=2) 