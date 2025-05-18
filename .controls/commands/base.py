"""Base command implementation for console commands."""

import abc
import logging
from typing import Any, Dict, List, Optional
import time

class BaseCommand(abc.ABC):
    """Base class for all console commands."""

    def __init__(self, name: str, description: str = ""):
        """Initialize the command.
        
        Args:
            name: The name of the command
            description: A description of what the command does
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"command.{name}")
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    @abc.abstractmethod
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute the command.
        
        Args:
            args: The command arguments
            
        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        pass

    def validate(self, args: Dict[str, Any]) -> bool:
        """Validate the command arguments.
        
        Args:
            args: The command arguments
            
        Returns:
            bool: True if the arguments are valid, False otherwise
        """
        return True

    def get_help(self) -> str:
        """Get the command help text.
        
        Returns:
            str: The help text
        """
        return self.description

    def get_usage(self) -> str:
        """Get the command usage text.
        
        Returns:
            str: The usage text
        """
        return f"{self.name} [options]"

    def get_examples(self) -> List[str]:
        """Get command usage examples.
        
        Returns:
            List[str]: A list of example commands
        """
        return []

    def pre_execute(self) -> None:
        """Called before command execution."""
        self._start_time = time.time()
        self.logger.info(f"Starting command: {self.name}")

    def post_execute(self, exit_code: int) -> None:
        """Called after command execution.
        
        Args:
            exit_code: The command exit code
        """
        self._end_time = time.time()
        duration = self._end_time - self._start_time if self._start_time else 0
        self.logger.info(f"Command {self.name} completed with exit code {exit_code} in {duration:.2f}s")

    @property
    def execution_time(self) -> float:
        """Get the command execution time in seconds.
        
        Returns:
            float: The execution time in seconds
        """
        if self._start_time and self._end_time:
            return self._end_time - self._start_time
        return 0.0 