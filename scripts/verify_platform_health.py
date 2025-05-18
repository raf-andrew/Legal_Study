#!/usr/bin/env python3
"""
Platform Health Verification Script
This script performs comprehensive health checks on all platform components.
"""

import os
import sys
import json
import logging
import time
import psutil
import requests
import redis
import psycopg2
from datetime import datetime
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('platform_health.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class PlatformHealthChecker:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "overall_status": "pending",
            "execution_time": 0,
            "summary": {}
        }
        
        # Define health check thresholds
        self.thresholds = {
            "cpu_usage": 80,        # %
            "memory_usage": 85,     # %
            "disk_usage": 90,       # %
            "response_time": 200,   # ms
            "error_rate": 0.1,      # %
            "queue_size": 1000,     # items
            "connection_limit": 80,  # %
            "cache_hit_rate": 80    # %
        }

    def check_system_resources(self) -> Dict:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "pass" if (
                    cpu_percent < self.thresholds["cpu_usage"] and
                    memory.percent < self.thresholds["memory_usage"] and
                    disk.percent < self.thresholds["disk_usage"]
                ) else "fail",
                "metrics": {
                    "cpu_usage": cpu_percent,
                    "memory_usage": memory.percent,
                    "disk_usage": disk.percent,
                    "memory_available": memory.available,
                    "disk_free": disk.free
                }
            }
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {"status": "error", "error": str(e)}

    def check_api_health(self) -> Dict:
        """Check API endpoints health"""
        endpoints = [
            "/api/health",
            "/api/status",
            "/api/metrics"
        ]
        
        results = []
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"http://localhost:8000{endpoint}")
                response_time = (time.time() - start_time) * 1000
                
                results.append({
                    "endpoint": endpoint,
                    "status": "pass" if response.status_code == 200 else "fail",
                    "response_time": response_time,
                    "status_code": response.status_code
                })
            except Exception as e:
                logger.error(f"Error checking endpoint {endpoint}: {e}")
                results.append({
                    "endpoint": endpoint,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "details": results
        }

    def check_database_health(self) -> Dict:
        """Check database health"""
        try:
            # Connect to database
            conn = psycopg2.connect(
                dbname="platform_db",
                user="platform_user",
                password="platform_pass",
                host="localhost"
            )
            cur = conn.cursor()
            
            # Check connection count
            cur.execute("SELECT count(*) FROM pg_stat_activity")
            connection_count = cur.fetchone()[0]
            
            # Check database size
            cur.execute("SELECT pg_database_size(current_database())")
            db_size = cur.fetchone()[0]
            
            # Check transaction rate
            cur.execute("SELECT xact_commit + xact_rollback FROM pg_stat_database WHERE datname = current_database()")
            transaction_rate = cur.fetchone()[0]
            
            conn.close()
            
            return {
                "status": "pass",
                "metrics": {
                    "connections": connection_count,
                    "database_size": db_size,
                    "transaction_rate": transaction_rate
                }
            }
        except Exception as e:
            logger.error(f"Error checking database health: {e}")
            return {"status": "error", "error": str(e)}

    def check_cache_health(self) -> Dict:
        """Check cache health"""
        try:
            # Connect to Redis
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            
            # Check connection
            redis_client.ping()
            
            # Get cache info
            info = redis_client.info()
            
            return {
                "status": "pass",
                "metrics": {
                    "connected_clients": info["connected_clients"],
                    "used_memory": info["used_memory"],
                    "hit_rate": info["keyspace_hits"] / (info["keyspace_hits"] + info["keyspace_misses"]) * 100 if info["keyspace_hits"] + info["keyspace_misses"] > 0 else 0,
                    "ops_per_second": info["instantaneous_ops_per_sec"]
                }
            }
        except Exception as e:
            logger.error(f"Error checking cache health: {e}")
            return {"status": "error", "error": str(e)}

    def check_queue_health(self) -> Dict:
        """Check message queue health"""
        try:
            response = requests.get("http://localhost:8000/api/queue/status")
            queue_info = response.json()
            
            return {
                "status": "pass" if queue_info["queue_size"] < self.thresholds["queue_size"] else "fail",
                "metrics": {
                    "queue_size": queue_info["queue_size"],
                    "processing_rate": queue_info["processing_rate"],
                    "error_rate": queue_info["error_rate"]
                }
            }
        except Exception as e:
            logger.error(f"Error checking queue health: {e}")
            return {"status": "error", "error": str(e)}

    def check_service_dependencies(self) -> Dict:
        """Check external service dependencies"""
        services = [
            "auth_service",
            "payment_service",
            "notification_service",
            "ai_service"
        ]
        
        results = []
        for service in services:
            try:
                start_time = time.time()
                response = requests.get(f"http://localhost:8000/api/services/{service}/health")
                response_time = (time.time() - start_time) * 1000
                
                results.append({
                    "service": service,
                    "status": "pass" if response.status_code == 200 else "fail",
                    "response_time": response_time,
                    "details": response.json() if response.status_code == 200 else None
                })
            except Exception as e:
                logger.error(f"Error checking service {service}: {e}")
                results.append({
                    "service": service,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "status": "pass" if all(r["status"] == "pass" for r in results) else "fail",
            "details": results
        }

    def run_all_checks(self):
        """Run all health checks"""
        start_time = time.time()
        
        # Run system checks
        self.results["checks"]["system"] = self.check_system_resources()
        
        # Run API checks
        self.results["checks"]["api"] = self.check_api_health()
        
        # Run database checks
        self.results["checks"]["database"] = self.check_database_health()
        
        # Run cache checks
        self.results["checks"]["cache"] = self.check_cache_health()
        
        # Run queue checks
        self.results["checks"]["queue"] = self.check_queue_health()
        
        # Run dependency checks
        self.results["checks"]["dependencies"] = self.check_service_dependencies()
        
        self.results["execution_time"] = time.time() - start_time
        
        # Calculate overall status
        failed_checks = [check for check in self.results["checks"].values() 
                        if check["status"] != "pass"]
        self.results["overall_status"] = "fail" if failed_checks else "pass"
        
        # Generate summary
        self.generate_summary()
        
        return self.results

    def generate_summary(self):
        """Generate health check summary"""
        total_checks = len(self.results["checks"])
        passed_checks = sum(1 for check in self.results["checks"].values() 
                          if check["status"] == "pass")
        failed_checks = total_checks - passed_checks
        
        self.results["summary"] = {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "failed_checks": failed_checks,
            "success_rate": (passed_checks / total_checks) * 100 if total_checks > 0 else 0,
            "execution_time": self.results["execution_time"]
        }

    def save_results(self):
        """Save health check results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"health_results/platform_health_{timestamp}.json"
        
        os.makedirs("health_results", exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"Results saved to {results_file}")

    def generate_report(self) -> str:
        """Generate a human-readable health report"""
        report = f"""
Platform Health Report
====================
Generated at: {self.results['timestamp']}
Overall Status: {self.results['overall_status'].upper()}
Total Execution Time: {self.results['execution_time']:.2f} seconds

Summary:
--------
Total Checks: {self.results['summary']['total_checks']}
Passed Checks: {self.results['summary']['passed_checks']}
Failed Checks: {self.results['summary']['failed_checks']}
Success Rate: {self.results['summary']['success_rate']:.2f}%

Detailed Results:
---------------
"""
        
        for check_name, result in self.results["checks"].items():
            report += f"\n{check_name.upper()}:"
            report += f"\n  Status: {result['status'].upper()}"
            
            if result.get("metrics"):
                report += "\n  Metrics:"
                for metric, value in result["metrics"].items():
                    report += f"\n    - {metric}: {value}"
            
            if result.get("details"):
                report += "\n  Details:"
                if isinstance(result["details"], list):
                    for detail in result["details"]:
                        report += f"\n    - {detail}"
                else:
                    report += f"\n    {result['details']}"
            
            if result.get("error"):
                report += f"\n  Error: {result['error']}"
            
            report += "\n"
        
        return report

def main():
    checker = PlatformHealthChecker()
    results = checker.run_all_checks()
    checker.save_results()
    
    # Print report
    print(checker.generate_report())
    
    # Exit with appropriate status code
    sys.exit(0 if results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main() 