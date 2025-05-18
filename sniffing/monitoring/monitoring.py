"""
Monitoring system for sniffing infrastructure.
"""
import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import aiohttp
import psutil
from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger("monitoring")

class MonitoringSystem:
    """Monitoring system for sniffing infrastructure."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_path = Path(config.get("metrics_path", "metrics"))
        self.alerts_path = Path(config.get("alerts_path", "alerts"))
        self.health_path = Path(config.get("health_path", "health"))
        self._setup_directories()
        self._setup_metrics()
        self._setup_alerts()

    def _setup_directories(self) -> None:
        """Set up monitoring directories."""
        self.metrics_path.mkdir(parents=True, exist_ok=True)
        self.alerts_path.mkdir(parents=True, exist_ok=True)
        self.health_path.mkdir(parents=True, exist_ok=True)

    def _setup_metrics(self) -> None:
        """Set up Prometheus metrics."""
        # Test metrics
        self.test_counter = Counter(
            "sniffing_tests_total",
            "Total number of tests run",
            ["domain", "status"]
        )
        self.test_duration = Histogram(
            "sniffing_test_duration_seconds",
            "Test duration in seconds",
            ["domain"]
        )

        # Issue metrics
        self.issue_counter = Counter(
            "sniffing_issues_total",
            "Total number of issues found",
            ["domain", "severity"]
        )
        self.issue_fix_counter = Counter(
            "sniffing_issues_fixed_total",
            "Total number of issues fixed",
            ["domain"]
        )

        # Performance metrics
        self.cpu_usage = Gauge(
            "sniffing_cpu_usage_percent",
            "CPU usage percentage"
        )
        self.memory_usage = Gauge(
            "sniffing_memory_usage_bytes",
            "Memory usage in bytes"
        )

        # Start Prometheus server
        port = self.config.get("prometheus_port", 9090)
        start_http_server(port)

    def _setup_alerts(self) -> None:
        """Set up alerting system."""
        self.alert_channels = []

        # Set up Slack alerts
        if self.config.get("alerts", {}).get("slack", {}).get("enabled", False):
            self.alert_channels.append(self._send_slack_alert)

        # Set up email alerts
        if self.config.get("alerts", {}).get("email", {}).get("enabled", False):
            self.alert_channels.append(self._send_email_alert)

    async def start_monitoring(self) -> None:
        """Start monitoring system."""
        try:
            # Start metric collection
            asyncio.create_task(self._collect_metrics())

            # Start health checks
            asyncio.create_task(self._run_health_checks())

            logger.info("Monitoring system started")

        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")

    async def _collect_metrics(self) -> None:
        """Collect system metrics."""
        while True:
            try:
                # Collect system metrics
                self.cpu_usage.set(psutil.cpu_percent())
                self.memory_usage.set(psutil.Process().memory_info().rss)

                # Save metrics to file
                await self._save_metrics()

                # Wait for next collection
                await asyncio.sleep(self.config.get("metrics", {}).get("collection_interval", 60))

            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(5)

    async def _run_health_checks(self) -> None:
        """Run system health checks."""
        while True:
            try:
                # Run checks
                health_status = await self._check_system_health()

                # Save health status
                await self._save_health_status(health_status)

                # Check for alerts
                await self._check_alerts(health_status)

                # Wait for next check
                await asyncio.sleep(self.config.get("health_checks", {}).get("interval", 300))

            except Exception as e:
                logger.error(f"Error running health checks: {e}")
                await asyncio.sleep(5)

    async def record_test_execution(self, domain: str, duration: float, status: str) -> None:
        """Record test execution metrics."""
        try:
            # Update counters
            self.test_counter.labels(domain=domain, status=status).inc()
            self.test_duration.labels(domain=domain).observe(duration)

        except Exception as e:
            logger.error(f"Error recording test execution: {e}")

    async def record_issue(self, domain: str, severity: str) -> None:
        """Record issue metrics."""
        try:
            # Update counter
            self.issue_counter.labels(domain=domain, severity=severity).inc()

        except Exception as e:
            logger.error(f"Error recording issue: {e}")

    async def record_fix(self, domain: str) -> None:
        """Record issue fix metrics."""
        try:
            # Update counter
            self.issue_fix_counter.labels(domain=domain).inc()

        except Exception as e:
            logger.error(f"Error recording fix: {e}")

    async def _save_metrics(self) -> None:
        """Save metrics to file."""
        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.Process().memory_info().rss,
                "test_metrics": {
                    "total": self.test_counter._value.sum(),
                    "duration": self.test_duration._sum.sum()
                },
                "issue_metrics": {
                    "total": self.issue_counter._value.sum(),
                    "fixed": self.issue_fix_counter._value.sum()
                }
            }

            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            metrics_file = self.metrics_path / f"metrics_{timestamp}.json"

            with open(metrics_file, "w") as f:
                json.dump(metrics, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    async def _check_system_health(self) -> Dict[str, Any]:
        """Check system health."""
        try:
            health = {
                "timestamp": datetime.now().isoformat(),
                "status": "healthy",
                "checks": {
                    "system": self._check_system_resources(),
                    "services": await self._check_services(),
                    "storage": self._check_storage()
                }
            }

            # Update overall status
            if any(check["status"] == "unhealthy" for check in health["checks"].values()):
                health["status"] = "unhealthy"

            return health

        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent

            status = "healthy"
            if cpu_percent > 90 or memory_percent > 90:
                status = "unhealthy"

            return {
                "status": status,
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent
            }

        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _check_services(self) -> Dict[str, Any]:
        """Check service health."""
        try:
            services = self.config.get("services", {})
            results = {}

            for service, config in services.items():
                if config.get("enabled", False):
                    results[service] = await self._check_service_health(service, config)

            return results

        except Exception as e:
            logger.error(f"Error checking services: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _check_service_health(self, service: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a specific service."""
        try:
            url = config.get("health_url")
            if not url:
                return {
                    "status": "unknown",
                    "message": "No health URL configured"
                }

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "response_time": response.elapsed.total_seconds()
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "status_code": response.status
                        }

        except Exception as e:
            logger.error(f"Error checking service {service}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _check_storage(self) -> Dict[str, Any]:
        """Check storage usage."""
        try:
            usage = psutil.disk_usage("/")

            status = "healthy"
            if usage.percent > 90:
                status = "unhealthy"

            return {
                "status": status,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            }

        except Exception as e:
            logger.error(f"Error checking storage: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _save_health_status(self, status: Dict[str, Any]) -> None:
        """Save health status to file."""
        try:
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            health_file = self.health_path / f"health_{timestamp}.json"

            with open(health_file, "w") as f:
                json.dump(status, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving health status: {e}")

    async def _check_alerts(self, health_status: Dict[str, Any]) -> None:
        """Check for and send alerts."""
        try:
            if health_status["status"] == "unhealthy":
                alert = self._create_alert(health_status)
                await self._send_alert(alert)

        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

    def _create_alert(self, health_status: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert from health status."""
        return {
            "timestamp": datetime.now().isoformat(),
            "severity": "high" if health_status["status"] == "unhealthy" else "low",
            "message": f"System health is {health_status['status']}",
            "details": health_status
        }

    async def _send_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert through configured channels."""
        try:
            # Save alert
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            alert_file = self.alerts_path / f"alert_{timestamp}.json"

            with open(alert_file, "w") as f:
                json.dump(alert, f, indent=2)

            # Send through channels
            for channel in self.alert_channels:
                try:
                    await channel(alert)
                except Exception as e:
                    logger.error(f"Error sending alert through channel: {e}")

        except Exception as e:
            logger.error(f"Error sending alert: {e}")

    async def _send_slack_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert through Slack."""
        try:
            webhook_url = self.config.get("alerts", {}).get("slack", {}).get("webhook_url")
            if not webhook_url:
                return

            async with aiohttp.ClientSession() as session:
                await session.post(webhook_url, json={
                    "text": f"Alert: {alert['message']}\nSeverity: {alert['severity']}"
                })

        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")

    async def _send_email_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert through email."""
        try:
            # This would integrate with an email service
            pass
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Clean up old files
            await self._cleanup_old_files()

        except Exception as e:
            logger.error(f"Error cleaning up: {e}")

    async def _cleanup_old_files(self) -> None:
        """Clean up old monitoring files."""
        try:
            retention_days = self.config.get("retention_days", 30)
            cutoff = time.time() - (retention_days * 86400)

            # Clean up metrics files
            for file in self.metrics_path.glob("*.json"):
                if os.path.getmtime(file) < cutoff:
                    file.unlink()

            # Clean up health files
            for file in self.health_path.glob("*.json"):
                if os.path.getmtime(file) < cutoff:
                    file.unlink()

            # Clean up alert files
            for file in self.alerts_path.glob("*.json"):
                if os.path.getmtime(file) < cutoff:
                    file.unlink()

        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu_usage": self.cpu_usage._value.get(),
                "memory_usage": self.memory_usage._value.get(),
                "test_metrics": {
                    "total": self.test_counter._value.sum(),
                    "duration": self.test_duration._sum.sum()
                },
                "issue_metrics": {
                    "total": self.issue_counter._value.sum(),
                    "fixed": self.issue_fix_counter._value.sum()
                }
            }

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        try:
            return await self._check_system_health()

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
