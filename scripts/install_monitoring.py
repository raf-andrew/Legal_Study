"""
Script to install monitoring infrastructure.
"""
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

import yaml

logger = logging.getLogger("install_monitoring")

class MonitoringInstaller:
    """Class for installing monitoring infrastructure."""

    def __init__(self):
        """Initialize installer."""
        self.config_path = Path("sniffing/config/sniffing_config.yaml")
        self.monitoring_dir = Path("monitoring")
        self.prometheus_dir = self.monitoring_dir / "prometheus"
        self.grafana_dir = self.monitoring_dir / "grafana"

    def install(self) -> None:
        """Install monitoring infrastructure."""
        try:
            # Load config
            if not self.config_path.exists():
                logger.error("Config file not found")
                return

            with open(self.config_path) as f:
                config = yaml.safe_load(f)

            # Create directories
            self._create_directories()

            # Install Prometheus
            self._install_prometheus(config)

            # Install Grafana
            self._install_grafana(config)

            # Create docker-compose file
            self._create_docker_compose(config)

            logger.info("Monitoring infrastructure installed successfully!")

        except Exception as e:
            logger.error(f"Error installing monitoring: {e}")
            raise

    def _create_directories(self) -> None:
        """Create necessary directories."""
        try:
            # Create main directories
            self.monitoring_dir.mkdir(exist_ok=True)
            self.prometheus_dir.mkdir(exist_ok=True)
            self.grafana_dir.mkdir(exist_ok=True)

            # Create data directories
            (self.prometheus_dir / "data").mkdir(exist_ok=True)
            (self.grafana_dir / "data").mkdir(exist_ok=True)

        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise

    def _install_prometheus(self, config: Dict) -> None:
        """Install Prometheus.

        Args:
            config: Configuration dictionary
        """
        try:
            # Create Prometheus config
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
                                    f"localhost:{config['mcp']['monitoring']['prometheus_port']}"
                                ]
                            }
                        ]
                    }
                ]
            }

            # Write config
            config_file = self.prometheus_dir / "prometheus.yml"
            with open(config_file, "w") as f:
                yaml.dump(prometheus_config, f)

        except Exception as e:
            logger.error(f"Error installing Prometheus: {e}")
            raise

    def _install_grafana(self, config: Dict) -> None:
        """Install Grafana.

        Args:
            config: Configuration dictionary
        """
        try:
            # Create Grafana config
            grafana_config = {
                "server": {
                    "http_port": 3000
                },
                "security": {
                    "admin_user": "admin",
                    "admin_password": "admin"
                },
                "auth.anonymous": {
                    "enabled": False
                },
                "datasources": [
                    {
                        "name": "Prometheus",
                        "type": "prometheus",
                        "url": "http://prometheus:9090",
                        "access": "proxy",
                        "isDefault": True
                    }
                ]
            }

            # Write config
            config_file = self.grafana_dir / "grafana.ini"
            with open(config_file, "w") as f:
                for section, settings in grafana_config.items():
                    f.write(f"[{section}]\n")
                    for key, value in settings.items():
                        f.write(f"{key} = {value}\n")
                    f.write("\n")

            # Copy dashboards
            dashboards_dir = Path("sniffing/monitoring/dashboards")
            if dashboards_dir.exists():
                dest_dir = self.grafana_dir / "dashboards"
                dest_dir.mkdir(exist_ok=True)
                for dashboard in dashboards_dir.glob("*.json"):
                    shutil.copy2(dashboard, dest_dir)

        except Exception as e:
            logger.error(f"Error installing Grafana: {e}")
            raise

    def _create_docker_compose(self, config: Dict) -> None:
        """Create docker-compose file.

        Args:
            config: Configuration dictionary
        """
        try:
            # Create docker-compose config
            compose_config = {
                "version": "3",
                "services": {
                    "prometheus": {
                        "image": "prom/prometheus:latest",
                        "ports": [
                            "9090:9090"
                        ],
                        "volumes": [
                            "./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml",
                            "./prometheus/data:/prometheus"
                        ],
                        "command": [
                            "--config.file=/etc/prometheus/prometheus.yml",
                            "--storage.tsdb.path=/prometheus",
                            "--web.console.libraries=/usr/share/prometheus/console_libraries",
                            "--web.console.templates=/usr/share/prometheus/consoles"
                        ]
                    },
                    "grafana": {
                        "image": "grafana/grafana:latest",
                        "ports": [
                            "3000:3000"
                        ],
                        "volumes": [
                            "./grafana/grafana.ini:/etc/grafana/grafana.ini",
                            "./grafana/data:/var/lib/grafana",
                            "./grafana/dashboards:/var/lib/grafana/dashboards"
                        ],
                        "environment": [
                            "GF_SECURITY_ADMIN_USER=admin",
                            "GF_SECURITY_ADMIN_PASSWORD=admin"
                        ],
                        "depends_on": [
                            "prometheus"
                        ]
                    }
                }
            }

            # Write docker-compose file
            compose_file = self.monitoring_dir / "docker-compose.yml"
            with open(compose_file, "w") as f:
                yaml.dump(compose_config, f)

        except Exception as e:
            logger.error(f"Error creating docker-compose file: {e}")
            raise

def main() -> None:
    """Main entry point."""
    try:
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Install monitoring
        installer = MonitoringInstaller()
        installer.install()

    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    main()
