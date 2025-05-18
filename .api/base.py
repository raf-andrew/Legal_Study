"""
Base API Interface and Class

This module provides the base interface and class for all APIs in the system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from fastapi import FastAPI
from pydantic import BaseModel

class APIInterface(ABC):
    """Base interface for all APIs."""
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize the API."""
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the API."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the API."""
        pass
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate input data."""
        pass

class BaseAPI(APIInterface):
    """Base class for all APIs."""
    
    def __init__(self, app: FastAPI, name: str, version: str):
        self.app = app
        self.name = name
        self.version = version
        self.initialized = False
    
    def initialize(self) -> None:
        """Initialize the API."""
        if not self.initialized:
            self._setup_routes()
            self.initialized = True
    
    def shutdown(self) -> None:
        """Shutdown the API."""
        self.initialized = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the API."""
        return {
            "name": self.name,
            "version": self.version,
            "initialized": self.initialized
        }
    
    def validate(self, data: Any) -> bool:
        """Validate input data."""
        return True
    
    @abstractmethod
    def _setup_routes(self) -> None:
        """Setup API routes."""
        pass

class APIResponse(BaseModel):
    """Base response model for all APIs."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None 