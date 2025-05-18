"""
MCP configuration management.
"""
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger("mcp_config")

class MCPConfig:
    """Configuration manager for MCP."""

    def __init__(self, config_path: str):
        """Initialize configuration.

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
            "domains",
            "monitoring",
            "logging",
            "model"
        ]

        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")

        self._validate_global_config()
        self._validate_domains_config()
        self._validate_monitoring_config()
        self._validate_logging_config()
        self._validate_model_config()

    def _validate_global_config(self) -> None:
        """Validate global configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = [
            "workspace_path",
            "job_path",
            "isolation_path",
            "analysis_path",
            "fix_path",
            "report_path",
            "parallel_jobs",
            "cache_ttl"
        ]

        for field in required_fields:
            if field not in self.config["global"]:
                raise ValueError(f"Missing required global config field: {field}")

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
            "collection_interval",
            "metrics_path",
            "health_check_interval"
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

    def _validate_model_config(self) -> None:
        """Validate model configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = [
            "name",
            "confidence_threshold",
            "max_sequence_length",
            "batch_size"
        ]

        for field in required_fields:
            if field not in self.config["model"]:
                raise ValueError(f"Missing required model config field: {field}")

    @property
    def global_config(self) -> Dict[str, Any]:
        """Get global configuration.

        Returns:
            Global configuration dictionary
        """
        return self.config["global"]

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

    @property
    def model_config(self) -> Dict[str, Any]:
        """Get model configuration.

        Returns:
            Model configuration dictionary
        """
        return self.config["model"]

    @property
    def workspace_path(self) -> str:
        """Get workspace path.

        Returns:
            Workspace path
        """
        return self.config["global"]["workspace_path"]

    @property
    def job_path(self) -> str:
        """Get job path.

        Returns:
            Job path
        """
        return self.config["global"]["job_path"]

    @property
    def isolation_path(self) -> str:
        """Get isolation path.

        Returns:
            Isolation path
        """
        return self.config["global"]["isolation_path"]

    @property
    def analysis_path(self) -> str:
        """Get analysis path.

        Returns:
            Analysis path
        """
        return self.config["global"]["analysis_path"]

    @property
    def fix_path(self) -> str:
        """Get fix path.

        Returns:
            Fix path
        """
        return self.config["global"]["fix_path"]

    @property
    def report_path(self) -> str:
        """Get report path.

        Returns:
            Report path
        """
        return self.config["global"]["report_path"]

    @property
    def parallel_jobs(self) -> int:
        """Get parallel jobs limit.

        Returns:
            Maximum number of parallel jobs
        """
        return self.config["global"]["parallel_jobs"]

    @property
    def cache_ttl(self) -> int:
        """Get cache TTL.

        Returns:
            Cache TTL in seconds
        """
        return self.config["global"]["cache_ttl"]

    def get_sniffer_config(self, domain: str) -> Dict[str, Any]:
        """Get sniffer configuration.

        Args:
            domain: Domain name

        Returns:
            Sniffer configuration dictionary

        Raises:
            ValueError: If domain not found
        """
        if domain not in self.config["domains"]:
            raise ValueError(f"Domain not found: {domain}")

        return self.config["domains"][domain].get("sniffer", {})

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

        return self.config["domains"][domain].get("analyzer", {})

    def get_fixer_config(self, domain: str) -> Dict[str, Any]:
        """Get fixer configuration.

        Args:
            domain: Domain name

        Returns:
            Fixer configuration dictionary

        Raises:
            ValueError: If domain not found
        """
        if domain not in self.config["domains"]:
            raise ValueError(f"Domain not found: {domain}")

        return self.config["domains"][domain].get("fixer", {})

    def get_reporter_config(self, domain: str) -> Dict[str, Any]:
        """Get reporter configuration.

        Args:
            domain: Domain name

        Returns:
            Reporter configuration dictionary

        Raises:
            ValueError: If domain not found
        """
        if domain not in self.config["domains"]:
            raise ValueError(f"Domain not found: {domain}")

        return self.config["domains"][domain].get("reporter", {})

    def get_metrics_path(self, component: str) -> str:
        """Get metrics path.

        Args:
            component: Component name

        Returns:
            Metrics path
        """
        return str(Path(self.config["monitoring"]["metrics_path"]) / component)

    def get_log_file(self, component: str) -> str:
        """Get log file path.

        Args:
            component: Component name

        Returns:
            Log file path
        """
        return self.config["logging"]["file"].format(name=component)
