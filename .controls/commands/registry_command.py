"""Command line interface for registry service."""

import click
import json
from typing import Dict, Any
from ..mocks.registry_service import MockRegistryService

registry_service = MockRegistryService()

def format_response(response: Dict[str, Any]) -> str:
    """Format response for command line output."""
    return json.dumps(response, indent=2)

@click.group()
def registry():
    """Registry service commands."""
    pass

@registry.command()
def start():
    """Start the registry service."""
    click.echo(format_response(registry_service.start()))

@registry.command()
def stop():
    """Stop the registry service."""
    click.echo(format_response(registry_service.stop()))

@registry.command()
def reset():
    """Reset the registry service."""
    click.echo(format_response(registry_service.reset()))

@registry.command()
@click.argument('config_file', type=click.Path(exists=True))
def apply_config(config_file):
    """Apply configuration from file."""
    with open(config_file) as f:
        config = json.load(f)
    click.echo(format_response(registry_service.apply_config(config)))

@registry.command()
def initialize():
    """Initialize the registry service."""
    click.echo(format_response(registry_service.initialize()))

@registry.command()
def discover():
    """Discover available services."""
    services = registry_service.discover_services()
    click.echo(format_response({"services": services}))

@registry.command()
@click.argument('service_name')
@click.argument('service_info_file', type=click.Path(exists=True))
def register(service_name, service_info_file):
    """Register a service with info from file."""
    with open(service_info_file) as f:
        service_info = json.load(f)
    click.echo(format_response(registry_service.register_service(service_name, service_info)))

@registry.command()
@click.argument('service_name')
def unregister(service_name):
    """Unregister a service."""
    click.echo(format_response(registry_service.unregister_service(service_name)))

@registry.command()
@click.argument('service_name')
@click.argument('check_info_file', type=click.Path(exists=True))
def configure_health(service_name, check_info_file):
    """Configure health check for service."""
    with open(check_info_file) as f:
        check_info = json.load(f)
    click.echo(format_response(registry_service.configure_health_check(service_name, check_info)))

@registry.command()
@click.argument('service_name')
@click.argument('dependencies', nargs=-1)
def resolve_deps(service_name, dependencies):
    """Resolve service dependencies."""
    click.echo(format_response(registry_service.resolve_dependencies(service_name, list(dependencies))))

@registry.command()
@click.argument('service_name')
def get_service(service_name):
    """Get service information."""
    info = registry_service.get_service(service_name)
    if info is None:
        click.echo(format_response({"status": "error", "error": "Service not found"}))
    else:
        click.echo(format_response({"status": "success", "service": info}))

@registry.command()
def list_services():
    """List all registered services."""
    services = registry_service.list_services()
    click.echo(format_response({"services": services}))

@registry.command()
@click.argument('service_name')
def get_health(service_name):
    """Get health check info for service."""
    info = registry_service.get_health_check(service_name)
    if info is None:
        click.echo(format_response({"status": "error", "error": "Health check not found"}))
    else:
        click.echo(format_response({"status": "success", "health_check": info}))

@registry.command()
@click.argument('service_name')
def get_deps(service_name):
    """Get dependencies for service."""
    deps = registry_service.get_dependencies(service_name)
    if deps is None:
        click.echo(format_response({"status": "error", "error": "Dependencies not found"}))
    else:
        click.echo(format_response({"status": "success", "dependencies": deps}))

@registry.command()
@click.option('--enable/--disable', default=True, help="Enable or disable error mode")
@click.option('--message', help="Custom error message")
def error_mode(enable, message):
    """Set error mode for testing."""
    registry_service.set_error_mode(enable, message)
    click.echo(format_response({
        "status": "success",
        "error_mode": "enabled" if enable else "disabled",
        "message": message
    }))

if __name__ == '__main__':
    registry() 