"""Base class for integration tests."""

import pytest
from typing import Any, Dict, Optional
from datetime import datetime
from ..commands.health.command import HealthCheckCommand
from ...mocks.registry import MockServiceRegistry

class BaseIntegrationTest:
    """Base class for integration tests."""
    
    @pytest.fixture
    def registry(self) -> MockServiceRegistry:
        """Create and configure service registry.
        
        Returns:
            Configured service registry
        """
        registry = MockServiceRegistry()
        registry.create_all_services()
        registry.start_all()
        return registry
    
    @pytest.fixture
    def command(self, registry) -> HealthCheckCommand:
        """Create health check command.
        
        Args:
            registry: Service registry instance
            
        Returns:
            Health check command instance
        """
        command = HealthCheckCommand()
        command.registry = registry
        return command
    
    def verify_check_result(self, result: Dict[str, Any],
                           expected_status: str = "healthy",
                           expected_checks: Optional[Dict[str, str]] = None) -> None:
        """Verify health check result.
        
        Args:
            result: Health check result
            expected_status: Expected overall status
            expected_checks: Expected check statuses
        """
        # Verify basic structure
        assert "status" in result
        assert "timestamp" in result
        assert "checks" in result
        
        # Verify timestamp
        timestamp = datetime.fromisoformat(result["timestamp"])
        assert (datetime.now() - timestamp).total_seconds() < 60
        
        # Verify status
        assert result["status"] == expected_status
        
        # Verify checks
        if expected_checks:
            for check_name, expected_status in expected_checks.items():
                assert check_name in result["checks"]
                assert result["checks"][check_name]["status"] == expected_status
    
    def verify_report(self, result: Dict[str, Any]) -> None:
        """Verify health check report.
        
        Args:
            result: Health check result with report
        """
        assert "report" in result
        report = result["report"]
        
        # Verify summary
        assert "summary" in report
        summary = report["summary"]
        assert "total_checks" in summary
        assert "healthy_checks" in summary
        assert "unhealthy_checks" in summary
        assert "error_checks" in summary
        assert "health_percentage" in summary
        
        # Verify recommendations
        assert "recommendations" in report
        assert isinstance(report["recommendations"], list)
    
    def verify_service_check(self, result: Dict[str, Any],
                           service_name: str,
                           expected_status: str = "healthy") -> None:
        """Verify service check result.
        
        Args:
            result: Health check result
            service_name: Name of service to verify
            expected_status: Expected service status
        """
        assert "checks" in result
        assert "services" in result["checks"]
        service_check = result["checks"]["services"]
        
        assert "details" in service_check
        assert "services" in service_check["details"]
        assert service_name in service_check["details"]["services"]
        
        service = service_check["details"]["services"][service_name]
        assert service["status"] == expected_status
    
    def verify_metrics_check(self, result: Dict[str, Any]) -> None:
        """Verify metrics check result.
        
        Args:
            result: Health check result
        """
        assert "checks" in result
        assert "metrics" in result["checks"]
        metrics_check = result["checks"]["metrics"]
        
        assert "details" in metrics_check
        assert "services" in metrics_check["details"]
        assert "system" in metrics_check["details"]
    
    def verify_logs_check(self, result: Dict[str, Any]) -> None:
        """Verify logs check result.
        
        Args:
            result: Health check result
        """
        assert "checks" in result
        assert "logs" in result["checks"]
        logs_check = result["checks"]["logs"]
        
        assert "details" in logs_check
        assert "handlers" in logs_check["details"]
        assert "services" in logs_check["details"] 