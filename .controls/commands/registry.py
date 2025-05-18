"""Command registry implementation."""

import logging
from typing import Dict, List, Optional, Type

from .base import BaseCommand

class CommandRegistry:
    """Registry for managing console commands."""

    def __init__(self):
        """Initialize the command registry."""
        self._commands: Dict[str, Type[BaseCommand]] = {}
        self.logger = logging.getLogger("command.registry")

    def register(self, command: Type[BaseCommand]) -> None:
        """Register a command.
        
        Args:
            command: The command class to register
        """
        name = command.__name__.lower()
        if name in self._commands:
            self.logger.warning(f"Command {name} already registered, overwriting")
        self._commands[name] = command
        self.logger.info(f"Registered command: {name}")

    def get_command(self, name: str) -> Optional[Type[BaseCommand]]:
        """Get a command by name.
        
        Args:
            name: The name of the command
            
        Returns:
            The command class if found, None otherwise
        """
        return self._commands.get(name.lower())

    def list_commands(self) -> List[str]:
        """List all registered commands.
        
        Returns:
            A list of command names
        """
        return list(self._commands.keys())

    def unregister(self, name: str) -> bool:
        """Unregister a command.
        
        Args:
            name: The name of the command to unregister
            
        Returns:
            True if the command was unregistered, False otherwise
        """
        if name.lower() in self._commands:
            del self._commands[name.lower()]
            self.logger.info(f"Unregistered command: {name}")
            return True
        return False

    def get_command_help(self, name: str) -> Optional[str]:
        """Get help text for a command.
        
        Args:
            name: The name of the command
            
        Returns:
            The help text if the command exists, None otherwise
        """
        command = self.get_command(name)
        if command:
            return command().get_help()
        return None

    def get_command_usage(self, name: str) -> Optional[str]:
        """Get usage text for a command.
        
        Args:
            name: The name of the command
            
        Returns:
            The usage text if the command exists, None otherwise
        """
        command = self.get_command(name)
        if command:
            return command().get_usage()
        return None

    def get_command_examples(self, name: str) -> List[str]:
        """Get examples for a command.
        
        Args:
            name: The name of the command
            
        Returns:
            A list of example commands
        """
        command = self.get_command(name)
        if command:
            return command().get_examples()
        return [] 