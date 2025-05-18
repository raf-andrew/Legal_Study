#!/usr/bin/env python3

import os
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

class HealthMonitor:
    def __init__(self, config_path='health_config.json'):
        self.config = self.load_config(config_path)
        self.setup_logging()
        
    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def setup_logging(self):
        log_dir = Path('.logs')
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            filename=log_dir / 'health_monitor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def check_directory_structure(self):
        required_dirs = [
            '.cursor', '.prompts', '.jobs', '.qa',
            '.research', '.build', '.deployment', '.health',
            '.logs', '.backup'
        ]
        
        for dir_name in required_dirs:
            if not os.path.exists(dir_name):
                logging.error(f"Missing required directory: {dir_name}")
                return False
        return True
    
    def check_file_permissions(self):
        required_files = [
            '.cursor/schema.json',
            '.cursor/rules.json',
            '.prompts/template.md'
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path):
                logging.error(f"Missing required file: {file_path}")
                return False
            if not os.access(file_path, os.R_OK):
                logging.error(f"File not readable: {file_path}")
                return False
        return True
    
    def check_system_resources(self):
        # Check disk space
        total, used, free = os.statvfs('.')
        disk_space = (free * total) / (2**30)  # Convert to GB
        
        if disk_space < 1:  # Less than 1GB free
            logging.warning(f"Low disk space: {disk_space:.2f}GB free")
            return False
        return True
    
    def check_backup_system(self):
        backup_dir = Path('.backup')
        if not backup_dir.exists():
            logging.error("Backup directory not found")
            return False
            
        # Check if backup was performed today
        today = datetime.now().strftime('%Y-%m-%d')
        backup_files = list(backup_dir.glob(f'*{today}*'))
        
        if not backup_files:
            logging.warning("No backup found for today")
            return False
        return True
    
    def run_health_checks(self):
        checks = {
            'directory_structure': self.check_directory_structure(),
            'file_permissions': self.check_file_permissions(),
            'system_resources': self.check_system_resources(),
            'backup_system': self.check_backup_system()
        }
        
        status = all(checks.values())
        self.log_results(checks, status)
        return status
    
    def log_results(self, checks, overall_status):
        logging.info("Health Check Results:")
        for check, result in checks.items():
            logging.info(f"{check}: {'PASS' if result else 'FAIL'}")
        logging.info(f"Overall Status: {'HEALTHY' if overall_status else 'UNHEALTHY'}")
    
    def generate_report(self):
        report = {
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'directory_structure': self.check_directory_structure(),
                'file_permissions': self.check_file_permissions(),
                'system_resources': self.check_system_resources(),
                'backup_system': self.check_backup_system()
            }
        }
        
        report_path = Path('.health/reports') / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_path

if __name__ == "__main__":
    monitor = HealthMonitor()
    if not monitor.run_health_checks():
        sys.exit(1)
    monitor.generate_report() 