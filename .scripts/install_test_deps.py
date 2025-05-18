#!/usr/bin/env python3
"""
Test Dependencies Installer

This script installs all required testing dependencies.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/install.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def install_dependencies() -> None:
    """Install testing dependencies."""
    try:
        # Create virtual environment if it doesn't exist
        venv_path = Path('.venv')
        if not venv_path.exists():
            logger.info("Creating virtual environment...")
            subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)

        # Activate virtual environment and install dependencies
        if os.name == 'nt':  # Windows
            activate_script = venv_path / 'Scripts' / 'activate'
            pip_path = venv_path / 'Scripts' / 'pip'
        else:  # Unix
            activate_script = venv_path / 'bin' / 'activate'
            pip_path = venv_path / 'bin' / 'pip'

        # Install dependencies
        logger.info("Installing testing dependencies...")
        subprocess.run(
            [str(pip_path), 'install', '-r', 'requirements.test.txt'],
            check=True
        )

        logger.info("Testing dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_dependencies() 