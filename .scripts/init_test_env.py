#!/usr/bin/env python3
"""
Test Environment Initialization Script

This script sets up the test environment by:
1. Creating necessary directories
2. Initializing logging
3. Setting up virtual environment
4. Installing dependencies
5. Verifying environment configuration
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import List, Dict
import shutil
import venv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/init.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestEnvironmentInitializer:
    def __init__(self):
        self.required_dirs = [
            '.errors',
            '.logs',
            '.tests',
            '.complete',
            '.research',
            '.experiments',
            '.notes',
            '.prompts',
            '.examples',
            '.api',
            '.backups',
            '.venv'
        ]
        self.error_count = 0

    def create_directories(self) -> None:
        """Create required directories if they don't exist."""
        logger.info("Creating required directories...")
        try:
            for dir_path in self.required_dirs:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info("Directory creation successful")
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            self.error_count += 1

    def setup_virtual_environment(self) -> None:
        """Create and configure virtual environment."""
        logger.info("Setting up virtual environment...")
        try:
            venv_path = Path('.venv')
            if not venv_path.exists():
                venv.create(venv_path, with_pip=True)
            logger.info("Virtual environment setup successful")
        except Exception as e:
            logger.error(f"Failed to setup virtual environment: {e}")
            self.error_count += 1

    def install_dependencies(self) -> None:
        """Install required dependencies."""
        logger.info("Installing dependencies...")
        try:
            # Determine pip path based on OS
            pip_path = str(Path('.venv/Scripts/pip' if os.name == 'nt' else '.venv/bin/pip'))
            
            # Install test dependencies
            subprocess.run(
                [pip_path, 'install', '-r', 'requirements.test.txt'],
                check=True
            )
            logger.info("Dependencies installation successful")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            self.error_count += 1

    def verify_environment(self) -> None:
        """Verify environment configuration."""
        logger.info("Verifying environment...")
        try:
            # Check environment file exists
            env_file = Path('.config/environment/env.dev')
            assert env_file.exists(), "Environment file not found"
            
            # Check virtual environment
            venv_path = Path('.venv')
            assert venv_path.exists(), "Virtual environment not found"
            
            # Check required directories
            for dir_path in self.required_dirs:
                assert Path(dir_path).exists(), f"Required directory {dir_path} not found"
            
            logger.info("Environment verification successful")
        except AssertionError as e:
            logger.error(f"Environment verification failed: {e}")
            self.error_count += 1

    def initialize(self) -> None:
        """Initialize test environment."""
        try:
            self.create_directories()
            self.setup_virtual_environment()
            self.install_dependencies()
            self.verify_environment()
        except Exception as e:
            logger.error(f"Environment initialization failed: {e}")
            self.error_count += 1
        finally:
            if self.error_count > 0:
                logger.error(f"Initialization completed with {self.error_count} errors")
            else:
                logger.info("Initialization completed successfully")

if __name__ == "__main__":
    initializer = TestEnvironmentInitializer()
    initializer.initialize()
    sys.exit(1 if initializer.error_count > 0 else 0) 