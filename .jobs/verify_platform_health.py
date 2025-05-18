import requests
import psutil
import json
import redis
import logging
from datetime import datetime
from typing import Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlatformHealthChecker:
    def __init__(self, config_path: str = "config/platform_config.json"):
        self.config = self._load_config(config_path)
        self.results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "api": {
                    "endpoints": ["http://localhost:8000/health"],
                    "timeout": 5
                },
                "redis": {
                    "host": "localhost",
                    "port": 6379
                },
                "thresholds": {
                    "cpu_percent": 80,
                    "memory_percent": 80,
                    "disk_percent": 80
                }
            }

    def check_api_health(self) -> Dict:
        results = {}
        for endpoint in self.config["api"]["endpoints"]:
            try:
                response = requests.get(endpoint, timeout=self.config["api"]["timeout"])
                results[endpoint] = {
                    "status": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds(),
                    "status_code": response.status_code
                }
            except Exception as e:
                results[endpoint] = {
                    "status": False,
                    "error": str(e)
                }
        return results

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

    def check_cache_health(self) -> Dict:
        try:
            redis_client = redis.Redis(
                host=self.config["redis"]["host"],
                port=self.config["redis"]["port"]
            )
            redis_info = redis_client.info()
            return {
                "status": True,
                "connected_clients": redis_info["connected_clients"],
                "used_memory": redis_info["used_memory"],
                "hit_rate": redis_info["keyspace_hits"] / (redis_info["keyspace_hits"] + redis_info["keyspace_misses"])
                if (redis_info["keyspace_hits"] + redis_info["keyspace_misses"]) > 0 else 0
            }
        except Exception as e:
            return {
                "status": False,
                "error": str(e)
            }

    def run_health_check(self) -> Dict:
        with ThreadPoolExecutor() as executor:
            api_future = executor.submit(self.check_api_health)
            resources_future = executor.submit(self.check_system_resources)
            cache_future = executor.submit(self.check_cache_health)

            self.results = {
                "timestamp": datetime.now().isoformat(),
                "api_health": api_future.result(),
                "system_resources": resources_future.result(),
                "cache_health": cache_future.result(),
                "overall_status": "healthy"  # Will be updated based on checks
            }

        # Evaluate overall status
        if any(not endpoint["status"] for endpoint in self.results["api_health"].values()):
            self.results["overall_status"] = "degraded"
        
        if (self.results["system_resources"]["cpu"]["percent"] > self.config["thresholds"]["cpu_percent"] or
            self.results["system_resources"]["memory"]["percent"] > self.config["thresholds"]["memory_percent"] or
            self.results["system_resources"]["disk"]["percent"] > self.config["thresholds"]["disk_percent"]):
            self.results["overall_status"] = "at_risk"

        if not self.results["cache_health"]["status"]:
            self.results["overall_status"] = "degraded"

        return self.results

    def generate_report(self, output_format: str = "json") -> str:
        if not self.results:
            self.run_health_check()

        if output_format == "json":
            return json.dumps(self.results, indent=2)
        elif output_format == "text":
            report = []
            report.append(f"Platform Health Report - {self.results['timestamp']}")
            report.append(f"Overall Status: {self.results['overall_status'].upper()}")
            report.append("\nAPI Health:")
            for endpoint, status in self.results["api_health"].items():
                report.append(f"  {endpoint}: {'✓' if status['status'] else '✗'}")
            
            resources = self.results["system_resources"]
            report.append("\nSystem Resources:")
            report.append(f"  CPU Usage: {resources['cpu']['percent']}%")
            report.append(f"  Memory Usage: {resources['memory']['percent']}%")
            report.append(f"  Disk Usage: {resources['disk']['percent']}%")
            
            cache = self.results["cache_health"]
            report.append("\nCache Health:")
            report.append(f"  Status: {'✓' if cache['status'] else '✗'}")
            if cache['status']:
                report.append(f"  Connected Clients: {cache['connected_clients']}")
                report.append(f"  Cache Hit Rate: {cache['hit_rate']:.2%}")
            
            return "\n".join(report)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

def main():
    checker = PlatformHealthChecker()
    report = checker.generate_report("text")
    print(report)
    
    # Also save JSON report
    with open(f"reports/platform_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(checker.results, f, indent=2)

if __name__ == "__main__":
    main() 