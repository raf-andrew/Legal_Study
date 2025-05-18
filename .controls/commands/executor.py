"""Command executor implementation."""

import logging
from typing import Dict, Any, Optional, List

from .base import BaseCommand
from .registry import CommandRegistry

class CommandExecutor:
    """Executor for console commands."""

    def __init__(self, registry: CommandRegistry):
        """Initialize the command executor.
        
        Args:
            registry: The command registry to use
        """
        self.registry = registry
        self.logger = logging.getLogger("command.executor")

    def execute(self, name: str, args: Dict[str, Any]) -> int:
        """Execute a command.
        
        Args:
            name: The name of the command to execute
            args: The command arguments
            
        Returns:
            int: The exit code (0 for success, non-zero for failure)
        """
        command_class = self.registry.get_command(name)
        if not command_class:
            self.logger.error(f"Command not found: {name}")
            return 1

        command = command_class()
        
        try:
            # Validate arguments
            if not command.validate(args):
                self.logger.error(f"Invalid arguments for command: {name}")
                return 1

            # Pre-execute
            command.pre_execute()

            # Execute command
            exit_code = command.execute(args)

            # Post-execute
            command.post_execute(exit_code)

            return exit_code

        except Exception as e:
            self.logger.error(f"Command execution failed: {str(e)}", exc_info=True)
            return 1

    def get_command_help(self, name: str) -> Optional[str]:
        """Get help text for a command.
        
        Args:
            name: The name of the command
            
        Returns:
            The help text if the command exists, None otherwise
        """
        return self.registry.get_command_help(name)

    def get_command_usage(self, name: str) -> Optional[str]:
        """Get usage text for a command.
        
        Args:
            name: The name of the command
            
        Returns:
            The usage text if the command exists, None otherwise
        """
        return self.registry.get_command_usage(name)

    def get_command_examples(self, name: str) -> List[str]:
        """Get examples for a command.
        
        Args:
            name: The name of the command
            
        Returns:
            A list of example commands
        """
        return self.registry.get_command_examples(name) 