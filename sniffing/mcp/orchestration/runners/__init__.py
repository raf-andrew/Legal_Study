"""
Runner factory for creating test runners.
"""
import logging
from typing import Any, Dict

from ...server.config import ServerConfig
from .base import BaseRunner
from .security import SecurityRunner
from .browser import BrowserRunner
from .functional import FunctionalRunner
from .unit import UnitRunner
from .documentation import DocumentationRunner

logger = logging.getLogger("runner_factory")

def get_runner(domain: str, config: ServerConfig) -> BaseRunner:
    """Get runner for domain.

    Args:
        domain: Domain to get runner for
        config: Server configuration

    Returns:
        Runner instance

    Raises:
        ValueError: If domain not found
    """
    try:
        # Get runner class
        runner_class = _get_runner_class(domain)
        if not runner_class:
            raise ValueError(f"Runner not found for domain: {domain}")

        # Create runner
        return runner_class(config)

    except Exception as e:
        logger.error(f"Error getting runner for {domain}: {e}")
        raise

def _get_runner_class(domain: str) -> Any:
    """Get runner class for domain.

    Args:
        domain: Domain to get runner class for

    Returns:
        Runner class or None if not found
    """
    try:
        runners = {
            "security": SecurityRunner,
            "browser": BrowserRunner,
            "functional": FunctionalRunner,
            "unit": UnitRunner,
            "documentation": DocumentationRunner
        }
        return runners.get(domain)

    except Exception as e:
        logger.error(f"Error getting runner class for {domain}: {e}")
        return None
