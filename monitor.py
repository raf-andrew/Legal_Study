#!/usr/bin/env python3
import psutil
import time
import logging
import json
import threading
from datetime import datetime
from pathlib import Path

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

class SystemMonitor:
    def __init__(self, interval=1):
        """Initialize the system monitor."""
        self.interval = interval
        self.running = False
        self.metrics = []
        self.start_time = None
        
        # Create metrics directory
        Path('.logs/metrics').mkdir(parents=True, exist_ok=True)
    
    def collect_metrics(self):
        """Collect system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get network I/O stats
            net_io = psutil.net_io_counters()
            
            # Get process metrics
            process = psutil.Process()
            process_metrics = {
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'threads': process.num_threads(),
                'fds': process.num_fds() if hasattr(process, 'num_fds') else None
            }
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available': memory.available,
                    'disk_percent': disk.percent,
                    'disk_free': disk.free,
                    'network': {
                        'bytes_sent': net_io.bytes_sent,
                        'bytes_recv': net_io.bytes_recv,
                        'packets_sent': net_io.packets_sent,
                        'packets_recv': net_io.packets_recv
                    }
                },
                'process': process_metrics
            }
            
            self.metrics.append(metrics)
            
            # Log warning if resources are running low
            if cpu_percent > 80:
                logger.warning(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 80:
                logger.warning(f"High memory usage: {memory.percent}%")
            if disk.percent > 80:
                logger.warning(f"High disk usage: {disk.percent}%")
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            with open('.errors/monitor_errors.log', 'a') as f:
                f.write(f"\n{datetime.now()} - Metrics collection error: {str(e)}")
    
    def start(self):
        """Start monitoring."""
        self.running = True
        self.start_time = datetime.now()
        self.monitoring_thread = threading.Thread(target=self._monitor)
        self.monitoring_thread.start()
        logger.info("System monitoring started")
    
    def stop(self):
        """Stop monitoring and save results."""
        self.running = False
        self.monitoring_thread.join()
        
        # Save metrics to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = f".logs/metrics/system_metrics_{timestamp}.json"
        
        try:
            with open(metrics_file, 'w') as f:
                json.dump({
                    'start_time': self.start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'metrics': self.metrics
                }, f, indent=2)
            
            logger.info(f"Metrics saved to {metrics_file}")
            
            # Generate summary
            self._generate_summary(metrics_file)
            
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            with open('.errors/monitor_errors.log', 'a') as f:
                f.write(f"\n{datetime.now()} - Error saving metrics: {str(e)}")
    
    def _monitor(self):
        """Monitoring loop."""
        while self.running:
            self.collect_metrics()
            time.sleep(self.interval)
    
    def _generate_summary(self, metrics_file):
        """Generate summary of collected metrics."""
        try:
            # Calculate statistics
            cpu_percentages = [m['system']['cpu_percent'] for m in self.metrics]
            memory_percentages = [m['system']['memory_percent'] for m in self.metrics]
            
            summary = {
                'duration': str(datetime.now() - self.start_time),
                'cpu': {
                    'min': min(cpu_percentages),
                    'max': max(cpu_percentages),
                    'avg': sum(cpu_percentages) / len(cpu_percentages)
                },
                'memory': {
                    'min': min(memory_percentages),
                    'max': max(memory_percentages),
                    'avg': sum(memory_percentages) / len(memory_percentages)
                },
                'samples': len(self.metrics)
            }
            
            # Save summary
            summary_file = metrics_file.replace('.json', '_summary.json')
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logger.info(f"Summary saved to {summary_file}")
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            with open('.errors/monitor_errors.log', 'a') as f:
                f.write(f"\n{datetime.now()} - Error generating summary: {str(e)}")

def main():
    """Main function to demonstrate monitoring."""
    try:
        monitor = SystemMonitor(interval=1)
        monitor.start()
        
        # Monitor for 60 seconds
        logger.info("Monitoring system for 60 seconds...")
        time.sleep(60)
        
        monitor.stop()
        logger.info("Monitoring completed")
        
    except Exception as e:
        logger.error(f"Monitor error: {e}")
        with open('.errors/monitor_errors.log', 'a') as f:
            f.write(f"\n{datetime.now()} - Monitor error: {str(e)}")
        
if __name__ == '__main__':
    main() 