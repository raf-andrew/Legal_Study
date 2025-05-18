#!/usr/bin/env python3

import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
import argparse
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.setup/logs/monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DeploymentMonitor:
    def __init__(self, service: Optional[str] = None):
        self.base_dir = Path('.')
        self.logs_dir = self.base_dir / '.setup' / 'logs'
        self.service = service
        self.monitoring_results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'overall_status': 'monitoring',
            'service_monitored': service if service else 'all'
        }

    def monitor_log_file(self, log_file: Path) -> None:
        """Monitor a log file in real-time."""
        try:
            with open(log_file, 'r') as f:
                # Go to end of file
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if line:
                        print(line.strip())
                    time.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error monitoring log file: {str(e)}")

    def monitor_deployment_log(self) -> None:
        """Monitor the deployment log file."""
        log_file = self.logs_dir / 'deployment.log'
        if not log_file.exists():
            logger.error(f"Deployment log file not found: {log_file}")
            return

        logger.info(f"Monitoring deployment log: {log_file}")
        self.monitor_log_file(log_file)

    def monitor_service_log(self, service: str) -> None:
        """Monitor a specific service log file."""
        log_file = self.logs_dir / f'{service}.log'
        if not log_file.exists():
            logger.error(f"Service log file not found: {log_file}")
            return

        logger.info(f"Monitoring {service} log: {log_file}")
        self.monitor_log_file(log_file)

    def monitor_all(self) -> None:
        """Monitor all deployment-related logs."""
        if self.service:
            self.monitor_service_log(self.service)
        else:
            self.monitor_deployment_log()

def main():
    parser = argparse.ArgumentParser(description='Deployment Monitor')
    parser.add_argument('--service', type=str, choices=['mysql', 'redis'],
                      help='Monitor specific service only')
    args = parser.parse_args()

    monitor = DeploymentMonitor(args.service)
    monitor.monitor_all()

if __name__ == '__main__':
    main()
