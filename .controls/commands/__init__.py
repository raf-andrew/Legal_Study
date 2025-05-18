"""Console command initialization."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseCommand(ABC):
    """Base class for all console commands."""
    
    def __init__(self, name: str, description: str):
        """Initialize command.
        
        Args:
            name: Command name
            description: Command description
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the command.
        
        Args:
            **kwargs: Command arguments
            
        Returns:
            Dict containing command execution results
        """
        pass
    
    @abstractmethod
    def validate(self, **kwargs) -> Optional[str]:
        """Validate command arguments.
        
        Args:
            **kwargs: Command arguments
            
        Returns:
            Error message if validation fails, None otherwise
        """
        pass 