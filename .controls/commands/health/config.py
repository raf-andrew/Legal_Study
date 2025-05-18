"""Configuration handler for health checks."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

@dataclass
class HealthCheckConfig:
    """Configuration for a health check."""
    
    enabled: bool = True
    timeout_ms: int = 5000  # 5 seconds
    interval_ms: Optional[int] = None  # None means run on-demand only
    retries: int = 0
    retry_delay_ms: int = 1000  # 1 second
    dependencies: Set[str] = field(default_factory=set)
    parameters: Dict[str, Any] = field(default_factory=dict)

class HealthCheckConfigurationError(Exception):
    """Base class for configuration errors."""
    pass

class HealthCheckConfiguration:
    """Handler for health check configurations."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration handler.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or Path(".controls/commands/health/config.json")
        self._configs: Dict[str, HealthCheckConfig] = {}
        self.logger = logging.getLogger("health.config")
        
        # Load configuration if file exists
        if self.config_path.exists():
            self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file.
        
        Raises:
            HealthCheckConfigurationError: If configuration invalid
        """
        try:
            with open(self.config_path) as f:
                data = json.load(f)
            
            self._configs.clear()
            for check_name, check_config in data.items():
                self._configs[check_name] = HealthCheckConfig(
                    enabled=check_config.get("enabled", True),
                    timeout_ms=check_config.get("timeout_ms", 5000),
                    interval_ms=check_config.get("interval_ms"),
                    retries=check_config.get("retries", 0),
                    retry_delay_ms=check_config.get("retry_delay_ms", 1000),
                    dependencies=set(check_config.get("dependencies", [])),
                    parameters=check_config.get("parameters", {})
                )
            
            self.logger.info(f"Loaded configuration for {len(self._configs)} checks")
        except Exception as e:
            raise HealthCheckConfigurationError(
                f"Failed to load configuration: {str(e)}"
            )
    
    def save_config(self) -> None:
        """Save configuration to file.
        
        Raises:
            HealthCheckConfigurationError: If save fails
        """
        try:
            # Create parent directories if they don't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert configs to dictionary format
            data = {
                name: {
                    "enabled": config.enabled,
                    "timeout_ms": config.timeout_ms,
                    "interval_ms": config.interval_ms,
                    "retries": config.retries,
                    "retry_delay_ms": config.retry_delay_ms,
                    "dependencies": list(config.dependencies),
                    "parameters": config.parameters
                }
                for name, config in self._configs.items()
            }
            
            # Write to file with pretty formatting
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=4)
            
            self.logger.info(f"Saved configuration for {len(self._configs)} checks")
        except Exception as e:
            raise HealthCheckConfigurationError(
                f"Failed to save configuration: {str(e)}"
            )
    
    def get_config(self, check_name: str) -> HealthCheckConfig:
        """Get configuration for a check.
        
        Args:
            check_name: Name of check to get configuration for
            
        Returns:
            Check configuration
        """
        return self._configs.get(
            check_name,
            HealthCheckConfig()  # Return default config if not found
        )
    
    def set_config(
        self,
        check_name: str,
        config: HealthCheckConfig
    ) -> None:
        """Set configuration for a check.
        
        Args:
            check_name: Name of check to set configuration for
            config: Check configuration
        """
        self._configs[check_name] = config
        self.logger.debug(f"Updated configuration for check: {check_name}")
    
    def enable_check(self, check_name: str) -> None:
        """Enable a health check.
        
        Args:
            check_name: Name of check to enable
        """
        config = self.get_config(check_name)
        config.enabled = True
        self.set_config(check_name, config)
        self.logger.info(f"Enabled health check: {check_name}")
    
    def disable_check(self, check_name: str) -> None:
        """Disable a health check.
        
        Args:
            check_name: Name of check to disable
        """
        config = self.get_config(check_name)
        config.enabled = False
        self.set_config(check_name, config)
        self.logger.info(f"Disabled health check: {check_name}")
    
    def set_check_interval(
        self,
        check_name: str,
        interval_ms: Optional[int]
    ) -> None:
        """Set check execution interval.
        
        Args:
            check_name: Name of check to set interval for
            interval_ms: Interval in milliseconds (None for on-demand)
        """
        config = self.get_config(check_name)
        config.interval_ms = interval_ms
        self.set_config(check_name, config)
        self.logger.debug(
            f"Set interval for {check_name}: "
            f"{interval_ms}ms" if interval_ms else "on-demand"
        )
    
    def set_check_timeout(
        self,
        check_name: str,
        timeout_ms: int
    ) -> None:
        """Set check execution timeout.
        
        Args:
            check_name: Name of check to set timeout for
            timeout_ms: Timeout in milliseconds
        """
        config = self.get_config(check_name)
        config.timeout_ms = timeout_ms
        self.set_config(check_name, config)
        self.logger.debug(f"Set timeout for {check_name}: {timeout_ms}ms")
    
    def set_check_retries(
        self,
        check_name: str,
        retries: int,
        retry_delay_ms: Optional[int] = None
    ) -> None:
        """Set check retry configuration.
        
        Args:
            check_name: Name of check to set retries for
            retries: Number of retries
            retry_delay_ms: Optional delay between retries
        """
        config = self.get_config(check_name)
        config.retries = retries
        if retry_delay_ms is not None:
            config.retry_delay_ms = retry_delay_ms
        self.set_config(check_name, config)
        self.logger.debug(
            f"Set retries for {check_name}: {retries} "
            f"(delay: {config.retry_delay_ms}ms)"
        )
    
    def set_check_dependencies(
        self,
        check_name: str,
        dependencies: Set[str]
    ) -> None:
        """Set check dependencies.
        
        Args:
            check_name: Name of check to set dependencies for
            dependencies: Set of dependency check names
        """
        config = self.get_config(check_name)
        config.dependencies = dependencies
        self.set_config(check_name, config)
        self.logger.debug(
            f"Set dependencies for {check_name}: {', '.join(dependencies)}"
        )
    
    def set_check_parameters(
        self,
        check_name: str,
        parameters: Dict[str, Any]
    ) -> None:
        """Set check parameters.
        
        Args:
            check_name: Name of check to set parameters for
            parameters: Check parameters
        """
        config = self.get_config(check_name)
        config.parameters = parameters
        self.set_config(check_name, config)
        self.logger.debug(f"Set parameters for {check_name}")
    
    def list_enabled_checks(self) -> List[str]:
        """List enabled check names.
        
        Returns:
            List of enabled check names
        """
        return [
            name for name, config in self._configs.items()
            if config.enabled
        ]
    
    def list_scheduled_checks(self) -> List[str]:
        """List checks with scheduled execution.
        
        Returns:
            List of check names with intervals set
        """
        return [
            name for name, config in self._configs.items()
            if config.interval_ms is not None
        ] 