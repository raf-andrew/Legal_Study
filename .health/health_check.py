#!/usr/bin/env python3
import os
import sys
import logging
import datetime
import psutil
import requests
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.health/logs/health_check.log'),
        logging.StreamHandler()
    ]
)

class HealthCheck:
    def __init__(self):
        self.logs_dir = Path('.health/logs')
        self.logs_dir.mkdir(exist_ok=True)
        self.results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'checks': {}
        }

    def check_disk_space(self):
        """Check available disk space"""
        try:
            usage = psutil.disk_usage('/')
            self.results['checks']['disk_space'] = {
                'status': 'OK' if usage.percent < 90 else 'WARNING',
                'details': {
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                }
            }
        except Exception as e:
            self.results['checks']['disk_space'] = {
                'status': 'ERROR',
                'details': str(e)
            }

    def check_memory_usage(self):
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            self.results['checks']['memory'] = {
                'status': 'OK' if memory.percent < 90 else 'WARNING',
                'details': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent
                }
            }
        except Exception as e:
            self.results['checks']['memory'] = {
                'status': 'ERROR',
                'details': str(e)
            }

    def check_cpu_usage(self):
        """Check CPU usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            self.results['checks']['cpu'] = {
                'status': 'OK' if cpu_percent < 90 else 'WARNING',
                'details': {
                    'usage_percent': cpu_percent
                }
            }
        except Exception as e:
            self.results['checks']['cpu'] = {
                'status': 'ERROR',
                'details': str(e)
            }

    def check_file_system(self):
        """Check critical file system paths"""
        try:
            critical_paths = [
                '.health',
                '.backup',
                '.config',
                '.security'
            ]
            status = {}
            for path in critical_paths:
                if Path(path).exists():
                    status[path] = 'OK'
                else:
                    status[path] = 'ERROR'
            
            self.results['checks']['file_system'] = {
                'status': 'OK' if all(v == 'OK' for v in status.values()) else 'ERROR',
                'details': status
            }
        except Exception as e:
            self.results['checks']['file_system'] = {
                'status': 'ERROR',
                'details': str(e)
            }

    def run_all_checks(self):
        """Run all health checks"""
        self.check_disk_space()
        self.check_memory_usage()
        self.check_cpu_usage()
        self.check_file_system()
        
        # Save results
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.logs_dir / f'health_check_{timestamp}.json'
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Log summary
        logging.info("Health check completed")
        for check, result in self.results['checks'].items():
            logging.info(f"{check}: {result['status']}")

    def get_overall_status(self):
        """Get overall system status"""
        statuses = [check['status'] for check in self.results['checks'].values()]
        if 'ERROR' in statuses:
            return 'ERROR'
        elif 'WARNING' in statuses:
            return 'WARNING'
        return 'OK'

if __name__ == '__main__':
    health_check = HealthCheck()
    health_check.run_all_checks()
    overall_status = health_check.get_overall_status()
    logging.info(f"Overall system status: {overall_status}")
    
    if overall_status == 'ERROR':
        sys.exit(1)
    elif overall_status == 'WARNING':
        sys.exit(2)
    sys.exit(0) 