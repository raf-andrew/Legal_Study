"""
Configuration loading and validation utilities.
"""
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from ..utils.logging import setup_logger

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Configuration error."""
    pass

def load_config(config_path: str) -> Dict:
    """Load configuration from file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        ConfigError: If configuration is invalid
    """
    try:
        # Load configuration
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Validate configuration
        validate_config(config)

        # Process environment variables
        process_env_vars(config)

        # Set up logging
        setup_logger(
            logger,
            config["monitoring"]["logging"],
            "config_loader"
        )

        logger.info(f"Loaded configuration from {config_path}")
        return config

    except Exception as e:
        raise ConfigError(f"Error loading configuration: {e}")

def validate_config(config: Dict) -> None:
    """Validate configuration.

    Args:
        config: Configuration dictionary

    Raises:
        ConfigError: If configuration is invalid
    """
    try:
        # Check required sections
        required_sections = [
            "core",
            "domains",
            "git",
            "reporting",
            "monitoring",
            "api",
            "soc2"
        ]
        for section in required_sections:
            if section not in config:
                raise ConfigError(f"Missing required section: {section}")

        # Validate core settings
        validate_core_config(config["core"])

        # Validate domains
        validate_domains_config(config["domains"])

        # Validate git integration
        validate_git_config(config["git"])

        # Validate reporting
        validate_reporting_config(config["reporting"])

        # Validate monitoring
        validate_monitoring_config(config["monitoring"])

        # Validate API
        validate_api_config(config["api"])

        # Validate SOC2
        validate_soc2_config(config["soc2"])

    except Exception as e:
        raise ConfigError(f"Configuration validation failed: {e}")

def validate_core_config(config: Dict) -> None:
    """Validate core configuration.

    Args:
        config: Core configuration

    Raises:
        ConfigError: If configuration is invalid
    """
    try:
        # Check required fields
        required_fields = [
            "max_concurrent_files",
            "max_queue_size",
            "cache_ttl_seconds",
            "file_lock_timeout",
            "report_retention_days"
        ]
        for field in required_fields:
            if field not in config:
                raise ConfigError(f"Missing core field: {field}")

        # Validate values
        if config["max_concurrent_files"] < 1:
            raise ConfigError("max_concurrent_files must be positive")
        if config["max_queue_size"] < 1:
            raise ConfigError("max_queue_size must be positive")
        if config["cache_ttl_seconds"] < 0:
            raise ConfigError("cache_ttl_seconds must be non-negative")
        if config["file_lock_timeout"] < 1:
            raise ConfigError("file_lock_timeout must be positive")
        if config["report_retention_days"] < 1:
            raise ConfigError("report_retention_days must be positive")

    except Exception as e:
        raise ConfigError(f"Core configuration validation failed: {e}")

def validate_domains_config(config: Dict) -> None:
    """Validate domains configuration.

    Args:
        config: Domains configuration

    Raises:
        ConfigError: If configuration is invalid
    """
    try:
        # Check required domains
        required_domains = [
            "security",
            "browser",
            "functional",
            "unit",
            "documentation"
        ]
        for domain in required_domains:
            if domain not in config:
                raise ConfigError(f"Missing required domain: {domain}")

        # Validate each domain
        for domain, settings in config.items():
            # Check required fields
            required_fields = [
                "enabled",
                "priority",
                "report_format",
                "thresholds"
            ]
            for field in required_fields:
                if field not in settings:
                    raise ConfigError(
                        f"Missing required field {field} in domain {domain}"
                    )

            # Validate values
            if not isinstance(settings["enabled"], bool):
                raise ConfigError(
                    f"enabled must be boolean in domain {domain}"
                )
            if not isinstance(settings["priority"], int):
                raise ConfigError(
                    f"priority must be integer in domain {domain}"
                )
            if settings["priority"] < 1:
                raise ConfigError(
                    f"priority must be positive in domain {domain}"
                )
            if settings["report_format"] not in ["json", "yaml"]:
                raise ConfigError(
                    f"Invalid report format in domain {domain}"
                )

    except Exception as e:
        raise ConfigError(f"Domains configuration validation failed: {e}")

def validate_git_config(config: Dict) -> None:
    """Validate git configuration.

    Args:
        config: Git configuration

    Raises:
        ConfigError: If configuration is invalid
    """
    try:
        # Check hooks section
        if "hooks" not in config:
            raise ConfigError("Missing hooks section in git config")

        # Validate hooks
        hooks = config["hooks"]
        required_hooks = ["pre_commit", "pre_push"]
        for hook in required_hooks:
            if hook not in hooks:
                raise ConfigError(f"Missing required hook: {hook}")

            # Check hook fields
            required_fields = [
                "enabled",
                "domains",
                "block_on_critical",
                "block_on_high"
            ]
            for field in required_fields:
                if field not in hooks[hook]:
                    raise ConfigError(
                        f"Missing required field {field} in hook {hook}"
                    )

            # Validate values
            if not isinstance(hooks[hook]["enabled"], bool):
                raise ConfigError(f"enabled must be boolean in hook {hook}")
            if not isinstance(hooks[hook]["domains"], list):
                raise ConfigError(f"domains must be list in hook {hook}")
            if not isinstance(hooks[hook]["block_on_critical"], bool):
                raise ConfigError(
                    f"block_on_critical must be boolean in hook {hook}"
                )
            if not isinstance(hooks[hook]["block_on_high"], bool):
                raise ConfigError(
                    f"block_on_high must be boolean in hook {hook}"
                )

    except Exception as e:
        raise ConfigError(f"Git configuration validation failed: {e}")

def validate_reporting_config(config: Dict) -> None:
    """Validate reporting configuration.

    Args:
        config: Reporting configuration

    Raises:
        ConfigError: If configuration is invalid
    """
    try:
        # Check required fields
        required_fields = [
            "base_path",
            "formats",
            "metrics",
            "alerts"
        ]
        for field in required_fields:
            if field not in config:
                raise ConfigError(f"Missing reporting field: {field}")

        # Validate formats
        if not isinstance(config["formats"], list):
            raise ConfigError("formats must be list")
        for fmt in config["formats"]:
            if fmt not in ["json", "html", "pdf"]:
                raise ConfigError(f"Invalid report format: {fmt}")

        # Validate metrics
        metrics = config["metrics"]
        if not isinstance(metrics["enabled"], bool):
            raise ConfigError("metrics.enabled must be boolean")
        if metrics["collection_interval"] < 1:
            raise ConfigError(
                "metrics.collection_interval must be positive"
            )
        if metrics["retention_days"] < 1:
            raise ConfigError("metrics.retention_days must be positive")

        # Validate alerts
        alerts = config["alerts"]
        if not isinstance(alerts["enabled"], bool):
            raise ConfigError("alerts.enabled must be boolean")
        if not isinstance(alerts["channels"], list):
            raise ConfigError("alerts.channels must be list")

    except Exception as e:
        raise ConfigError(f"Reporting configuration validation failed: {e}")

def validate_monitoring_config(config: Dict) -> None:
    """Validate monitoring configuration.

    Args:
        config: Monitoring configuration

    Raises:
        ConfigError: If configuration is invalid
    """
    try:
        # Check required fields
        required_fields = [
            "health_check_interval",
            "metrics_enabled",
            "logging"
        ]
        for field in required_fields:
            if field not in config:
                raise ConfigError(f"Missing monitoring field: {field}")

        # Validate values
        if config["health_check_interval"] < 1:
            raise ConfigError("health_check_interval must be positive")
        if not isinstance(config["metrics_enabled"], bool):
            raise ConfigError("metrics_enabled must be boolean")

        # Validate logging
        logging = config["logging"]
        required_fields = [
            "level",
            "format",
            "file",
            "max_size_mb",
            "backup_count"
        ]
        for field in required_fields:
            if field not in logging:
                raise ConfigError(f"Missing logging field: {field}")

    except Exception as e:
        raise ConfigError(f"Monitoring configuration validation failed: {e}")

def validate_api_config(config: Dict) -> None:
    """Validate API configuration.

    Args:
        config: API configuration

    Raises:
        ConfigError: If configuration is invalid
    """
    try:
        # Check required fields
        required_fields = [
            "enabled",
            "host",
            "port",
            "rate_limit",
            "authentication"
        ]
        for field in required_fields:
            if field not in config:
                raise ConfigError(f"Missing API field: {field}")

        # Validate values
        if not isinstance(config["enabled"], bool):
            raise ConfigError("enabled must be boolean")
        if config["port"] < 1 or config["port"] > 65535:
            raise ConfigError("Invalid port number")

        # Validate rate limit
        rate_limit = config["rate_limit"]
        if rate_limit["requests_per_second"] < 1:
            raise ConfigError("requests_per_second must be positive")
        if rate_limit["burst"] < rate_limit["requests_per_second"]:
            raise ConfigError("burst must be >= requests_per_second")

        # Validate authentication
        auth = config["authentication"]
        if not isinstance(auth["enabled"], bool):
            raise ConfigError("authentication.enabled must be boolean")
        if auth["token_expiry_hours"] < 1:
            raise ConfigError("token_expiry_hours must be positive")

    except Exception as e:
        raise ConfigError(f"API configuration validation failed: {e}")

def validate_soc2_config(config: Dict) -> None:
    """Validate SOC2 configuration.

    Args:
        config: SOC2 configuration

    Raises:
        ConfigError: If configuration is invalid
    """
    try:
        # Check required fields
        required_fields = [
            "enabled",
            "audit_logging",
            "encryption",
            "access_control",
            "monitoring",
            "reporting"
        ]
        for field in required_fields:
            if field not in config:
                raise ConfigError(f"Missing SOC2 field: {field}")

        # Validate values
        if not isinstance(config["enabled"], bool):
            raise ConfigError("enabled must be boolean")
        if not isinstance(config["audit_logging"], bool):
            raise ConfigError("audit_logging must be boolean")

        # Validate encryption
        encryption = config["encryption"]
        if not isinstance(encryption["enabled"], bool):
            raise ConfigError("encryption.enabled must be boolean")
        if encryption["algorithm"] not in ["AES-256"]:
            raise ConfigError("Invalid encryption algorithm")

        # Validate access control
        access = config["access_control"]
        if not isinstance(access["enabled"], bool):
            raise ConfigError("access_control.enabled must be boolean")
        if not isinstance(access["role_based"], bool):
            raise ConfigError("role_based must be boolean")

        # Validate monitoring
        monitoring = config["monitoring"]
        if not isinstance(monitoring["enabled"], bool):
            raise ConfigError("monitoring.enabled must be boolean")
        if monitoring["interval"] < 1:
            raise ConfigError("monitoring interval must be positive")

        # Validate reporting
        reporting = config["reporting"]
        if not isinstance(reporting["enabled"], bool):
            raise ConfigError("reporting.enabled must be boolean")
        if reporting["format"] not in ["pdf"]:
            raise ConfigError("Invalid report format")
        if reporting["schedule"] not in ["daily", "weekly", "monthly"]:
            raise ConfigError("Invalid report schedule")

    except Exception as e:
        raise ConfigError(f"SOC2 configuration validation failed: {e}")

def process_env_vars(config: Dict) -> None:
    """Process environment variables in configuration.

    Args:
        config: Configuration dictionary
    """
    try:
        def process_value(value: Any) -> Any:
            """Process single configuration value."""
            if isinstance(value, str):
                # Check for environment variable
                if value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    if env_var in os.environ:
                        return os.environ[env_var]
                    else:
                        logger.warning(f"Environment variable not found: {env_var}")
                        return value
            elif isinstance(value, dict):
                # Process dictionary
                return {k: process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                # Process list
                return [process_value(v) for v in value]
            return value

        # Process configuration
        for section in config:
            config[section] = process_value(config[section])

    except Exception as e:
        logger.error(f"Error processing environment variables: {e}")
        raise
