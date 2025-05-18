"""Console output formatters."""
import json
import yaml
import click
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

class BaseFormatter:
    """Base class for output formatters."""
    
    def __init__(self):
        self.console = Console()

    def format(self, data: Any) -> str:
        """Format data for output."""
        raise NotImplementedError

    def display(self, data: Any):
        """Display formatted data."""
        self.console.print(self.format(data))

class JsonFormatter(BaseFormatter):
    """JSON output formatter."""
    
    def format(self, data: Any) -> str:
        """Format data as JSON."""
        return json.dumps(data, indent=2, sort_keys=True)

    def display(self, data: Any):
        """Display JSON data with syntax highlighting."""
        syntax = Syntax(self.format(data), "json", theme="monokai")
        self.console.print(syntax)

class YamlFormatter(BaseFormatter):
    """YAML output formatter."""
    
    def format(self, data: Any) -> str:
        """Format data as YAML."""
        return yaml.dump(data, sort_keys=True)

    def display(self, data: Any):
        """Display YAML data with syntax highlighting."""
        syntax = Syntax(self.format(data), "yaml", theme="monokai")
        self.console.print(syntax)

class TableFormatter(BaseFormatter):
    """Table output formatter."""
    
    def format_table(self, data: List[Dict[str, Any]], columns: List[str]) -> Table:
        """Format data as a table."""
        table = Table(show_header=True, header_style="bold magenta")
        
        # Add columns
        for column in columns:
            table.add_column(column.title())
        
        # Add rows
        for row in data:
            table.add_row(*[str(row.get(col, "")) for col in columns])
        
        return table

    def display(self, data: List[Dict[str, Any]], columns: List[str]):
        """Display data as a table."""
        table = self.format_table(data, columns)
        self.console.print(table)

class ProgressFormatter(BaseFormatter):
    """Progress output formatter."""
    
    def create_progress(self) -> Progress:
        """Create a progress bar."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        )

    def display_progress(self, total: int, description: str = "Processing"):
        """Display progress bar."""
        progress = self.create_progress()
        task = progress.add_task(description, total=total)
        return progress, task

class ErrorFormatter(BaseFormatter):
    """Error output formatter."""
    
    def format_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Panel:
        """Format error message."""
        error_text = f"[red bold]Error:[/red bold] {str(error)}\n"
        if context:
            error_text += "\n[yellow]Context:[/yellow]\n"
            error_text += yaml.dump(context, indent=2)
        
        return Panel(
            error_text,
            title="Error Details",
            border_style="red",
            padding=(1, 2)
        )

    def display_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Display error message."""
        panel = self.format_error(error, context)
        self.console.print(panel)

class SuccessFormatter(BaseFormatter):
    """Success output formatter."""
    
    def format_success(self, message: str, details: Optional[Dict[str, Any]] = None) -> Panel:
        """Format success message."""
        success_text = f"[green bold]Success:[/green bold] {message}\n"
        if details:
            success_text += "\n[blue]Details:[/blue]\n"
            success_text += yaml.dump(details, indent=2)
        
        return Panel(
            success_text,
            title="Success",
            border_style="green",
            padding=(1, 2)
        )

    def display_success(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Display success message."""
        panel = self.format_success(message, details)
        self.console.print(panel)

class FormatterFactory:
    """Factory for creating formatters."""
    
    @staticmethod
    def create_formatter(format_type: str) -> BaseFormatter:
        """Create a formatter instance."""
        formatters = {
            "json": JsonFormatter,
            "yaml": YamlFormatter,
            "table": TableFormatter,
            "progress": ProgressFormatter,
            "error": ErrorFormatter,
            "success": SuccessFormatter
        }
        
        formatter_class = formatters.get(format_type.lower())
        if not formatter_class:
            raise ValueError(f"Unknown format type: {format_type}")
        
        return formatter_class()

def format_output(data: Any, format_type: str = "json") -> str:
    """Format output using the specified formatter."""
    formatter = FormatterFactory.create_formatter(format_type)
    return formatter.format(data)

def display_output(data: Any, format_type: str = "json"):
    """Display output using the specified formatter."""
    formatter = FormatterFactory.create_formatter(format_type)
    formatter.display(data) 