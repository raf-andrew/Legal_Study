"""
Monitoring system for sniffing operations.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger("sniffing_monitor")

class SniffingMonitor:
    """Monitor for sniffing operations."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_path = Path(config.get("metrics_path", "metrics"))
        self.alerts_path = Path(config.get("alerts_path", "alerts"))
        self.health_path = Path(config.get("health_path", "health"))
        self._setup_directories()
        self._setup_metrics()

    def _setup_directories(self) -> None:
        """Set up monitoring directories."""
        self.metrics_path.mkdir(parents=True, exist_ok=True)
        self.alerts_path.mkdir(parents=True, exist_ok=True)
        self.health_path.mkdir(parents=True, exist_ok=True)

    def _setup_metrics(self) -> None:
        """Set up Prometheus metrics."""
        # Sniffing metrics
        self.sniff_counter = Counter(
            "sniffing_total",
            "Total number of sniffing operations",
            ["domain", "status"]
        )
        self.sniff_duration = Histogram(
            "sniffing_duration_seconds",
            "Sniffing operation duration in seconds",
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
        try:
            while True:
                # Get CPU usage
                cpu_percent = psutil.cpu_percent()
                self.cpu_usage.set(cpu_percent)

                # Get memory usage
                memory = psutil.Process().memory_info()
                self.memory_usage.set(memory.rss)

                # Wait before next collection
                await asyncio.sleep(60)  # Collect every minute

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

    async def _run_health_checks(self) -> None:
        """Run system health checks."""
        try:
            while True:
                # Run checks
                health_status = await self._check_health()

                # Write health status
                health_file = self.health_path / "status.json"
                with open(health_file, "w") as f:
                    json.dump(health_status, f, indent=2)

                # Check for alerts
                if health_status["status"] != "healthy":
                    await self._send_alert(health_status)

                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes

        except Exception as e:
            logger.error(f"Error running health checks: {e}")

    async def _check_health(self) -> Dict[str, Any]:
        """Check system health."""
        try:
            checks = {
                "cpu_usage": await self._check_cpu_usage(),
                "memory_usage": await self._check_memory_usage(),
                "disk_usage": await self._check_disk_usage(),
                "prometheus": await self._check_prometheus()
            }

            # Determine overall status
            status = "healthy"
            for check in checks.values():
                if check["status"] != "healthy":
                    status = "unhealthy"
                    break

            return {
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "checks": checks
            }

        except Exception as e:
            logger.error(f"Error checking health: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    async def _check_cpu_usage(self) -> Dict[str, Any]:
        """Check CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent()
            threshold = self.config.get("cpu_threshold", 80)

            return {
                "status": "healthy" if cpu_percent < threshold else "unhealthy",
                "value": cpu_percent,
                "threshold": threshold
            }

        except Exception as e:
            logger.error(f"Error checking CPU usage: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            memory = psutil.Process().memory_info()
            memory_percent = memory.rss / psutil.virtual_memory().total * 100
            threshold = self.config.get("memory_threshold", 80)

            return {
                "status": "healthy" if memory_percent < threshold else "unhealthy",
                "value": memory_percent,
                "threshold": threshold
            }

        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _check_disk_usage(self) -> Dict[str, Any]:
        """Check disk usage."""
        try:
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            threshold = self.config.get("disk_threshold", 80)

            return {
                "status": "healthy" if disk_percent < threshold else "unhealthy",
                "value": disk_percent,
                "threshold": threshold
            }

        except Exception as e:
            logger.error(f"Error checking disk usage: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _check_prometheus(self) -> Dict[str, Any]:
        """Check Prometheus server."""
        try:
            port = self.config.get("prometheus_port", 9090)
            url = f"http://localhost:{port}/metrics"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "code": response.status
                    }

        except Exception as e:
            logger.error(f"Error checking Prometheus: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _send_alert(self, health_status: Dict[str, Any]) -> None:
        """Send alert for unhealthy status."""
        try:
            # Create alert
            alert = {
                "timestamp": datetime.now().isoformat(),
                "type": "health_check",
                "status": health_status["status"],
                "checks": health_status["checks"]
            }

            # Save alert
            alert_file = self.alerts_path / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(alert_file, "w") as f:
                json.dump(alert, f, indent=2)

            # Send notifications
            await self._send_slack_alert(alert)
            await self._send_email_alert(alert)

        except Exception as e:
            logger.error(f"Error sending alert: {e}")

    async def _send_slack_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert to Slack."""
        try:
            slack_config = self.config.get("alerts", {}).get("slack", {})
            if not slack_config.get("enabled"):
                return

            webhook_url = slack_config.get("webhook_url")
            if not webhook_url:
                return

            # Format message
            message = {
                "text": f"Health Check Alert\nStatus: {alert['status']}",
                "attachments": [{
                    "fields": [
                        {
                            "title": check_name,
                            "value": f"Status: {check_data['status']}\nValue: {check_data.get('value', 'N/A')}"
                        }
                        for check_name, check_data in alert["checks"].items()
                    ]
                }]
            }

            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=message) as response:
                    if response.status != 200:
                        logger.error(f"Error sending Slack alert: {response.status}")

        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")

    async def _send_email_alert(self, alert: Dict[str, Any]) -> None:
        """Send alert via email."""
        try:
            email_config = self.config.get("alerts", {}).get("email", {})
            if not email_config.get("enabled"):
                return

            # Email settings
            smtp_server = email_config.get("smtp_server")
            smtp_port = email_config.get("smtp_port")
            from_address = email_config.get("from_address")
            to_addresses = email_config.get("to_addresses", [])

            if not all([smtp_server, smtp_port, from_address, to_addresses]):
                return

            # Format message
            subject = f"Health Check Alert - Status: {alert['status']}"
            body = "Health Check Results:\n\n"
            for check_name, check_data in alert["checks"].items():
                body += f"{check_name}:\n"
                body += f"  Status: {check_data['status']}\n"
                body += f"  Value: {check_data.get('value', 'N/A')}\n\n"

            # Send email
            message = MIMEText(body)
            message["Subject"] = subject
            message["From"] = from_address
            message["To"] = ", ".join(to_addresses)

            async with aiosmtplib.SMTP(hostname=smtp_server, port=smtp_port) as smtp:
                await smtp.send_message(message)

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
        """Clean up old metric and alert files."""
        try:
            retention_days = self.config.get("retention_days", 30)
            cutoff = datetime.now() - timedelta(days=retention_days)

            # Clean up metrics
            for file in self.metrics_path.glob("*.json"):
                if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                    file.unlink()

            # Clean up alerts
            for file in self.alerts_path.glob("*.json"):
                if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
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
                "sniffing_metrics": {
                    "total": self.sniff_counter._value.sum(),
                    "duration": self.sniff_duration._sum.sum()
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
            return await self._check_health()

        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
