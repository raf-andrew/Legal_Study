#!/usr/bin/env python3

import os
import sys
import logging
import shutil
import subprocess
from pathlib import Path
import yaml
import venv
import pip

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/setup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TestEnvironmentSetup:
    def __init__(self):
        self.config = None
        self.venv_path = Path('venv')
        
        # Create necessary directories
        self.create_directories()
    
    def create_directories(self):
        """Create necessary directories for testing."""
        directories = [
            '.logs',
            '.errors',
            '.complete',
            'test_data',
            'docs',
            'templates',
            '.config'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def load_config(self):
        """Load test configuration."""
        try:
            config_file = Path('.config/test_config.yaml')
            if not config_file.exists():
                logger.error("Configuration file not found")
                sys.exit(1)
            
            with open(config_file) as f:
                self.config = yaml.safe_load(f)
            
            logger.info("Loaded test configuration")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def create_virtual_environment(self):
        """Create a virtual environment for testing."""
        try:
            if self.venv_path.exists():
                logger.info("Virtual environment already exists")
                return
            
            venv.create(self.venv_path, with_pip=True)
            logger.info("Created virtual environment")
            
        except Exception as e:
            logger.error(f"Error creating virtual environment: {e}")
            sys.exit(1)
    
    def install_dependencies(self):
        """Install required dependencies."""
        try:
            # Activate virtual environment
            if sys.platform == 'win32':
                activate_script = self.venv_path / 'Scripts' / 'activate.bat'
                activate_cmd = f'call {activate_script}'
            else:
                activate_script = self.venv_path / 'bin' / 'activate'
                activate_cmd = f'source {activate_script}'
            
            # Install dependencies
            requirements_file = Path('requirements.txt')
            if not requirements_file.exists():
                logger.error("Requirements file not found")
                sys.exit(1)
            
            subprocess.run(
                f'{activate_cmd} && pip install -r {requirements_file}',
                shell=True,
                check=True
            )
            
            logger.info("Installed dependencies")
            
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            sys.exit(1)
    
    def setup_database(self):
        """Setup test database."""
        try:
            db_type = self.config['database']['type']
            db_name = self.config['database']['name']
            
            if db_type == 'sqlite':
                # SQLite doesn't require setup
                logger.info("SQLite database will be created automatically")
            else:
                logger.error(f"Unsupported database type: {db_type}")
                sys.exit(1)
            
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            sys.exit(1)
    
    def setup_logging(self):
        """Setup logging configuration."""
        try:
            log_config = self.config['logging']
            
            # Configure root logger
            logging.getLogger().setLevel(log_config['level'])
            
            # Create log handlers
            file_handler = logging.FileHandler(log_config['file'])
            error_handler = logging.FileHandler(log_config['error_file'])
            
            # Set formatters
            formatter = logging.Formatter(log_config['format'])
            file_handler.setFormatter(formatter)
            error_handler.setFormatter(formatter)
            
            # Add handlers
            logging.getLogger().addHandler(file_handler)
            logging.getLogger().addHandler(error_handler)
            
            logger.info("Setup logging configuration")
            
        except Exception as e:
            logger.error(f"Error setting up logging: {e}")
            sys.exit(1)
    
    def setup_test_data(self):
        """Setup test data."""
        try:
            # Generate test data
            subprocess.run(
                ['python', 'scripts/generate_test_data.py'],
                check=True
            )
            
            logger.info("Generated test data")
            
        except Exception as e:
            logger.error(f"Error setting up test data: {e}")
            sys.exit(1)
    
    def setup_documentation(self):
        """Setup test documentation."""
        try:
            # Generate documentation
            subprocess.run(
                ['python', 'scripts/generate_docs.py'],
                check=True
            )
            
            logger.info("Generated documentation")
            
        except Exception as e:
            logger.error(f"Error setting up documentation: {e}")
            sys.exit(1)
    
    def setup_environment(self):
        """Main environment setup process."""
        try:
            logger.info("Starting test environment setup")
            
            # Load configuration
            self.load_config()
            
            # Create virtual environment
            self.create_virtual_environment()
            
            # Install dependencies
            self.install_dependencies()
            
            # Setup database
            self.setup_database()
            
            # Setup logging
            self.setup_logging()
            
            # Setup test data
            self.setup_test_data()
            
            # Setup documentation
            self.setup_documentation()
            
            logger.info("Test environment setup completed")
            
        except Exception as e:
            logger.error(f"Error in environment setup process: {e}")
            sys.exit(1)

if __name__ == "__main__":
    setup = TestEnvironmentSetup()
    setup.setup_environment() 