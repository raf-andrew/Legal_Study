#!/usr/bin/env python3
"""
CLI module for the Health Check command.
"""

import os
import sys
import logging
import click
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from .check import HealthCheck

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/health_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Health Check command for Legal Study System."""
    pass

@cli.command()
@click.option('--check', '-c', multiple=True, help='Specific checks to run')
@click.option('--report', '-r', is_flag=True, help='Generate detailed report')
@click.option('--log-level', '-l', default='INFO', help='Logging level')
@click.option('--config', '-f', help='Configuration file')
@click.option('--output', '-o', default='json', help='Output format')
def check(check: List[str], report: bool, log_level: str, config: Optional[str], output: str):
    """Run health checks."""
    try:
        # Set log level
        logging.getLogger().setLevel(log_level)
        
        # Initialize health check
        health_check = HealthCheck()
        
        # Load configuration if specified
        if config:
            health_check.load_config(config)
            
        # Run checks
        if check:
            for check_name in check:
                if check_name == 'directory':
                    health_check._check_directory_structure()
                elif check_name == 'configuration':
                    health_check._check_configuration()
                elif check_name == 'services':
                    health_check._check_services()
                elif check_name == 'security':
                    health_check._check_security()
                elif check_name == 'monitoring':
                    health_check._check_monitoring()
                else:
                    logger.warning(f"Unknown check: {check_name}")
        else:
            health_check.check_system_health()
            
        # Generate report if requested
        if report:
            report_data = health_check.generate_report()
            if output == 'json':
                print(report_data)
            elif output == 'yaml':
                import yaml
                print(yaml.dump(report_data))
            elif output == 'text':
                print(f"Health Check Report")
                print(f"==================")
                print(f"Timestamp: {report_data['timestamp']}")
                print(f"\nChecks:")
                for check_name, status in report_data['checks'].items():
                    print(f"- {check_name}: {status}")
                print(f"\nStatus: {report_data['status']}")
                if report_data['errors']:
                    print(f"\nErrors:")
                    for error in report_data['errors']:
                        print(f"- {error}")
                else:
                    print(f"\nErrors: none")
            else:
                logger.error(f"Unknown output format: {output}")
                sys.exit(1)
                
        # Exit with appropriate status code
        if health_check.results['status'] == 'healthy':
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        sys.exit(1)

@cli.command()
@click.option('--version', '-v', is_flag=True, help='Show version')
def version(version: bool):
    """Show version information."""
    if version:
        print("Health Check Command v1.0.0")
        sys.exit(0)

def main():
    """Main entry point for the CLI."""
    cli()

if __name__ == '__main__':
    main() 