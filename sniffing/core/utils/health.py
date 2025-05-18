"""
Enhanced health checker for monitoring sniffer health status.
"""
import logging
import psutil
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("health")

class HealthChecker:
    """Class for monitoring and managing sniffer health."""

    def __init__(self, sniffer_type: str):
        """Initialize health checker.

        Args:
            sniffer_type: Type of sniffer this checker is for
        """
        self.sniffer_type = sniffer_type
        self.last_update = None
        self.status = "healthy"
        self.checks = {
            "memory": self._check_memory,
            "cpu": self._check_cpu,
            "disk": self._check_disk,
            "errors": self._check_errors
        }
        self.thresholds = {
            "memory": 90.0,  # Percentage
            "cpu": 80.0,     # Percentage
            "disk": 90.0,    # Percentage
            "errors": 5      # Count
        }
        self.check_history = []
        self.error_count = 0
        self.last_error = None

    def is_healthy(self) -> bool:
        """Check if sniffer is healthy.

        Returns:
            True if healthy, False otherwise
        """
        return self.status == "healthy"

    async def run_health_check(self) -> Dict[str, Any]:
        """Run all health checks.

        Returns:
            Dictionary containing health check results
        """
        try:
            results = {}
            all_healthy = True

            # Run each check
            for check_name, check_func in self.checks.items():
                check_result = await check_func()
                results[check_name] = check_result
                if not check_result["healthy"]:
                    all_healthy = False

            # Update status
            self.status = "healthy" if all_healthy else "unhealthy"
            self.last_update = datetime.now()

            # Add to history
            self.check_history.append({
                "timestamp": self.last_update.isoformat(),
                "status": self.status,
                "results": results
            })

            # Trim history (keep last 100 checks)
            if len(self.check_history) > 100:
                self.check_history = self.check_history[-100:]

            return {
                "status": self.status,
                "timestamp": self.last_update.isoformat(),
                "checks": results
            }

        except Exception as e:
            logger.error(f"Error running health check: {e}")
            self.record_error("health_check", str(e))
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    async def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage.

        Returns:
            Dictionary containing memory check results
        """
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            healthy = usage_percent < self.thresholds["memory"]

            return {
                "healthy": healthy,
                "usage_percent": usage_percent,
                "threshold": self.thresholds["memory"],
                "available": memory.available,
                "total": memory.total
            }

        except Exception as e:
            logger.error(f"Error checking memory: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage.

        Returns:
            Dictionary containing CPU check results
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            healthy = cpu_percent < self.thresholds["cpu"]

            return {
                "healthy": healthy,
                "usage_percent": cpu_percent,
                "threshold": self.thresholds["cpu"],
                "cores": psutil.cpu_count()
            }

        except Exception as e:
            logger.error(f"Error checking CPU: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_disk(self) -> Dict[str, Any]:
        """Check disk usage.

        Returns:
            Dictionary containing disk check results
        """
        try:
            disk = psutil.disk_usage("/")
            usage_percent = disk.percent
            healthy = usage_percent < self.thresholds["disk"]

            return {
                "healthy": healthy,
                "usage_percent": usage_percent,
                "threshold": self.thresholds["disk"],
                "free": disk.free,
                "total": disk.total
            }

        except Exception as e:
            logger.error(f"Error checking disk: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }

    async def _check_errors(self) -> Dict[str, Any]:
        """Check error status.

        Returns:
            Dictionary containing error check results
        """
        try:
            healthy = self.error_count < self.thresholds["errors"]

            return {
                "healthy": healthy,
                "error_count": self.error_count,
                "threshold": self.thresholds["errors"],
                "last_error": self.last_error.isoformat() if self.last_error else None
            }

        except Exception as e:
            logger.error(f"Error checking errors: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }

    def record_error(self, operation: str, error: str) -> None:
        """Record an error.

        Args:
            operation: Operation where error occurred
            error: Error message
        """
        try:
            self.error_count += 1
            self.last_error = datetime.now()

            # Add to history
            self.check_history.append({
                "timestamp": self.last_error.isoformat(),
                "type": "error",
                "operation": operation,
                "error": error
            })

            # Trim history
            if len(self.check_history) > 100:
                self.check_history = self.check_history[-100:]

        except Exception as e:
            logger.error(f"Error recording health error: {e}")

    def get_checks(self) -> List[Dict[str, Any]]:
        """Get recent health checks.

        Returns:
            List of recent health check results
        """
        return self.check_history

    def get_status(self) -> Dict[str, Any]:
        """Get current health status.

        Returns:
            Dictionary containing current health status
        """
        return {
            "sniffer_type": self.sniffer_type,
            "status": self.status,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "error_count": self.error_count,
            "last_error": self.last_error.isoformat() if self.last_error else None
        }

    def set_threshold(self, check_name: str, value: float) -> None:
        """Set threshold for a health check.

        Args:
            check_name: Name of check to set threshold for
            value: Threshold value
        """
        if check_name in self.thresholds:
            self.thresholds[check_name] = value

    def reset(self) -> None:
        """Reset health checker to initial state."""
        try:
            self.status = "healthy"
            self.error_count = 0
            self.last_error = None
            self.check_history.clear()
            self.last_update = None

        except Exception as e:
            logger.error(f"Error resetting health checker: {e}")

    async def cleanup(self) -> None:
        """Clean up health checker."""
        try:
            # Reset state
            self.reset()

            # Additional cleanup if needed
            pass

        except Exception as e:
            logger.error(f"Error cleaning up health checker: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """Get health summary.

        Returns:
            Dictionary containing health summary
        """
        try:
            return {
                "sniffer_type": self.sniffer_type,
                "current_status": self.status,
                "error_rate": self.error_count / len(self.check_history)
                if self.check_history else 0.0,
                "last_check": self.last_update.isoformat()
                if self.last_update else None,
                "checks_performed": len(self.check_history),
                "current_thresholds": self.thresholds
            }

        except Exception as e:
            logger.error(f"Error getting health summary: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
