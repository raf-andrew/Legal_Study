"""Text formatter for health check output."""

from typing import Any, Dict
from .base import BaseFormatter

class TextFormatter(BaseFormatter):
    """Text formatter for health check output."""
    
    def format_output(self, data: Dict[str, Any]) -> str:
        """Format health check output as text.
        
        Args:
            data: Health check data to format
            
        Returns:
            Text formatted string
        """
        lines = [
            "Health Check Report",
            "==================",
            f"Status: {data['status']}",
            f"Timestamp: {data['timestamp']}",
            "",
            "Checks:",
        ]
        
        for check_name, check_data in data.get("checks", {}).items():
            lines.append(f"\n{check_name.title()}:")
            lines.append("-" * (len(check_name) + 1))
            lines.append(f"Status: {check_data['status']}")
            
            if "details" in check_data:
                details = check_data["details"]
                if isinstance(details, dict):
                    for key, value in details.items():
                        if isinstance(value, dict):
                            lines.append(f"\n{key.title()}:")
                            for k, v in value.items():
                                lines.append(f"  {k}: {v}")
                        else:
                            lines.append(f"{key}: {value}")
            
            if "error" in check_data:
                lines.append(f"Error: {check_data['error']}")
        
        if "report" in data:
            report = data["report"]
            lines.extend([
                "\nReport Summary:",
                "---------------",
                f"Total Checks: {report['summary']['total_checks']}",
                f"Healthy Checks: {report['summary']['healthy_checks']}",
                f"Unhealthy Checks: {report['summary']['unhealthy_checks']}",
                f"Error Checks: {report['summary']['error_checks']}",
                f"Health Percentage: {report['summary']['health_percentage']}%",
                
                "\nRecommendations:",
                "----------------"
            ])
            
            for recommendation in report.get("recommendations", []):
                lines.append(f"- {recommendation}")
        
        return "\n".join(lines)
    
    def format_error(self, error: str) -> str:
        """Format error message as text.
        
        Args:
            error: Error message to format
            
        Returns:
            Text formatted error string
        """
        return "\n".join([
            "Health Check Error",
            "=================",
            f"Status: error",
            f"Error: {error}"
        ]) 