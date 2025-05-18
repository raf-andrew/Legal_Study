import os
import sys
import logging
import click
import json
import yaml
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(".logs/console.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

class BaseCommand(ABC):
    """Base class for console commands."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.start_time = None
        self.end_time = None
        self.metrics = {}

    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the command."""
        pass

    def pre_execute(self, *args, **kwargs):
        """Pre-execution hook."""
        self.start_time = datetime.now()
        logger.info(f"Starting command: {self.name}")
        self._record_metric("command_start", self.start_time.isoformat())

    def post_execute(self, result: Dict[str, Any], *args, **kwargs):
        """Post-execution hook."""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        self._record_metric("command_end", self.end_time.isoformat())
        self._record_metric("duration", duration)
        logger.info(f"Completed command: {self.name} in {duration} seconds")
        return result

    def _record_metric(self, name: str, value: Any):
        """Record a metric."""
        self.metrics[name] = value

    def get_metrics(self) -> Dict[str, Any]:
        """Get command metrics."""
        return self.metrics

    def format_output(self, data: Dict[str, Any], format: str = "json") -> str:
        """Format command output."""
        if format == "json":
            return json.dumps(data, indent=2)
        elif format == "yaml":
            return yaml.dump(data)
        else:
            return str(data)

    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle command error."""
        error_data = {
            "error": str(error),
            "type": error.__class__.__name__,
            "timestamp": datetime.now().isoformat()
        }
        logger.error(f"Command error: {error_data}")
        self._record_metric("error", error_data)
        return error_data

class ClickCommand(BaseCommand):
    """Base class for Click commands."""
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
        self.click_command = None

    def create_command(self) -> click.Command:
        """Create Click command."""
        @click.command(name=self.name, help=self.description)
        @click.option("--format", "-f", default="json", type=click.Choice(["json", "yaml", "text"]),
                     help="Output format")
        @click.option("--log-level", "-l", default="INFO",
                     type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
                     help="Logging level")
        @click.option("--config", "-c", type=click.Path(exists=True),
                     help="Configuration file")
        @click.pass_context
        def command(ctx, format: str, log_level: str, config: Optional[str], *args, **kwargs):
            """Command implementation."""
            try:
                # Set logging level
                logging.getLogger().setLevel(log_level)
                
                # Pre-execution
                self.pre_execute(*args, **kwargs)
                
                # Load configuration
                if config:
                    with open(config) as f:
                        kwargs["config"] = yaml.safe_load(f)
                
                # Execute command
                result = self.execute(*args, **kwargs)
                
                # Post-execution
                result = self.post_execute(result, *args, **kwargs)
                
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

class CommandGroup:
    """Command group manager."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.commands: Dict[str, BaseCommand] = {}
        self.click_group = click.Group(name=name, help=description)

    def add_command(self, command: BaseCommand):
        """Add a command to the group."""
        if isinstance(command, ClickCommand):
            click_command = command.create_command()
            self.click_group.add_command(click_command)
        self.commands[command.name] = command

    def get_command(self, name: str) -> Optional[BaseCommand]:
        """Get a command by name."""
        return self.commands.get(name)

    def list_commands(self) -> List[str]:
        """List available commands."""
        return list(self.commands.keys())

    def create_cli(self):
        """Create CLI application."""
        return self.click_group 