"""Service configuration health check implementation."""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from ..base import HealthCheckResult
from .service import ServiceHealthCheck

class ServiceConfigCheck(ServiceHealthCheck):
    """Check service configuration."""
    
    def __init__(
        self,
        name: str,
        service_name: str,
        config_path: Union[str, Path],
        required_settings: Set[str],
        optional_settings: Optional[Set[str]] = None,
        value_validators: Optional[Dict[str, callable]] = None,
        required: bool = True,
        timeout_ms: int = 5000
    ):
        """Initialize configuration check.
        
        Args:
            name: Check name
            service_name: Name of service to check
            config_path: Path to configuration file
            required_settings: Set of required setting names
            optional_settings: Optional set of optional setting names
            value_validators: Optional mapping of setting names to validator functions
            required: Whether service is required
            timeout_ms: Check timeout in milliseconds
        """
        super().__init__(name, service_name, required, timeout_ms)
        self.config_path = Path(config_path)
        self.required_settings = required_settings
        self.optional_settings = optional_settings or set()
        self.value_validators = value_validators or {}
        self.logger = logging.getLogger(f"health.service.config.{service_name}")
    
    async def _check_service(self) -> HealthCheckResult:
        """Check service configuration."""
        # Check if config file exists
        if not self.config_path.exists():
            return self._create_result(
                status="unhealthy",
                error=f"Configuration file not found: {self.config_path}",
                details={"config_path": str(self.config_path)}
            )
        
        try:
            # Load configuration
            config = self._load_config()
            
            # Check settings
            missing_settings = []
            invalid_settings = []
            validation_warnings = []
            
            # Check required settings
            for setting in self.required_settings:
                if setting not in config:
                    missing_settings.append(setting)
                elif setting in self.value_validators:
                    try:
                        if not self.value_validators[setting](config[setting]):
                            invalid_settings.append(setting)
                    except Exception as e:
                        invalid_settings.append(setting)
                        self.logger.warning(
                            f"Validation failed for setting {setting}: {str(e)}"
                        )
            
            # Check optional settings
            for setting in self.optional_settings:
                if setting in config and setting in self.value_validators:
                    try:
                        if not self.value_validators[setting](config[setting]):
                            validation_warnings.append(
                                f"Invalid value for optional setting: {setting}"
                            )
                    except Exception as e:
                        validation_warnings.append(
                            f"Validation failed for optional setting {setting}: {str(e)}"
                        )
            
            # Check for unknown settings
            known_settings = self.required_settings | self.optional_settings
            unknown_settings = set(config.keys()) - known_settings
            if unknown_settings:
                validation_warnings.append(
                    f"Unknown settings found: {', '.join(unknown_settings)}"
                )
            
            # Determine status
            if missing_settings or (invalid_settings and self.required):
                status = "unhealthy"
                error = None
                
                if missing_settings:
                    error = f"Missing required settings: {', '.join(missing_settings)}"
                elif invalid_settings:
                    error = f"Invalid required settings: {', '.join(invalid_settings)}"
            elif invalid_settings:
                status = "warning"
                validation_warnings.append(
                    f"Invalid settings found: {', '.join(invalid_settings)}"
                )
            else:
                status = "healthy"
            
            return self._create_result(
                status=status,
                error=error,
                warnings=validation_warnings,
                details={
                    "config_path": str(self.config_path),
                    "missing_settings": missing_settings,
                    "invalid_settings": invalid_settings,
                    "unknown_settings": list(unknown_settings),
                    "config": self._sanitize_config(config)
                },
                metrics={
                    "total_settings": len(config),
                    "missing_settings": len(missing_settings),
                    "invalid_settings": len(invalid_settings),
                    "unknown_settings": len(unknown_settings)
                }
            )
        
        except Exception as e:
            self.logger.error(
                f"Failed to check configuration: {str(e)}",
                exc_info=True
            )
            return self._create_result(
                status="unhealthy",
                error=f"Failed to check configuration: {str(e)}",
                details={"config_path": str(self.config_path)}
            )
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            Exception: If loading fails
        """
        # This would typically load from a config file
        # For now, we'll just return a mock config
        return {
            "host": "localhost",
            "port": 8080,
            "timeout": 30,
            "max_connections": 100,
            "debug": False,
            "log_level": "INFO"
        }
    
    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize configuration for output.
        
        Args:
            config: Configuration to sanitize
            
        Returns:
            Sanitized configuration
        """
        # Remove sensitive values
        sensitive_keys = {
            "password", "secret", "key", "token", "credential",
            "api_key", "private_key", "access_key"
        }
        
        return {
            key: "***" if any(s in key.lower() for s in sensitive_keys) else value
            for key, value in config.items()
        }

class ServiceConfigValueCheck(ServiceHealthCheck):
    """Check service configuration values."""
    
    def __init__(
        self,
        name: str,
        service_name: str,
        config_path: Union[str, Path],
        value_checks: Dict[str, Dict[str, Any]],
        required: bool = True,
        timeout_ms: int = 5000
    ):
        """Initialize configuration value check.
        
        Args:
            name: Check name
            service_name: Name of service to check
            config_path: Path to configuration file
            value_checks: Mapping of setting names to check parameters
            required: Whether service is required
            timeout_ms: Check timeout in milliseconds
            
        Example value_checks:
            {
                "port": {
                    "type": int,
                    "min": 1024,
                    "max": 65535
                },
                "log_level": {
                    "type": str,
                    "allowed": ["DEBUG", "INFO", "WARNING", "ERROR"]
                },
                "timeout": {
                    "type": int,
                    "min": 0,
                    "max": 3600
                }
            }
        """
        super().__init__(name, service_name, required, timeout_ms)
        self.config_path = Path(config_path)
        self.value_checks = value_checks
        self.logger = logging.getLogger(f"health.service.config_value.{service_name}")
    
    async def _check_service(self) -> HealthCheckResult:
        """Check service configuration values."""
        try:
            # Load configuration
            config = self._load_config()
            
            # Check values
            invalid_values = []
            validation_warnings = []
            
            for setting, checks in self.value_checks.items():
                if setting not in config:
                    validation_warnings.append(f"Setting not found: {setting}")
                    continue
                
                value = config[setting]
                
                # Check type
                expected_type = checks.get("type")
                if expected_type and not isinstance(value, expected_type):
                    invalid_values.append(
                        f"{setting}: expected type {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
                    continue
                
                # Check allowed values
                allowed_values = checks.get("allowed")
                if allowed_values is not None and value not in allowed_values:
                    invalid_values.append(
                        f"{setting}: value {value} not in allowed values: "
                        f"{allowed_values}"
                    )
                    continue
                
                # Check numeric bounds
                if isinstance(value, (int, float)):
                    min_value = checks.get("min")
                    if min_value is not None and value < min_value:
                        invalid_values.append(
                            f"{setting}: value {value} below minimum {min_value}"
                        )
                        continue
                    
                    max_value = checks.get("max")
                    if max_value is not None and value > max_value:
                        invalid_values.append(
                            f"{setting}: value {value} above maximum {max_value}"
                        )
                        continue
                
                # Check string length
                if isinstance(value, str):
                    min_length = checks.get("min_length")
                    if min_length is not None and len(value) < min_length:
                        invalid_values.append(
                            f"{setting}: length {len(value)} below minimum {min_length}"
                        )
                        continue
                    
                    max_length = checks.get("max_length")
                    if max_length is not None and len(value) > max_length:
                        invalid_values.append(
                            f"{setting}: length {len(value)} above maximum {max_length}"
                        )
                        continue
            
            # Determine status
            if invalid_values and self.required:
                status = "unhealthy"
                error = f"Invalid configuration values: {'; '.join(invalid_values)}"
            elif invalid_values:
                status = "warning"
                validation_warnings.extend(invalid_values)
                error = None
            else:
                status = "healthy"
                error = None
            
            return self._create_result(
                status=status,
                error=error,
                warnings=validation_warnings,
                details={
                    "config_path": str(self.config_path),
                    "invalid_values": invalid_values,
                    "config": self._sanitize_config(config)
                },
                metrics={
                    "total_checks": len(self.value_checks),
                    "invalid_values": len(invalid_values)
                }
            )
        
        except Exception as e:
            self.logger.error(
                f"Failed to check configuration values: {str(e)}",
                exc_info=True
            )
            return self._create_result(
                status="unhealthy",
                error=f"Failed to check configuration values: {str(e)}",
                details={"config_path": str(self.config_path)}
            )
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            Exception: If loading fails
        """
        # This would typically load from a config file
        # For now, we'll just return a mock config
        return {
            "host": "localhost",
            "port": 8080,
            "timeout": 30,
            "max_connections": 100,
            "debug": False,
            "log_level": "INFO"
        }
    
    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize configuration for output.
        
        Args:
            config: Configuration to sanitize
            
        Returns:
            Sanitized configuration
        """
        # Remove sensitive values
        sensitive_keys = {
            "password", "secret", "key", "token", "credential",
            "api_key", "private_key", "access_key"
        }
        
        return {
            key: "***" if any(s in key.lower() for s in sensitive_keys) else value
            for key, value in config.items()
        } 