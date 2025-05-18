"""Health check command implementation."""
import logging
import click
from typing import Any, Dict, List, Optional
from datetime import datetime
from ...mocks.registry import MockServiceRegistry

logger = logging.getLogger(__name__)

class HealthCheckCommand:
    """Health check command implementation."""
    
    def __init__(self):
        self.registry = MockServiceRegistry()
        self.checks = {
            "services": self.check_services,
            "metrics": self.check_metrics,
            "logs": self.check_logs,
            "errors": self.check_errors
        }

    def create_command(self) -> click.Command:
        """Create Click command."""
        @click.command(name="health", help="Run health checks")
        @click.option("--check", "-c", multiple=True,
                     type=click.Choice(list(self.checks.keys())),
                     help="Specific checks to run")
        @click.option("--report", "-r", is_flag=True,
                     help="Generate detailed report")
        @click.option("--format", "-f", default="json",
                     type=click.Choice(["json", "yaml", "text"]),
                     help="Output format")
        @click.option("--log-level", "-l", default="INFO",
                     type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
                     help="Logging level")
        @click.pass_context
        def command(ctx, check: List[str], report: bool, format: str,
                   log_level: str):
            """Run health checks."""
            try:
                # Set logging level
                logging.getLogger().setLevel(log_level)
                
                # Execute command
                result = self.execute(checks=check, report=report)
                
                # Format output
                formatter = self.registry.get_service("formatters")
                if not formatter:
                    formatter = self.registry.create_service("formatters")
                    formatter.start()
                
                output = formatter.format_output(result, format)
                click.echo(output)
                
                # Exit with status
                ctx.exit(0 if result["status"] == "healthy" else 1)
                
            except Exception as e:
                logger.error(f"Error running health checks: {e}")
                ctx.exit(2)
        
        return command

    def execute(self, checks: Optional[List[str]] = None,
                report: bool = False) -> Dict[str, Any]:
        """Execute health checks."""
        try:
            # Create and start services if needed
            self.registry.create_all_services()
            self.registry.start_all()
            
            # Run checks
            results = {}
            check_list = checks if checks else list(self.checks.keys())
            
            for check in check_list:
                check_func = self.checks.get(check)
                if check_func:
                    try:
                        result = check_func()
                        results[check] = {
                            "status": "healthy" if result["healthy"] else "unhealthy",
                            "details": result
                        }
                    except Exception as e:
                        results[check] = {
                            "status": "error",
                            "error": str(e)
                        }
            
            # Generate report
            status = all(r["status"] == "healthy" for r in results.values())
            response = {
                "status": "healthy" if status else "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "checks": results
            }
            
            if report:
                response["report"] = self.generate_report(results)
            
            return response
            
        except Exception as e:
            logger.error(f"Error executing health checks: {e}")
            return {
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    def check_services(self) -> Dict[str, Any]:
        """Check service health."""
        results = {
            "healthy": True,
            "services": {}
        }
        
        for service_name in self.registry.list_services():
            service = self.registry.get_service(service_name)
            if not service:
                continue
            
            try:
                metrics = service.get_metrics()
                errors = service.get_errors()
                
                service_status = {
                    "status": "healthy",
                    "started_at": metrics.get("started_at"),
                    "total_calls": metrics.get("total_calls", 0),
                    "total_errors": metrics.get("total_errors", 0)
                }
                
                if errors:
                    service_status["status"] = "unhealthy"
                    service_status["errors"] = errors
                    results["healthy"] = False
                
                results["services"][service_name] = service_status
                
            except Exception as e:
                results["services"][service_name] = {
                    "status": "error",
                    "error": str(e)
                }
                results["healthy"] = False
        
        return results

    def check_metrics(self) -> Dict[str, Any]:
        """Check metrics collection."""
        metrics_service = self.registry.get_service("metrics")
        if not metrics_service:
            return {
                "healthy": False,
                "error": "Metrics service not available"
            }
        
        try:
            metrics = metrics_service.collect()
            return {
                "healthy": True,
                "metrics": metrics
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def check_logs(self) -> Dict[str, Any]:
        """Check logging system."""
        logging_service = self.registry.get_service("logging")
        if not logging_service:
            return {
                "healthy": False,
                "error": "Logging service not available"
            }
        
        try:
            # Test logging
            logging_service.log("INFO", "Health check test message")
            
            # Get handlers
            handlers = logging_service.list_handlers()
            handler_stats = {}
            
            for handler in handlers:
                records = logging_service.get_records(handler)
                handler_stats[handler] = {
                    "total_records": len(records),
                    "last_record": records[-1] if records else None
                }
            
            return {
                "healthy": True,
                "handlers": handler_stats
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    def check_errors(self) -> Dict[str, Any]:
        """Check for service errors."""
        results = {
            "healthy": True,
            "errors": {}
        }
        
        all_errors = self.registry.get_all_errors()
        for service_name, errors in all_errors.items():
            if errors:
                results["errors"][service_name] = errors
                results["healthy"] = False
        
        return results

    def generate_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed report."""
        total_checks = len(results)
        healthy_checks = sum(1 for r in results.values() if r["status"] == "healthy")
        unhealthy_checks = sum(1 for r in results.values() if r["status"] == "unhealthy")
        error_checks = sum(1 for r in results.values() if r["status"] == "error")
        
        recommendations = []
        for check, result in results.items():
            if result["status"] != "healthy":
                if "error" in result:
                    recommendations.append(f"Fix error in {check} check: {result['error']}")
                elif "details" in result:
                    details = result["details"]
                    if check == "services":
                        for service, status in details["services"].items():
                            if status["status"] != "healthy":
                                recommendations.append(f"Check service {service}: {status.get('error', 'unhealthy')}")
                    elif check == "metrics":
                        recommendations.append("Fix metrics collection system")
                    elif check == "logs":
                        recommendations.append("Fix logging system")
                    elif check == "errors":
                        for service, errors in details["errors"].items():
                            recommendations.append(f"Fix errors in service {service}")
        
        return {
            "summary": {
                "total_checks": total_checks,
                "healthy_checks": healthy_checks,
                "unhealthy_checks": unhealthy_checks,
                "error_checks": error_checks,
                "health_percentage": (healthy_checks / total_checks * 100) if total_checks > 0 else 0
            },
            "recommendations": recommendations
        } 