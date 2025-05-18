"""
Main setup script for sniffing infrastructure.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from setup_ai import main as setup_ai
from setup_api import main as setup_api
from setup_database import main as setup_database
from setup_hooks import main as setup_hooks
from setup_monitoring import main as setup_monitoring

logger = logging.getLogger("setup")

def main() -> int:
    """Main entry point for setup."""
    try:
        # Set up logging
        setup_logging()

        # Load configuration
        config = load_config()
        if not config:
            logger.error("Failed to load configuration")
            return 1

        # Create directories
        if not create_directories():
            logger.error("Failed to create directories")
            return 1

        # Run setup components
        components = [
            ("database", setup_database),
            ("api", setup_api),
            ("monitoring", setup_monitoring),
            ("ai", setup_ai),
            ("hooks", setup_hooks)
        ]

        for name, setup_func in components:
            logger.info(f"Setting up {name}...")
            if setup_func() != 0:
                logger.error(f"Failed to set up {name}")
                return 1
            logger.info(f"{name} set up successfully")

        # Verify setup
        if not verify_setup():
            logger.error("Setup verification failed")
            return 1

        logger.info("Setup completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Error during setup: {e}")
        return 1

def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def load_config() -> Optional[Dict[str, Any]]:
    """Load sniffing configuration."""
    try:
        config_path = Path("sniffing/config/sniffing_config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return None

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return config

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def create_directories() -> bool:
    """Create required directories."""
    try:
        directories = [
            "sniffing/api",
            "sniffing/core",
            "sniffing/domains",
            "sniffing/git",
            "sniffing/mcp",
            "sniffing/monitoring",
            "database/migrations",
            "models",
            "metrics",
            "alerts",
            "health",
            "reports",
            "logs"
        ]

        for directory in directories:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")

        return True

    except Exception as e:
        logger.error(f"Error creating directories: {e}")
        return False

def verify_setup() -> bool:
    """Verify complete setup."""
    try:
        # Check directories
        directories = [
            "sniffing/api",
            "sniffing/core",
            "sniffing/domains",
            "sniffing/git",
            "sniffing/mcp",
            "sniffing/monitoring",
            "database/migrations",
            "models",
            "metrics",
            "alerts",
            "health",
            "reports",
            "logs"
        ]

        for directory in directories:
            path = Path(directory)
            if not path.exists():
                logger.error(f"Directory not found: {directory}")
                return False

        # Check configuration files
        config_files = [
            "sniffing/config/sniffing_config.yaml",
            "api/config.yml",
            "monitoring/prometheus/prometheus.yml",
            "monitoring/alerts/slack.yml",
            "monitoring/alerts/email.yml",
            "models/code_analysis/config.yml",
            "models/vulnerability_detection/config.yml",
            "models/documentation_generation/config.yml",
            "models/test_generation/config.yml",
            "models/code_review/config.yml"
        ]

        for config_file in config_files:
            path = Path(config_file)
            if not path.exists():
                logger.error(f"Configuration file not found: {config_file}")
                return False

        # Check Git hooks
        hooks = [
            ".git/hooks/pre-commit",
            ".git/hooks/pre-push"
        ]

        for hook in hooks:
            path = Path(hook)
            if not path.exists():
                logger.error(f"Git hook not found: {hook}")
                return False
            if not os.access(path, os.X_OK):
                logger.error(f"Git hook not executable: {hook}")
                return False

        # Check model files
        model_files = [
            "models/model/pytorch_model.bin",
            "models/tokenizer/vocab.json"
        ]

        for model_file in model_files:
            path = Path(model_file)
            if not path.exists():
                logger.error(f"Model file not found: {model_file}")
                return False

        # Check database migration
        migration_file = Path("database/migrations/001_initial.sql")
        if not migration_file.exists():
            logger.error("Initial database migration not found")
            return False

        logger.info("Setup verification passed")
        return True

    except Exception as e:
        logger.error(f"Error verifying setup: {e}")
        return False

def cleanup_old_files() -> bool:
    """Clean up old files."""
    try:
        # Clean up old configuration files
        old_files = [
            "api/config.yml.old",
            "monitoring/prometheus/prometheus.yml.old",
            "monitoring/alerts/slack.yml.old",
            "monitoring/alerts/email.yml.old",
            "models/code_analysis/config.yml.old",
            "models/vulnerability_detection/config.yml.old",
            "models/documentation_generation/config.yml.old",
            "models/test_generation/config.yml.old",
            "models/code_review/config.yml.old"
        ]

        for file in old_files:
            path = Path(file)
            if path.exists():
                path.unlink()
                logger.info(f"Removed old file: {file}")

        # Clean up old directories
        old_dirs = [
            "models/old",
            "metrics/old",
            "alerts/old",
            "health/old",
            "reports/old",
            "logs/old"
        ]

        for directory in old_dirs:
            path = Path(directory)
            if path.exists():
                import shutil
                shutil.rmtree(path)
                logger.info(f"Removed old directory: {directory}")

        return True

    except Exception as e:
        logger.error(f"Error cleaning up old files: {e}")
        return False

if __name__ == "__main__":
    sys.exit(main())
