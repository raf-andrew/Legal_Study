#!/usr/bin/env python3
"""
Platform Monitoring Setup Script
This script sets up monitoring infrastructure and configurations.
"""

import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from sniffing.monitoring.sniffing_monitor import SniffingMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring_setup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class MonitoringSetup:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "steps": {},
            "overall_status": "pending",
            "execution_time": 0,
            "summary": {}
        }

        # Define required directories
        self.directories = [
            "monitoring/prometheus",
            "monitoring/grafana",
            "monitoring/alertmanager",
            "monitoring/dashboards",
            "monitoring/rules"
        ]

        # Define Prometheus configuration
        self.prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "alerting": {
                "alertmanagers": [
                    {
                        "static_configs": [
                            {
                                "targets": ["localhost:9093"]
                            }
                        ]
                    }
                ]
            },
            "rule_files": [
                "rules/*.yml"
            ],
            "scrape_configs": [
                {
                    "job_name": "platform",
                    "static_configs": [
                        {
                            "targets": ["localhost:8000"]
                        }
                    ]
                },
                {
                    "job_name": "ai_service",
                    "static_configs": [
                        {
                            "targets": ["localhost:8001"]
                        }
                    ]
                },
                {
                    "job_name": "notification_service",
                    "static_configs": [
                        {
                            "targets": ["localhost:8002"]
                        }
                    ]
                }
            ]
        }

        # Define Alertmanager configuration
        self.alertmanager_config = {
            "global": {
                "resolve_timeout": "5m"
            },
            "route": {
                "group_by": ["alertname"],
                "group_wait": "10s",
                "group_interval": "10m",
                "repeat_interval": "1h",
                "receiver": "email-notifications"
            },
            "receivers": [
                {
                    "name": "email-notifications",
                    "email_configs": [
                        {
                            "to": "admin@example.com",
                            "from": "alertmanager@example.com",
                            "smarthost": "smtp.example.com:587",
                            "auth_username": "alertmanager",
                            "auth_password": "password"
                        }
                    ]
                }
            ]
        }

        # Define alert rules
        self.alert_rules = {
            "groups": [
                {
                    "name": "platform_alerts",
                    "rules": [
                        {
                            "alert": "HighCPUUsage",
                            "expr": "cpu_usage > 80",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High CPU usage detected",
                                "description": "CPU usage is above 80% for 5 minutes"
                            }
                        },
                        {
                            "alert": "HighMemoryUsage",
                            "expr": "memory_usage > 85",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High memory usage detected",
                                "description": "Memory usage is above 85% for 5 minutes"
                            }
                        },
                        {
                            "alert": "APIHighLatency",
                            "expr": "http_request_duration_seconds > 1",
                            "for": "5m",
                            "labels": {
                                "severity": "warning"
                            },
                            "annotations": {
                                "summary": "High API latency detected",
                                "description": "API requests are taking more than 1 second"
                            }
                        }
                    ]
                }
            ]
        }

        # Define Grafana dashboards
        self.dashboards = {
            "platform_overview": {
                "title": "Platform Overview",
                "panels": [
                    {
                        "title": "CPU Usage",
                        "type": "graph",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "cpu_usage"
                            }
                        ]
                    },
                    {
                        "title": "Memory Usage",
                        "type": "graph",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "memory_usage"
                            }
                        ]
                    },
                    {
                        "title": "API Request Rate",
                        "type": "graph",
                        "datasource": "Prometheus",
                        "targets": [
                            {
                                "expr": "rate(http_requests_total[5m])"
                            }
                        ]
                    }
                ]
            }
        }

    def setup_directories(self) -> Dict:
        """Create monitoring directories"""
        try:
            for directory in self.directories:
                os.makedirs(directory, exist_ok=True)

            return {
                "status": "pass",
                "details": {
                    "directories_created": self.directories
                }
            }
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_prometheus(self) -> Dict:
        """Set up Prometheus configuration"""
        try:
            config_file = "monitoring/prometheus/prometheus.yml"
            with open(config_file, "w") as f:
                yaml.dump(self.prometheus_config, f)

            return {
                "status": "pass",
                "details": {
                    "config_file": config_file
                }
            }
        except Exception as e:
            logger.error(f"Error setting up Prometheus: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_alertmanager(self) -> Dict:
        """Set up Alertmanager configuration"""
        try:
            config_file = "monitoring/alertmanager/alertmanager.yml"
            with open(config_file, "w") as f:
                yaml.dump(self.alertmanager_config, f)

            return {
                "status": "pass",
                "details": {
                    "config_file": config_file
                }
            }
        except Exception as e:
            logger.error(f"Error setting up Alertmanager: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_alert_rules(self) -> Dict:
        """Set up alert rules"""
        try:
            rules_file = "monitoring/rules/platform_alerts.yml"
            with open(rules_file, "w") as f:
                yaml.dump(self.alert_rules, f)

            return {
                "status": "pass",
                "details": {
                    "rules_file": rules_file
                }
            }
        except Exception as e:
            logger.error(f"Error setting up alert rules: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_grafana_dashboards(self) -> Dict:
        """Set up Grafana dashboards"""
        try:
            for name, dashboard in self.dashboards.items():
                dashboard_file = f"monitoring/dashboards/{name}.json"
                with open(dashboard_file, "w") as f:
                    json.dump(dashboard, f, indent=2)

            return {
                "status": "pass",
                "details": {
                    "dashboards": list(self.dashboards.keys())
                }
            }
        except Exception as e:
            logger.error(f"Error setting up Grafana dashboards: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_docker_compose(self) -> Dict:
        """Set up Docker Compose configuration"""
        try:
            docker_compose = {
                "version": "3",
                "services": {
                    "prometheus": {
                        "image": "prom/prometheus:latest",
                        "ports": ["9090:9090"],
                        "volumes": [
                            "./monitoring/prometheus:/etc/prometheus",
                            "./monitoring/rules:/etc/prometheus/rules"
                        ]
                    },
                    "alertmanager": {
                        "image": "prom/alertmanager:latest",
                        "ports": ["9093:9093"],
                        "volumes": [
                            "./monitoring/alertmanager:/etc/alertmanager"
                        ]
                    },
                    "grafana": {
                        "image": "grafana/grafana:latest",
                        "ports": ["3000:3000"],
                        "volumes": [
                            "./monitoring/grafana:/var/lib/grafana",
                            "./monitoring/dashboards:/etc/grafana/provisioning/dashboards"
                        ]
                    }
                }
            }

            with open("docker-compose.monitoring.yml", "w") as f:
                yaml.dump(docker_compose, f)

            return {
                "status": "pass",
                "details": {
                    "config_file": "docker-compose.monitoring.yml"
                }
            }
        except Exception as e:
            logger.error(f"Error setting up Docker Compose: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def run_setup(self):
        """Run all setup steps"""
        start_time = time.time()

        # Run setup steps
        self.results["steps"]["directories"] = self.setup_directories()
        self.results["steps"]["prometheus"] = self.setup_prometheus()
        self.results["steps"]["alertmanager"] = self.setup_alertmanager()
        self.results["steps"]["alert_rules"] = self.setup_alert_rules()
        self.results["steps"]["grafana"] = self.setup_grafana_dashboards()
        self.results["steps"]["docker"] = self.setup_docker_compose()

        self.results["execution_time"] = time.time() - start_time

        # Calculate overall status
        failed_steps = [step for step in self.results["steps"].values()
                       if step["status"] != "pass"]
        self.results["overall_status"] = "fail" if failed_steps else "pass"

        # Generate summary
        self.generate_summary()

        return self.results

    def generate_summary(self):
        """Generate setup summary"""
        total_steps = len(self.results["steps"])
        passed_steps = sum(1 for step in self.results["steps"].values()
                          if step["status"] == "pass")
        failed_steps = total_steps - passed_steps

        self.results["summary"] = {
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "failed_steps": failed_steps,
            "success_rate": (passed_steps / total_steps) * 100 if total_steps > 0 else 0,
            "execution_time": self.results["execution_time"]
        }

    def save_results(self):
        """Save setup results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"setup_results/monitoring_setup_{timestamp}.json"

        os.makedirs("setup_results", exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {results_file}")

    def generate_report(self) -> str:
        """Generate a human-readable setup report"""
        report = f"""
Monitoring Setup Report
=====================
Generated at: {self.results['timestamp']}
Overall Status: {self.results['overall_status'].upper()}
Total Execution Time: {self.results['execution_time']:.2f} seconds

Summary:
--------
Total Steps: {self.results['summary']['total_steps']}
Passed Steps: {self.results['summary']['passed_steps']}
Failed Steps: {self.results['summary']['failed_steps']}
Success Rate: {self.results['summary']['success_rate']:.2f}%

Detailed Results:
---------------
"""

        for step_name, result in self.results["steps"].items():
            report += f"\n{step_name.upper()}:"
            report += f"\n  Status: {result['status'].upper()}"

            if result.get("details"):
                report += "\n  Details:"
                for key, value in result["details"].items():
                    if isinstance(value, list):
                        report += f"\n    {key}:"
                        for item in value:
                            report += f"\n      - {item}"
                    else:
                        report += f"\n    {key}: {value}"

            if result.get("error"):
                report += f"\n  Error: {result['error']}"

            report += "\n"

        return report

def main() -> int:
    """Main entry point for monitoring setup."""
    try:
        # Set up logging
        setup_logging()

        # Load configuration
        config = load_config()
        if not config:
            logger.error("Failed to load configuration")
            return 1

        # Set up monitoring
        if not setup_monitoring(config):
            logger.error("Failed to set up monitoring")
            return 1

        logger.info("Monitoring set up successfully")
        return 0

    except Exception as e:
        logger.error(f"Error setting up monitoring: {e}")
        return 1

def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def load_config() -> Optional[Dict[str, Any]]:
    """Load sniffing configuration."""
    try:
        config_path = Path("sniffing/config/sniffing_config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return None

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return config

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def setup_monitoring(config: Dict[str, Any]) -> bool:
    """Set up monitoring system."""
    try:
        # Get monitoring configuration
        monitoring_config = config.get("monitoring", {})
        if not monitoring_config.get("enabled", False):
            logger.info("Monitoring is disabled in configuration")
            return True

        # Create directories
        if not create_directories(monitoring_config):
            return False

        # Set up Prometheus
        if not setup_prometheus(monitoring_config):
            return False

        # Set up alerting
        if not setup_alerting(monitoring_config):
            return False

        # Initialize monitor
        monitor = SniffingMonitor(monitoring_config)

        # Start monitoring
        import asyncio
        asyncio.run(monitor.start_monitoring())

        return True

    except Exception as e:
        logger.error(f"Error setting up monitoring: {e}")
        return False

def create_directories(config: Dict[str, Any]) -> bool:
    """Create monitoring directories."""
    try:
        directories = [
            config.get("metrics_path", "metrics"),
            config.get("alerts_path", "alerts"),
            config.get("health_path", "health"),
            config.get("reports_path", "reports")
        ]

        for directory in directories:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")

        return True

    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False

def setup_prometheus(config: Dict[str, Any]) -> bool:
    """Set up Prometheus monitoring."""
    try:
        # Create Prometheus configuration
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "scrape_configs": [
                {
                    "job_name": "sniffing",
                    "static_configs": [
                        {
                            "targets": [
                                f"localhost:{config.get('prometheus_port', 9090)}"
                            ]
                        }
                    ]
                }
            ]
        }

        # Write configuration
        config_path = Path("monitoring/prometheus/prometheus.yml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(prometheus_config, f)

        logger.info("Prometheus configuration created")
        return True

    except Exception as e:
        logger.error(f"Error setting up Prometheus: {e}")
        return False

def setup_alerting(config: Dict[str, Any]) -> bool:
    """Set up alerting system."""
    try:
        alerts_config = config.get("alerts", {})

        # Set up Slack alerts
        if alerts_config.get("slack", {}).get("enabled", False):
            if not setup_slack_alerts(alerts_config["slack"]):
                return False

        # Set up email alerts
        if alerts_config.get("email", {}).get("enabled", False):
            if not setup_email_alerts(alerts_config["email"]):
                return False

        return True

    except Exception as e:
        logger.error(f"Error setting up alerting: {e}")
        return False

def setup_slack_alerts(config: Dict[str, Any]) -> bool:
    """Set up Slack alerting."""
    try:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return True

        # Create Slack configuration
        slack_config = {
            "webhook_url": webhook_url,
            "channel": config.get("channel", "#monitoring"),
            "username": config.get("username", "Sniffing Monitor"),
            "icon_emoji": config.get("icon_emoji", ":mag:")
        }

        # Write configuration
        config_path = Path("monitoring/alerts/slack.yml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(slack_config, f)

        logger.info("Slack alerting configured")
        return True

    except Exception as e:
        logger.error(f"Error setting up Slack alerts: {e}")
        return False

def setup_email_alerts(config: Dict[str, Any]) -> bool:
    """Set up email alerting."""
    try:
        smtp_server = config.get("smtp_server")
        if not smtp_server:
            logger.warning("SMTP server not configured")
            return True

        # Create email configuration
        email_config = {
            "smtp_server": smtp_server,
            "smtp_port": config.get("smtp_port", 587),
            "from_address": config.get("from_address"),
            "to_addresses": config.get("to_addresses", []),
            "use_tls": config.get("use_tls", True)
        }

        # Write configuration
        config_path = Path("monitoring/alerts/email.yml")
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(email_config, f)

        logger.info("Email alerting configured")
        return True

    except Exception as e:
        logger.error(f"Error setting up email alerts: {e}")
        return False

def verify_monitoring() -> bool:
    """Verify monitoring setup."""
    try:
        # Check directories
        required_dirs = [
            "metrics",
            "alerts",
            "health",
            "reports",
            "monitoring/prometheus",
            "monitoring/alerts"
        ]

        for directory in required_dirs:
            path = Path(directory)
            if not path.exists():
                logger.error(f"Required directory not found: {directory}")
                return False

        # Check configurations
        required_configs = [
            "monitoring/prometheus/prometheus.yml",
            "monitoring/alerts/slack.yml",
            "monitoring/alerts/email.yml"
        ]

        for config_file in required_configs:
            path = Path(config_file)
            if not path.exists():
                logger.warning(f"Configuration file not found: {config_file}")

        # Check Prometheus
        import subprocess
        try:
            result = subprocess.run(
                ["prometheus", "--version"],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Prometheus version: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            logger.warning("Prometheus not installed")
        except FileNotFoundError:
            logger.warning("Prometheus not found in PATH")

        return True

    except Exception as e:
        logger.error(f"Error verifying monitoring: {e}")
        return False

def cleanup_old_monitoring() -> bool:
    """Clean up old monitoring files."""
    try:
        # Clean up old files
        old_files = [
            "monitoring/prometheus/prometheus.yml.old",
            "monitoring/alerts/slack.yml.old",
            "monitoring/alerts/email.yml.old"
        ]

        for file in old_files:
            path = Path(file)
            if path.exists():
                path.unlink()
                logger.info(f"Removed old file: {file}")

        return True

    except Exception as e:
        logger.error(f"Error cleaning up old monitoring: {e}")
        return False

if __name__ == "__main__":
    sys.exit(main())
