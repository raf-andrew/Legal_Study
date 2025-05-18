import psutil
import requests
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlatformHealthMonitor:
    def __init__(self, config_path: str = "config/monitoring_config.json"):
        self.config = self._load_config(config_path)
        self.results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "endpoints": {
                    "api": "http://localhost:8000/health",
                    "ai": "http://localhost:8000/ai/health",
                    "notifications": "http://localhost:8000/notifications/health"
                },
                "thresholds": {
                    "cpu_percent": 80,
                    "memory_percent": 80,
                    "disk_percent": 80,
                    "response_time": 1.0
                },
                "check_interval": 60
            }

    def check_system_resources(self) -> Dict:
        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count()
            },
            "memory": {
                "percent": psutil.virtual_memory().percent,
                "available": psutil.virtual_memory().available
            },
            "disk": {
                "percent": psutil.disk_usage('/').percent,
                "free": psutil.disk_usage('/').free
            }
        }

    def check_endpoint_health(self, name: str, url: str) -> Dict:
        try:
            start_time = time.time()
            response = requests.get(url, timeout=5)
            response_time = time.time() - start_time

            return {
                "status": response.status_code == 200,
                "response_time": response_time,
                "status_code": response.status_code
            }
        except Exception as e:
            return {
                "status": False,
                "error": str(e)
            }

    def check_platform_health(self) -> Dict:
        results = {
            "timestamp": datetime.now().isoformat(),
            "system_resources": self.check_system_resources(),
            "endpoints": {},
            "alerts": []
        }

        # Check endpoint health
        with ThreadPoolExecutor() as executor:
            futures = {
                name: executor.submit(self.check_endpoint_health, name, url)
                for name, url in self.config["endpoints"].items()
            }
            for name, future in futures.items():
                results["endpoints"][name] = future.result()

        # Generate alerts
        resources = results["system_resources"]
        if resources["cpu"]["percent"] > self.config["thresholds"]["cpu_percent"]:
            results["alerts"].append(f"High CPU usage: {resources['cpu']['percent']}%")
        
        if resources["memory"]["percent"] > self.config["thresholds"]["memory_percent"]:
            results["alerts"].append(f"High memory usage: {resources['memory']['percent']}%")
        
        if resources["disk"]["percent"] > self.config["thresholds"]["disk_percent"]:
            results["alerts"].append(f"High disk usage: {resources['disk']['percent']}%")

        for name, endpoint in results["endpoints"].items():
            if not endpoint["status"]:
                results["alerts"].append(f"{name} endpoint is down")
            elif endpoint["response_time"] > self.config["thresholds"]["response_time"]:
                results["alerts"].append(f"{name} endpoint is slow: {endpoint['response_time']:.2f}s")

        self.results = results
        return results

    def generate_report(self, output_format: str = "text") -> str:
        if not self.results:
            self.check_platform_health()

        if output_format == "json":
            return json.dumps(self.results, indent=2)
        elif output_format == "text":
            report = []
            report.append(f"Platform Health Report - {self.results['timestamp']}")
            
            # System Resources
            resources = self.results["system_resources"]
            report.append("\nSystem Resources:")
            report.append(f"  CPU Usage: {resources['cpu']['percent']}%")
            report.append(f"  Memory Usage: {resources['memory']['percent']}%")
            report.append(f"  Disk Usage: {resources['disk']['percent']}%")
            
            # Endpoint Health
            report.append("\nEndpoint Health:")
            for name, status in self.results["endpoints"].items():
                status_symbol = "✓" if status["status"] else "✗"
                error_msg = f" - {status.get('error', '')}" if not status["status"] else ""
                report.append(f"  {name}: {status_symbol}{error_msg}")
                if status["status"]:
                    report.append(f"    Response Time: {status['response_time']:.3f}s")
            
            # Alerts
            if self.results["alerts"]:
                report.append("\nAlerts:")
                for alert in self.results["alerts"]:
                    report.append(f"  ⚠ {alert}")
            
            return "\n".join(report)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

def main():
    monitor = PlatformHealthMonitor()
    
    while True:
        report = monitor.generate_report("text")
        print("\n" + "="*50)
        print(report)
        
        # Save detailed JSON report
        with open(f"reports/platform_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(monitor.results, f, indent=2)
        
        time.sleep(monitor.config["check_interval"])

if __name__ == "__main__":
    main() 