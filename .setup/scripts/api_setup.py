#!/usr/bin/env python3

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
import yaml
import json

logger = logging.getLogger(__name__)

def setup_api_config(config: Dict[str, Any]) -> bool:
    """Setup API configuration files."""
    try:
        # Create config directory if it doesn't exist
        config_dir = Path('config')
        config_dir.mkdir(exist_ok=True)

        # Create API configuration
        api_config = {
            'server': {
                'host': '0.0.0.0',
                'port': int(config['api']['port']),
                'debug': config['api']['debug']
            },
            'database': config['database'],
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'logs/api.log'
            },
            'security': {
                'secret_key': os.urandom(32).hex(),
                'token_expiry': 3600
            }
        }

        # Save API configuration
        with open(config_dir / 'api_config.yaml', 'w') as f:
            yaml.dump(api_config, f, default_flow_style=False)

        # Create environment file
        env_config = {
            'FLASK_APP': 'legal_study.api.app',
            'FLASK_ENV': 'development' if config['api']['debug'] else 'production',
            'FLASK_DEBUG': str(config['api']['debug']).lower(),
            'DATABASE_URL': f"{config['database']['type']}://{config['database']['user']}:{config['database']['password']}@{config['database']['host']}:{config['database']['port']}/{config['database']['name']}"
        }

        # Save environment configuration
        with open('.env', 'w') as f:
            for key, value in env_config.items():
                f.write(f"{key}={value}\n")

        logger.info("API configuration setup completed")
        return True

    except Exception as e:
        logger.error(f"Failed to setup API configuration: {str(e)}")
        return False

def setup_api_dependencies() -> bool:
    """Install API dependencies."""
    try:
        # Install required packages
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)

        # Install development dependencies if in debug mode
        if os.getenv('FLASK_DEBUG', 'false').lower() == 'true':
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements-dev.txt'], check=True)

        logger.info("API dependencies installed successfully")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install API dependencies: {str(e)}")
        return False

def setup_api_logging() -> bool:
    """Setup API logging configuration."""
    try:
        # Create logs directory
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)

        # Configure logging
        logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'INFO',
                    'formatter': 'standard',
                    'filename': 'logs/api.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': True
                }
            }
        }

        # Save logging configuration
        with open('config/logging_config.json', 'w') as f:
            json.dump(logging_config, f, indent=4)

        logger.info("API logging setup completed")
        return True

    except Exception as e:
        logger.error(f"Failed to setup API logging: {str(e)}")
        return False

def setup_api(config: Dict[str, Any]) -> bool:
    """Main API setup function."""
    try:
        # Setup API configuration
        if not setup_api_config(config):
            return False

        # Setup API dependencies
        if not setup_api_dependencies():
            return False

        # Setup API logging
        if not setup_api_logging():
            return False

        logger.info("API setup completed successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to setup API: {str(e)}")
        return False

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test configuration
    test_config = {
        'api': {
            'port': '5000',
            'debug': True
        },
        'database': {
            'type': 'postgresql',
            'host': 'localhost',
            'port': '5432',
            'name': 'legal_study',
            'user': 'postgres',
            'password': 'postgres'
        }
    }

    success = setup_api(test_config)
    sys.exit(0 if success else 1)
