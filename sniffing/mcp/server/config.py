"""
Server configuration management for MCP server.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger("server_config")

class ServerConfig:
    """Configuration manager for MCP server."""

    def __init__(self, config_path: str):
        """Initialize server configuration.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file not found
            yaml.YAMLError: If config file is invalid
        """
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")

            with open(self.config_path) as f:
                return yaml.safe_load(f)

        except yaml.YAMLError as e:
            logger.error(f"Error parsing config file: {e}")
            raise

        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise

    def _validate_config(self) -> None:
        """Validate configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        required_sections = [
            "global",
            "mcp",
            "domains",
            "monitoring",
            "logging"
        ]

        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")

        self._validate_global_config()
        self._validate_mcp_config()
        self._validate_domains_config()
        self._validate_monitoring_config()
        self._validate_logging_config()

    def _validate_global_config(self) -> None:
        """Validate global configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = [
            "workspace_path",
            "report_path",
            "cache_ttl",
            "parallel_jobs"
        ]

        for field in required_fields:
            if field not in self.config["global"]:
                raise ValueError(f"Missing required global config field: {field}")

    def _validate_mcp_config(self) -> None:
        """Validate MCP configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = [
            "host",
            "port",
            "api_version",
            "workers",
            "timeout"
        ]

        for field in required_fields:
            if field not in self.config["mcp"]:
                raise ValueError(f"Missing required MCP config field: {field}")

    def _validate_domains_config(self) -> None:
        """Validate domains configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        required_domains = [
            "security",
            "browser",
            "functional",
            "unit",
            "documentation"
        ]

        for domain in required_domains:
            if domain not in self.config["domains"]:
                raise ValueError(f"Missing required domain: {domain}")

            if not self.config["domains"][domain].get("enabled", False):
                logger.warning(f"Domain {domain} is disabled")

    def _validate_monitoring_config(self) -> None:
        """Validate monitoring configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = [
            "enabled",
            "prometheus_port",
            "metrics_path",
            "collection_interval"
        ]

        for field in required_fields:
            if field not in self.config["monitoring"]:
                raise ValueError(f"Missing required monitoring config field: {field}")

    def _validate_logging_config(self) -> None:
        """Validate logging configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = [
            "level",
            "format",
            "file"
        ]

        for field in required_fields:
            if field not in self.config["logging"]:
                raise ValueError(f"Missing required logging config field: {field}")

    @property
    def global_config(self) -> Dict[str, Any]:
        """Get global configuration.

        Returns:
            Global configuration dictionary
        """
        return self.config["global"]

    @property
    def mcp_config(self) -> Dict[str, Any]:
        """Get MCP configuration.

        Returns:
            MCP configuration dictionary
        """
        return self.config["mcp"]

    @property
    def domains(self) -> List[str]:
        """Get enabled domains.

        Returns:
            List of enabled domain names
        """
        return [
            domain
            for domain, config in self.config["domains"].items()
            if config.get("enabled", False)
        ]

    def get_domain_config(self, domain: str) -> Dict[str, Any]:
        """Get domain configuration.

        Args:
            domain: Domain name

        Returns:
            Domain configuration dictionary

        Raises:
            ValueError: If domain not found
        """
        if domain not in self.config["domains"]:
            raise ValueError(f"Domain not found: {domain}")

        return self.config["domains"][domain]

    @property
    def monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration.

        Returns:
            Monitoring configuration dictionary
        """
        return self.config["monitoring"]

    @property
    def logging_config(self) -> Dict[str, Any]:
        """Get logging configuration.

        Returns:
            Logging configuration dictionary
        """
        return self.config["logging"]

    def get_queue_config(self, queue_type: str) -> Dict[str, Any]:
        """Get queue configuration.

        Args:
            queue_type: Type of queue

        Returns:
            Queue configuration dictionary

        Raises:
            ValueError: If queue type not found
        """
        if queue_type not in self.config["mcp"]["queues"]:
            raise ValueError(f"Queue type not found: {queue_type}")

        return self.config["mcp"]["queues"][queue_type]

    def get_runner_config(self, domain: str) -> Dict[str, Any]:
        """Get runner configuration.

        Args:
            domain: Domain name

        Returns:
            Runner configuration dictionary

        Raises:
            ValueError: If domain not found
        """
        if domain not in self.config["domains"]:
            raise ValueError(f"Domain not found: {domain}")

        return self.config["domains"][domain]["runner"]

    def get_analyzer_config(self, domain: str) -> Dict[str, Any]:
        """Get analyzer configuration.

        Args:
            domain: Domain name

        Returns:
            Analyzer configuration dictionary

        Raises:
            ValueError: If domain not found
        """
        if domain not in self.config["domains"]:
            raise ValueError(f"Domain not found: {domain}")

        return self.config["domains"][domain]["analyzer"]

    def get_result_config(self, domain: str) -> Dict[str, Any]:
        """Get result configuration.

        Args:
            domain: Domain name

        Returns:
            Result configuration dictionary

        Raises:
            ValueError: If domain not found
        """
        if domain not in self.config["domains"]:
            raise ValueError(f"Domain not found: {domain}")

        return self.config["domains"][domain]["results"]
