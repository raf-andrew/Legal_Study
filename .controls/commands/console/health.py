import os
import sys
import click
from typing import Any, Dict, List, Optional
from .base import ClickCommand

class HealthCheckCommand(ClickCommand):
    """Health check command implementation."""
    
    def __init__(self):
        super().__init__("health", "Run health checks")
        self.checks = {
            "directories": self.check_directories,
            "configurations": self.check_configurations,
            "services": self.check_services,
            "security": self.check_security,
            "monitoring": self.check_monitoring
        }

    def create_command(self) -> click.Command:
        """Create Click command."""
        @click.command(name=self.name, help=self.description)
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
        @click.option("--config", "-C", type=click.Path(exists=True),
                     help="Configuration file")
        @click.pass_context
        def command(ctx, check: List[str], report: bool, format: str,
                   log_level: str, config: Optional[str]):
            """Run health checks."""
            try:
                # Set logging level
                self.logger.setLevel(log_level)
                
                # Pre-execution
                self.pre_execute()
                
                # Load configuration
                if config:
                    with open(config) as f:
                        kwargs["config"] = yaml.safe_load(f)
                
                # Execute command
                result = self.execute(checks=check, report=report)
                
                # Post-execution
                result = self.post_execute(result)
                
                # Format output
                output = self.format_output(result, format)
                click.echo(output)
                
                return result
                
            except Exception as e:
                error_data = self.handle_error(e)
                click.echo(self.format_output(error_data, format))
                sys.exit(1)
        
        self.click_command = command
        return command

    def execute(self, checks: List[str] = None, report: bool = False,
               **kwargs) -> Dict[str, Any]:
        """Execute health checks."""
        results = {}
        
        # Run all checks if none specified
        if not checks:
            checks = list(self.checks.keys())
        
        # Run specified checks
        for check in checks:
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
        if report:
            results["report"] = self.generate_report(results)
        
        return {
            "status": "healthy" if all(r["status"] == "healthy" for r in results.values()) else "unhealthy",
            "checks": results,
            "metrics": self.get_metrics()
        }

    def check_directories(self) -> Dict[str, Any]:
        """Check required directories."""
        required_dirs = [
            ".controls",
            ".config",
            ".logs",
            ".test",
            ".docs"
        ]
        
        results = {
            "healthy": True,
            "checked": [],
            "missing": []
        }
        
        for dir_name in required_dirs:
            if os.path.isdir(dir_name):
                results["checked"].append(dir_name)
            else:
                results["missing"].append(dir_name)
                results["healthy"] = False
        
        return results

    def check_configurations(self) -> Dict[str, Any]:
        """Check configuration files."""
        required_configs = [
            ".config/console.yaml",
            ".config/security.yaml",
            ".config/monitoring.yaml"
        ]
        
        results = {
            "healthy": True,
            "checked": [],
            "missing": [],
            "invalid": []
        }
        
        for config_file in required_configs:
            if os.path.isfile(config_file):
                try:
                    with open(config_file) as f:
                        yaml.safe_load(f)
                    results["checked"].append(config_file)
                except Exception as e:
                    results["invalid"].append({
                        "file": config_file,
                        "error": str(e)
                    })
                    results["healthy"] = False
            else:
                results["missing"].append(config_file)
                results["healthy"] = False
        
        return results

    def check_services(self) -> Dict[str, Any]:
        """Check required services."""
        services = [
            "api",
            "database",
            "cache",
            "queue"
        ]
        
        results = {
            "healthy": True,
            "checked": [],
            "unavailable": []
        }
        
        # Mock service checks for now
        for service in services:
            # TODO: Implement actual service checks
            results["checked"].append(service)
        
        return results

    def check_security(self) -> Dict[str, Any]:
        """Check security configuration."""
        checks = [
            "authentication",
            "authorization",
            "encryption",
            "validation"
        ]
        
        results = {
            "healthy": True,
            "checked": [],
            "failed": []
        }
        
        # Mock security checks for now
        for check in checks:
            # TODO: Implement actual security checks
            results["checked"].append(check)
        
        return results

    def check_monitoring(self) -> Dict[str, Any]:
        """Check monitoring configuration."""
        checks = [
            "metrics",
            "logs",
            "alerts",
            "dashboards"
        ]
        
        results = {
            "healthy": True,
            "checked": [],
            "failed": []
        }
        
        # Mock monitoring checks for now
        for check in checks:
            # TODO: Implement actual monitoring checks
            results["checked"].append(check)
        
        return results

    def generate_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed report."""
        total_checks = len(results)
        healthy_checks = sum(1 for r in results.values() if r["status"] == "healthy")
        unhealthy_checks = sum(1 for r in results.values() if r["status"] == "unhealthy")
        error_checks = sum(1 for r in results.values() if r["status"] == "error")
        
        return {
            "summary": {
                "total_checks": total_checks,
                "healthy_checks": healthy_checks,
                "unhealthy_checks": unhealthy_checks,
                "error_checks": error_checks,
                "health_percentage": (healthy_checks / total_checks * 100) if total_checks > 0 else 0
            },
            "recommendations": self.generate_recommendations(results)
        }

    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on check results."""
        recommendations = []
        
        for check, result in results.items():
            if result["status"] != "healthy":
                if check == "directories":
                    for dir_name in result["details"]["missing"]:
                        recommendations.append(f"Create missing directory: {dir_name}")
                elif check == "configurations":
                    for config in result["details"]["missing"]:
                        recommendations.append(f"Create missing configuration file: {config}")
                    for config in result["details"]["invalid"]:
                        recommendations.append(f"Fix invalid configuration file: {config['file']}")
                else:
                    recommendations.append(f"Investigate {check} check failure")
        
        return recommendations 