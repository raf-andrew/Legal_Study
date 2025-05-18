#!/usr/bin/env python3

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.setup/logs/setup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SetupManager:
    def __init__(self):
        self.config_dir = Path('.setup/config')
        self.config_file = self.config_dir / 'setup_config.json'
        self.config: Dict[str, Any] = {}
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            '.setup/config',
            '.setup/logs',
            '.setup/tests',
            '.setup/docs',
            '.setup/scripts',
            '.setup/diagrams'
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def load_config(self):
        """Load existing configuration if available."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                logger.info("Loaded existing configuration")
            except json.JSONDecodeError:
                logger.error("Error loading configuration file")
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        """Save current configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
        logger.info("Configuration saved")

    def interactive_setup(self):
        """Run interactive setup process."""
        print("\n=== Legal Study Platform Setup ===\n")

        # Deployment Environment
        print("\nDeployment Environment:")
        print("1. Local Development")
        print("2. GitHub Codespaces")
        print("3. AWS Cloud")
        env_choice = input("Select deployment environment (1-3): ").strip()

        self.config['environment'] = {
            '1': 'local',
            '2': 'codespaces',
            '3': 'aws'
        }.get(env_choice, 'local')

        # Database Configuration
        print("\nDatabase Configuration:")
        self.config['database'] = {
            'type': input("Database type (postgresql/mysql): ").strip().lower(),
            'host': input("Database host: ").strip(),
            'port': input("Database port: ").strip(),
            'name': input("Database name: ").strip(),
            'user': input("Database user: ").strip(),
            'password': input("Database password: ").strip()
        }

        # API Configuration
        print("\nAPI Configuration:")
        self.config['api'] = {
            'port': input("API port: ").strip(),
            'debug': input("Enable debug mode? (y/n): ").strip().lower() == 'y'
        }

        # Testing Configuration
        print("\nTesting Configuration:")
        self.config['testing'] = {
            'run_unit_tests': input("Run unit tests? (y/n): ").strip().lower() == 'y',
            'run_integration_tests': input("Run integration tests? (y/n): ").strip().lower() == 'y',
            'generate_coverage': input("Generate coverage reports? (y/n): ").strip().lower() == 'y'
        }

        # Documentation Configuration
        print("\nDocumentation Configuration:")
        self.config['documentation'] = {
            'generate_docs': input("Generate documentation? (y/n): ").strip().lower() == 'y',
            'generate_diagrams': input("Generate PlantUML diagrams? (y/n): ").strip().lower() == 'y'
        }

        self.save_config()
        logger.info("Interactive setup completed")

    def test_mode(self):
        """Run in test mode with default configuration."""
        logger.info("Running in test mode")

        # Set default test configuration
        self.config = {
            'environment': 'codespaces',
            'database': {
                'type': 'mysql',
                'host': 'codespaces-mysql',
                'port': '3306',
                'name': 'legal_study',
                'user': 'root',
                'password': 'secret'
            },
            'api': {
                'port': '8000',
                'debug': True
            },
            'testing': {
                'run_unit_tests': True,
                'run_integration_tests': True,
                'generate_coverage': True
            },
            'documentation': {
                'generate_docs': True,
                'generate_diagrams': True
            }
        }

        self.save_config()
        logger.info("Test configuration saved")
        return True

    def execute_setup(self):
        """Execute the setup process based on configuration."""
        try:
            # Import setup modules
            from .setup.scripts.environment_setup import setup_environment
            from .setup.scripts.database_setup import setup_database
            from .setup.scripts.api_setup import setup_api
            from .setup.scripts.test_setup import run_tests
            from .setup.scripts.docs_setup import generate_documentation

            # Execute setup steps
            setup_environment(self.config)
            setup_database(self.config)
            setup_api(self.config)

            if self.config['testing']['run_unit_tests']:
                run_tests(self.config)

            if self.config['documentation']['generate_docs']:
                generate_documentation(self.config)

            logger.info("Setup completed successfully")
            return True

        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Legal Study Platform Setup')
    parser.add_argument('--interactive', action='store_true', help='Run interactive setup')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    args = parser.parse_args()

    setup_manager = SetupManager()

    if args.config:
        setup_manager.config_file = Path(args.config)
        setup_manager.load_config()
    elif args.test:
        setup_manager.test_mode()
    elif args.interactive:
        setup_manager.interactive_setup()
    else:
        setup_manager.load_config()

    success = setup_manager.execute_setup()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
