#!/usr/bin/env python3

import os
import sys
import logging
import time
import psutil
import json
from datetime import datetime
from pathlib import Path
import yaml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TestMonitor:
    def __init__(self):
        self.config = None
        self.metrics = {
            'start_time': datetime.now().isoformat(),
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'test_status': {},
            'errors': []
        }
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load monitoring configuration."""
        try:
            config_file = Path('.config/test_config.yaml')
            if not config_file.exists():
                logger.error("Configuration file not found")
                sys.exit(1)
            
            with open(config_file) as f:
                self.config = yaml.safe_load(f)
            
            logger.info("Loaded monitoring configuration")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def collect_metrics(self):
        """Collect system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics['cpu_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'value': cpu_percent
            })
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['memory_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'total': memory.total,
                'used': memory.used,
                'percent': memory.percent
            })
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.metrics['disk_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'total': disk.total,
                'used': disk.used,
                'percent': disk.percent
            })
            
            logger.info(f"Collected metrics: CPU={cpu_percent}%, Memory={memory.percent}%, Disk={disk.percent}%")
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            self.metrics['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            })
    
    def check_resource_limits(self):
        """Check if resource usage exceeds limits."""
        try:
            limits = self.config['resources']
            alerts = []
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > limits['cpu_limit']:
                alerts.append(f"CPU usage ({cpu_percent}%) exceeds limit ({limits['cpu_limit']}%)")
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > limits['memory_limit']:
                alerts.append(f"Memory usage ({memory.percent}%) exceeds limit ({limits['memory_limit']}%)")
            
            # Check disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > limits['file_limit']:
                alerts.append(f"Disk usage ({disk.percent}%) exceeds limit ({limits['file_limit']}%)")
            
            if alerts:
                self.send_alert(alerts)
            
        except Exception as e:
            logger.error(f"Error checking resource limits: {e}")
    
    def monitor_test(self, test_name):
        """Monitor a specific test."""
        try:
            start_time = time.time()
            self.metrics['test_status'][test_name] = {
                'start_time': datetime.now().isoformat(),
                'status': 'running'
            }
            
            # Run the test
            logger.info(f"Starting test: {test_name}")
            # Add your test execution code here
            
            # Update status
            self.metrics['test_status'][test_name].update({
                'end_time': datetime.now().isoformat(),
                'duration': time.time() - start_time,
                'status': 'completed'
            })
            
        except Exception as e:
            logger.error(f"Error in test {test_name}: {e}")
            self.metrics['test_status'][test_name].update({
                'end_time': datetime.now().isoformat(),
                'duration': time.time() - start_time,
                'status': 'failed',
                'error': str(e)
            })
            self.metrics['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'test': test_name,
                'error': str(e)
            })
    
    def send_alert(self, alerts):
        """Send alert notifications."""
        try:
            if not self.config['notifications']['email']['enabled']:
                return
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.config['notifications']['email']['sender']
            msg['To'] = self.config['notifications']['email']['receiver']
            msg['Subject'] = f"Test Monitoring Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Email body
            body = f"""
            Test Monitoring Alert
            =====================
            
            The following issues were detected:
            
            {chr(10).join(f"- {alert}" for alert in alerts)}
            
            Please check the test logs for more information.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(
                self.config['notifications']['email']['smtp_host'],
                self.config['notifications']['email']['smtp_port']
            ) as server:
                server.send_message(msg)
            
            logger.info("Sent alert notification")
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    def save_metrics(self):
        """Save collected metrics."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            metrics_file = Path('.logs') / f'metrics_{timestamp}.json'
            
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            
            logger.info(f"Saved metrics to {metrics_file}")
            
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def monitor(self):
        """Main monitoring process."""
        try:
            logger.info("Starting test monitoring")
            
            # Monitor smoke tests
            self.monitor_test('smoke_tests')
            self.collect_metrics()
            self.check_resource_limits()
            
            # Monitor ACID tests
            self.monitor_test('acid_tests')
            self.collect_metrics()
            self.check_resource_limits()
            
            # Monitor chaos tests
            self.monitor_test('chaos_tests')
            self.collect_metrics()
            self.check_resource_limits()
            
            # Monitor security tests
            self.monitor_test('security_tests')
            self.collect_metrics()
            self.check_resource_limits()
            
            # Save metrics
            self.save_metrics()
            
            logger.info("Test monitoring completed")
            
        except Exception as e:
            logger.error(f"Error in monitoring process: {e}")
            sys.exit(1)

if __name__ == "__main__":
    monitor = TestMonitor()
    monitor.monitor() 