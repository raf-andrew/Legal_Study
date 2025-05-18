import psutil
import time
import json
import os
from datetime import datetime
import logging

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

def get_system_metrics():
    """Get current system metrics"""
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "network_io": {
            "bytes_sent": psutil.net_io_counters().bytes_sent,
            "bytes_recv": psutil.net_io_counters().bytes_recv
        },
        "process_count": len(psutil.pids())
    }

def monitor_resources(duration=300, interval=1):
    """Monitor system resources for a specified duration"""
    metrics = []
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            metrics.append(get_system_metrics())
            time.sleep(interval)
            
            # Log current metrics
            current = metrics[-1]
            logger.info(
                f"CPU: {current['cpu_percent']}%, "
                f"Memory: {current['memory_percent']}%, "
                f"Disk: {current['disk_usage']}%"
            )
    
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
    
    finally:
        # Save metrics to file
        with open('.logs/resource_metrics.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Calculate statistics
        if metrics:
            cpu_avg = sum(m['cpu_percent'] for m in metrics) / len(metrics)
            memory_avg = sum(m['memory_percent'] for m in metrics) / len(metrics)
            disk_avg = sum(m['disk_usage'] for m in metrics) / len(metrics)
            
            logger.info(f"\nResource Usage Summary:")
            logger.info(f"Average CPU Usage: {cpu_avg:.2f}%")
            logger.info(f"Average Memory Usage: {memory_avg:.2f}%")
            logger.info(f"Average Disk Usage: {disk_avg:.2f}%")
            
            # Save summary
            summary = {
                "duration": duration,
                "interval": interval,
                "average_cpu": cpu_avg,
                "average_memory": memory_avg,
                "average_disk": disk_avg,
                "max_cpu": max(m['cpu_percent'] for m in metrics),
                "max_memory": max(m['memory_percent'] for m in metrics),
                "max_disk": max(m['disk_usage'] for m in metrics)
            }
            
            with open('.logs/resource_summary.json', 'w') as f:
                json.dump(summary, f, indent=2)

def main():
    """Main monitoring function"""
    # Create logs directory if it doesn't exist
    os.makedirs('.logs', exist_ok=True)
    
    # Start monitoring
    logger.info("Starting resource monitoring")
    monitor_resources()
    logger.info("Resource monitoring completed")

if __name__ == "__main__":
    main() 