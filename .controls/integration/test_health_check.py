"""Integration tests for health check command."""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from .base import BaseIntegrationTest

class TestHealthCheck(BaseIntegrationTest):
    """Integration tests for health check command."""
    
    def test_basic_health_check(self, command):
        """Test basic health check with all services."""
        result = command.execute()
        self.verify_check_result(result)
    
    def test_specific_checks(self, command):
        """Test running specific checks."""
        # Test services check
        result = command.execute(checks=["services"])
        self.verify_check_result(result)
        assert len(result["checks"]) == 1
        assert "services" in result["checks"]
        
        # Test metrics check
        result = command.execute(checks=["metrics"])
        self.verify_check_result(result)
        assert len(result["checks"]) == 1
        assert "metrics" in result["checks"]
        
        # Test logs check
        result = command.execute(checks=["logs"])
        self.verify_check_result(result)
        assert len(result["checks"]) == 1
        assert "logs" in result["checks"]
    
    def test_health_check_with_report(self, command):
        """Test health check with detailed report."""
        result = command.execute(report=True)
        self.verify_check_result(result)
        self.verify_report(result)
    
    def test_service_interaction(self, command, registry):
        """Test health check with service interactions."""
        # Create some service activity
        api = registry.get_service("api")
        db = registry.get_service("database")
        cache = registry.get_service("cache")
        
        # API requests
        for _ in range(5):
            api.handle_request("/test")
        
        # Database operations
        for i in range(3):
            db.insert("test", {"id": i, "value": f"test_{i}"})
        
        # Cache operations
        for i in range(4):
            cache.set(f"key_{i}", f"value_{i}")
        
        # Run health check
        result = command.execute(report=True)
        self.verify_check_result(result)
        
        # Verify service metrics
        self.verify_service_check(result, "api")
        api_metrics = result["checks"]["services"]["details"]["services"]["api"]
        assert api_metrics["total_calls"] == 5
        
        self.verify_service_check(result, "database")
        db_metrics = result["checks"]["services"]["details"]["services"]["database"]
        assert db_metrics["total_calls"] == 3
        
        self.verify_service_check(result, "cache")
        cache_metrics = result["checks"]["services"]["details"]["services"]["cache"]
        assert cache_metrics["total_calls"] == 4
    
    def test_error_handling(self, command, registry):
        """Test health check error handling."""
        # Simulate service error
        api = registry.get_service("api")
        api.handle_request("/error")
        
        # Run health check
        result = command.execute()
        self.verify_check_result(result, expected_status="unhealthy")
        self.verify_service_check(result, "api", expected_status="unhealthy")
    
    def test_metrics_collection(self, command, registry):
        """Test metrics collection."""
        # Generate some metrics
        metrics = registry.get_service("metrics")
        counter = metrics.create_counter("requests", ["method"])
        counter.inc(labels={"method": "GET"})
        
        # Run health check
        result = command.execute(checks=["metrics"])
        self.verify_check_result(result)
        self.verify_metrics_check(result)
        
        # Verify metrics data
        metrics_data = result["checks"]["metrics"]["details"]
        assert "services" in metrics_data
        assert "system" in metrics_data
    
    def test_log_collection(self, command, registry):
        """Test log collection."""
        # Generate some logs
        logging = registry.get_service("logging")
        logging.log("INFO", "Test message")
        logging.log("WARNING", "Test warning")
        logging.log("ERROR", "Test error")
        
        # Run health check
        result = command.execute(checks=["logs"])
        self.verify_check_result(result)
        self.verify_logs_check(result)
        
        # Verify log data
        logs_data = result["checks"]["logs"]["details"]
        assert "handlers" in logs_data
        assert "services" in logs_data
    
    def test_stale_logs_detection(self, command, registry):
        """Test detection of stale logs."""
        # Mock stale logs
        logging = registry.get_service("logging")
        logging._records = [{
            "timestamp": (datetime.now() - timedelta(minutes=10)).isoformat(),
            "level": "INFO",
            "message": "Old message"
        }]
        
        # Run health check
        result = command.execute(checks=["logs"])
        self.verify_check_result(result, expected_status="unhealthy")
        
        # Verify stale handlers
        logs_data = result["checks"]["logs"]["details"]
        assert len(logs_data["stale_handlers"]) > 0
    
    def test_service_recovery(self, command, registry):
        """Test service recovery detection."""
        # Stop a service
        api = registry.get_service("api")
        api.stop()
        
        # Verify unhealthy state
        result = command.execute()
        self.verify_check_result(result, expected_status="unhealthy")
        self.verify_service_check(result, "api", expected_status="unhealthy")
        
        # Restart service
        api.start()
        
        # Verify recovery
        result = command.execute()
        self.verify_check_result(result)
        self.verify_service_check(result, "api")
    
    def test_concurrent_health_checks(self, command):
        """Test running concurrent health checks."""
        import threading
        
        results = []
        def run_check():
            result = command.execute()
            results.append(result)
        
        # Run multiple checks concurrently
        threads = [
            threading.Thread(target=run_check)
            for _ in range(5)
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all results
        for result in results:
            self.verify_check_result(result) 