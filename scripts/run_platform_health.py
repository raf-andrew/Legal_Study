#!/usr/bin/env python3
"""
Platform Health Check Script
This script automates the execution of platform health checks and generates reports.
"""

import os
import sys
import json
import logging
import requests
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

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

class PlatformHealthCheck:
    """Platform health check orchestrator."""

    def __init__(self):
        """Initialize the health checker."""
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "issues": []
        }

    def run_all_checks(self) -> bool:
        """Run all health checks."""
        logger.info("Starting platform health checks...")
        
        try:
            # Run core service checks
            self._check_core_services()
            
            # Run AI feature checks
            self._check_ai_features()
            
            # Run notification checks
            self._check_notifications()
            
            # Run error handling checks
            self._check_error_handling()
            
            # Run monitoring checks
            self._check_monitoring()
            
            # Generate reports
            self._generate_reports()
            
            return len(self.results["issues"]) == 0
            
        except Exception as e:
            logger.error(f"Error running health checks: {str(e)}")
            self.results["issues"].append({
                "type": "system_error",
                "message": str(e)
            })
            return False

    def _check_core_services(self):
        """Check core platform services."""
        logger.info("Checking core services...")
        
        # Check API service
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            self.results["checks"]["api_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds(),
                "details": response.json() if response.status_code == 200 else None
            }
        except Exception as e:
            self.results["checks"]["api_service"] = {
                "status": "error",
                "error": str(e)
            }
            self.results["issues"].append({
                "type": "api_service_error",
                "message": f"API service check failed: {str(e)}"
            })

        # Check database
        try:
            import psycopg2
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME", "postgres"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres"),
                host=os.getenv("DB_HOST", "localhost")
            )
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            self.results["checks"]["database"] = {
                "status": "healthy",
                "details": {"connection": "successful"}
            }
            conn.close()
        except Exception as e:
            self.results["checks"]["database"] = {
                "status": "error",
                "error": str(e)
            }
            self.results["issues"].append({
                "type": "database_error",
                "message": f"Database check failed: {str(e)}"
            })

        # Check Redis
        try:
            import redis
            r = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379))
            )
            r.ping()
            self.results["checks"]["redis"] = {
                "status": "healthy",
                "details": {"connection": "successful"}
            }
        except Exception as e:
            self.results["checks"]["redis"] = {
                "status": "error",
                "error": str(e)
            }
            self.results["issues"].append({
                "type": "redis_error",
                "message": f"Redis check failed: {str(e)}"
            })

    def _check_ai_features(self):
        """Check AI feature health."""
        logger.info("Checking AI features...")
        
        try:
            # Check AI service health
            response = requests.get("http://localhost:8000/api/v1/ai/health", timeout=5)
            self.results["checks"]["ai_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
            
            # Test AI model initialization
            response = requests.get("http://localhost:8000/api/v1/ai/models", timeout=5)
            self.results["checks"]["ai_models"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
            
            # Test prompt processing
            test_prompt = {"text": "Test prompt", "model": "default"}
            response = requests.post(
                "http://localhost:8000/api/v1/ai/process",
                json=test_prompt,
                timeout=5
            )
            self.results["checks"]["ai_processing"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
            
        except Exception as e:
            self.results["checks"]["ai_features"] = {
                "status": "error",
                "error": str(e)
            }
            self.results["issues"].append({
                "type": "ai_feature_error",
                "message": f"AI feature check failed: {str(e)}"
            })

    def _check_notifications(self):
        """Check notification system health."""
        logger.info("Checking notification system...")
        
        try:
            # Check notification service health
            response = requests.get("http://localhost:8000/api/v1/notifications/health", timeout=5)
            self.results["checks"]["notification_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
            
            # Test notification sending
            test_notification = {
                "type": "email",
                "recipient": "test@example.com",
                "subject": "Test",
                "body": "Test notification"
            }
            response = requests.post(
                "http://localhost:8000/api/v1/notifications/send",
                json=test_notification,
                timeout=5
            )
            self.results["checks"]["notification_sending"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
            
        except Exception as e:
            self.results["checks"]["notifications"] = {
                "status": "error",
                "error": str(e)
            }
            self.results["issues"].append({
                "type": "notification_error",
                "message": f"Notification check failed: {str(e)}"
            })

    def _check_error_handling(self):
        """Check error handling system health."""
        logger.info("Checking error handling system...")
        
        try:
            # Check error handling service health
            response = requests.get("http://localhost:8000/api/v1/error-handling/health", timeout=5)
            self.results["checks"]["error_handling_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
            
            # Test error logging
            test_error = {
                "level": "error",
                "message": "Test error",
                "context": {"test": True}
            }
            response = requests.post(
                "http://localhost:8000/api/v1/error-handling/log",
                json=test_error,
                timeout=5
            )
            self.results["checks"]["error_logging"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
            
        except Exception as e:
            self.results["checks"]["error_handling"] = {
                "status": "error",
                "error": str(e)
            }
            self.results["issues"].append({
                "type": "error_handling_error",
                "message": f"Error handling check failed: {str(e)}"
            })

    def _check_monitoring(self):
        """Check monitoring system health."""
        logger.info("Checking monitoring system...")
        
        try:
            # Check monitoring service health
            response = requests.get("http://localhost:8000/api/v1/monitoring/health", timeout=5)
            self.results["checks"]["monitoring_service"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
            
            # Check system metrics
            response = requests.get("http://localhost:8000/api/v1/monitoring/system", timeout=5)
            self.results["checks"]["system_metrics"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
            
            # Check application metrics
            response = requests.get("http://localhost:8000/api/v1/monitoring/application", timeout=5)
            self.results["checks"]["application_metrics"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "details": response.json() if response.status_code == 200 else None
            }
            
        except Exception as e:
            self.results["checks"]["monitoring"] = {
                "status": "error",
                "error": str(e)
            }
            self.results["issues"].append({
                "type": "monitoring_error",
                "message": f"Monitoring check failed: {str(e)}"
            })

    def _generate_reports(self):
        """Generate health check reports."""
        logger.info("Generating reports...")
        
        # Save JSON report
        with open("reports/platform_health.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Generate HTML report
        self._generate_html_report()
        
        # Generate summary
        self._generate_summary()

    def _generate_html_report(self):
        """Generate HTML report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Platform Health Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .check {{ margin: 10px 0; padding: 10px; border-radius: 3px; }}
                .healthy {{ background-color: #dff0d8; }}
                .unhealthy {{ background-color: #f2dede; }}
                .error {{ background-color: #fcf8e3; }}
                .timestamp {{ color: #666; }}
            </style>
        </head>
        <body>
            <h1>Platform Health Report</h1>
            <p class="timestamp">Generated at: {self.results['timestamp']}</p>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Total Issues: {len(self.results['issues'])}</p>
                <p>Status: {'Healthy' if len(self.results['issues']) == 0 else 'Unhealthy'}</p>
            </div>

            <h2>Health Checks</h2>
        """
        
        for check, result in self.results["checks"].items():
            status = result["status"]
            html += f"""
            <div class="check {status}">
                <h3>{check}</h3>
                <p>Status: {status.title()}</p>
                <pre>{json.dumps(result.get('details', {}), indent=2)}</pre>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        with open("reports/platform_health.html", "w") as f:
            f.write(html)

    def _generate_summary(self):
        """Generate summary report."""
        summary = f"""
        Platform Health Summary
        Generated at: {self.results['timestamp']}
        
        Status: {'Healthy' if len(self.results['issues']) == 0 else 'Unhealthy'}
        Total Issues: {len(self.results['issues'])}
        
        Issues:
        """
        
        for issue in self.results["issues"]:
            summary += f"\n- {issue['type']}: {issue['message']}"
        
        with open("reports/platform_health_summary.txt", "w") as f:
            f.write(summary)

def main():
    """Main entry point."""
    health_checker = PlatformHealthCheck()
    success = health_checker.run_all_checks()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 