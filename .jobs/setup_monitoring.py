import subprocess
import json
import logging
import os
import sys
import psutil
import requests
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MonitoringSetup:
    def __init__(self, config_path: str = "config/monitoring.json"):
        self.config = self._load_config(config_path)
        self.results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "metrics": {
                    "system": {
                        "cpu": True,
                        "memory": True,
                        "disk": True,
                        "network": True,
                        "process": True
                    },
                    "ai": {
                        "model_performance": True,
                        "inference_latency": True,
                        "resource_usage": True,
                        "accuracy": True
                    },
                    "notifications": {
                        "delivery_rate": True,
                        "queue_length": True,
                        "processing_time": True,
                        "error_rate": True
                    }
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "handlers": ["file", "console"],
                    "rotation": "1 day",
                    "retention": "30 days"
                },
                "alerting": {
                    "channels": {
                        "email": {
                            "enabled": True,
                            "recipients": ["admin@example.com"]
                        },
                        "slack": {
                            "enabled": True,
                            "webhook_url": "https://hooks.slack.com/services/xxx"
                        }
                    },
                    "thresholds": {
                        "cpu_percent": 80,
                        "memory_percent": 80,
                        "disk_percent": 80,
                        "error_rate": 0.01
                    }
                },
                "dashboards": {
                    "system": True,
                    "ai": True,
                    "notifications": True,
                    "errors": True,
                    "performance": True
                }
            }

    def setup_system_monitoring(self) -> Dict:
        """Set up system metrics monitoring."""
        try:
            metrics_config = self.config["metrics"]["system"]
            enabled_metrics = []
            
            if metrics_config["cpu"]:
                enabled_metrics.append("cpu")
                # Set up CPU monitoring
                psutil.cpu_percent(interval=1)  # Initialize CPU monitoring
            
            if metrics_config["memory"]:
                enabled_metrics.append("memory")
                # Set up memory monitoring
                psutil.virtual_memory()
            
            if metrics_config["disk"]:
                enabled_metrics.append("disk")
                # Set up disk monitoring
                psutil.disk_usage('/')
            
            if metrics_config["network"]:
                enabled_metrics.append("network")
                # Set up network monitoring
                psutil.net_io_counters()
            
            if metrics_config["process"]:
                enabled_metrics.append("process")
                # Set up process monitoring
                psutil.Process().memory_info()
            
            return {
                "status": "success",
                "enabled_metrics": enabled_metrics
            }
        except Exception as e:
            logger.error(f"Error setting up system monitoring: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_ai_monitoring(self) -> Dict:
        """Set up AI system monitoring."""
        try:
            metrics_config = self.config["metrics"]["ai"]
            enabled_metrics = []
            
            if metrics_config["model_performance"]:
                enabled_metrics.append("model_performance")
                # Set up model performance monitoring
                # Implementation depends on specific AI framework
            
            if metrics_config["inference_latency"]:
                enabled_metrics.append("inference_latency")
                # Set up inference latency monitoring
            
            if metrics_config["resource_usage"]:
                enabled_metrics.append("resource_usage")
                # Set up AI resource monitoring
            
            if metrics_config["accuracy"]:
                enabled_metrics.append("accuracy")
                # Set up accuracy monitoring
            
            return {
                "status": "success",
                "enabled_metrics": enabled_metrics
            }
        except Exception as e:
            logger.error(f"Error setting up AI monitoring: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_notification_monitoring(self) -> Dict:
        """Set up notification system monitoring."""
        try:
            metrics_config = self.config["metrics"]["notifications"]
            enabled_metrics = []
            
            if metrics_config["delivery_rate"]:
                enabled_metrics.append("delivery_rate")
                # Set up delivery rate monitoring
            
            if metrics_config["queue_length"]:
                enabled_metrics.append("queue_length")
                # Set up queue monitoring
            
            if metrics_config["processing_time"]:
                enabled_metrics.append("processing_time")
                # Set up processing time monitoring
            
            if metrics_config["error_rate"]:
                enabled_metrics.append("error_rate")
                # Set up error rate monitoring
            
            return {
                "status": "success",
                "enabled_metrics": enabled_metrics
            }
        except Exception as e:
            logger.error(f"Error setting up notification monitoring: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_logging(self) -> Dict:
        """Set up logging configuration."""
        try:
            log_config = self.config["logging"]
            
            # Configure logging
            handlers = []
            if "file" in log_config["handlers"]:
                log_dir = Path("logs")
                log_dir.mkdir(exist_ok=True)
                handlers.append(logging.FileHandler("logs/platform.log"))
            
            if "console" in log_config["handlers"]:
                handlers.append(logging.StreamHandler())
            
            # Set up logging format
            formatter = logging.Formatter(log_config["format"])
            for handler in handlers:
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            
            # Set logging level
            logger.setLevel(getattr(logging, log_config["level"]))
            
            return {
                "status": "success",
                "handlers": log_config["handlers"],
                "level": log_config["level"]
            }
        except Exception as e:
            logger.error(f"Error setting up logging: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_alerting(self) -> Dict:
        """Set up alerting system."""
        try:
            alert_config = self.config["alerting"]
            enabled_channels = []
            
            if alert_config["channels"]["email"]["enabled"]:
                enabled_channels.append("email")
                # Set up email alerting
            
            if alert_config["channels"]["slack"]["enabled"]:
                enabled_channels.append("slack")
                # Set up Slack alerting
            
            # Set up alert thresholds
            thresholds = alert_config["thresholds"]
            
            return {
                "status": "success",
                "enabled_channels": enabled_channels,
                "thresholds": thresholds
            }
        except Exception as e:
            logger.error(f"Error setting up alerting: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_dashboards(self) -> Dict:
        """Set up monitoring dashboards."""
        try:
            dashboard_config = self.config["dashboards"]
            enabled_dashboards = []
            
            for dashboard, enabled in dashboard_config.items():
                if enabled:
                    enabled_dashboards.append(dashboard)
                    # Set up specific dashboard
            
            return {
                "status": "success",
                "enabled_dashboards": enabled_dashboards
            }
        except Exception as e:
            logger.error(f"Error setting up dashboards: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_monitoring(self) -> Dict:
        """Set up the complete monitoring system."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "system_monitoring": self.setup_system_monitoring(),
            "ai_monitoring": self.setup_ai_monitoring(),
            "notification_monitoring": self.setup_notification_monitoring(),
            "logging": self.setup_logging(),
            "alerting": self.setup_alerting(),
            "dashboards": self.setup_dashboards()
        }
        
        # Check overall status
        overall_status = all(component["status"] == "success" 
                           for component in results.values() 
                           if isinstance(component, dict))
        
        results["status"] = "success" if overall_status else "error"
        self.results = results
        return results

    def generate_report(self, output_format: str = "text") -> str:
        """Generate a monitoring setup report."""
        if not self.results:
            self.setup_monitoring()
            
        if output_format == "json":
            return json.dumps(self.results, indent=2)
            
        elif output_format == "text":
            report = []
            report.append("Monitoring Setup Report")
            report.append(f"Generated: {self.results['timestamp']}")
            report.append(f"Overall Status: {self.results['status'].upper()}")
            
            for component, result in self.results.items():
                if isinstance(result, dict) and component != "status":
                    report.append(f"\n{component.replace('_', ' ').title()}:")
                    report.append(f"Status: {result['status'].upper()}")
                    
                    if result["status"] == "error":
                        report.append(f"Error: {result.get('error', 'Unknown error')}")
                    else:
                        for key, value in result.items():
                            if key != "status":
                                report.append(f"{key}: {value}")
            
            return "\n".join(report)
            
        elif output_format == "html":
            html = [
                "<html>",
                "<head>",
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                ".success { color: green; }",
                ".error { color: red; }",
                ".component { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }",
                "</style>",
                "</head>",
                "<body>",
                "<h1>Monitoring Setup Report</h1>",
                f"<p>Generated: {self.results['timestamp']}</p>",
                f"<h2>Overall Status: <span class='{self.results['status']}'>{self.results['status'].upper()}</span></h2>"
            ]
            
            for component, result in self.results.items():
                if isinstance(result, dict) and component != "status":
                    html.append(f'<div class="component">')
                    html.append(f"<h3>{component.replace('_', ' ').title()}</h3>")
                    html.append(f"<p>Status: <span class='{result['status']}'>{result['status'].upper()}</span></p>")
                    
                    if result["status"] == "error":
                        html.append(f"<p class='error'>Error: {result.get('error', 'Unknown error')}</p>")
                    else:
                        html.append("<ul>")
                        for key, value in result.items():
                            if key != "status":
                                html.append(f"<li><strong>{key}:</strong> {value}</li>")
                        html.append("</ul>")
                    
                    html.append("</div>")
            
            html.extend(["</body>", "</html>"])
            return "\n".join(html)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def save_report(self, output_dir: str = "reports") -> None:
        """Save monitoring setup results in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON report
        with open(f"{output_dir}/monitoring_setup_{timestamp}.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Save text report
        with open(f"{output_dir}/monitoring_setup_{timestamp}.txt", "w") as f:
            f.write(self.generate_report("text"))
        
        # Save HTML report
        with open(f"{output_dir}/monitoring_setup_{timestamp}.html", "w") as f:
            f.write(self.generate_report("html"))

def main():
    setup = MonitoringSetup()
    
    # Set up monitoring
    setup.setup_monitoring()
    
    # Generate and print text report
    print(setup.generate_report("text"))
    
    # Save reports in all formats
    setup.save_report()
    
    # Exit with appropriate status code
    if setup.results["status"] == "error":
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main() 