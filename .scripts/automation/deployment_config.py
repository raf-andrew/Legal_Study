"""
Deployment configuration for chaos testing framework.
"""
import os
import sys
import venv
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

class DeploymentConfig:
    def __init__(self):
        self.venv_path = Path('.venv')
        self.requirements_file = Path('requirements.txt')
        self.python_version = "3.11"
        self.test_directories = ['.tests']
        self.error_directories = ['.errors']
        self.script_directories = ['.scripts']
        
    def create_virtual_environment(self) -> bool:
        """Create a virtual environment if it doesn't exist."""
        try:
            if not self.venv_path.exists():
                print(f"Creating virtual environment at {self.venv_path}")
                venv.create(self.venv_path, with_pip=True)
            return True
        except Exception as e:
            print(f"Error creating virtual environment: {str(e)}")
            return False
            
    def install_requirements(self) -> bool:
        """Install required packages from requirements.txt."""
        try:
            if not self.requirements_file.exists():
                print("requirements.txt not found")
                return False
                
            pip_path = self.venv_path / 'Scripts' / 'pip.exe'
            if not pip_path.exists():
                print(f"pip not found at {pip_path}")
                return False
                
            print("Installing requirements...")
            subprocess.check_call([
                str(pip_path),
                'install',
                '-r',
                str(self.requirements_file)
            ])
            return True
        except Exception as e:
            print(f"Error installing requirements: {str(e)}")
            return False
            
    def create_directories(self) -> bool:
        """Create necessary directories if they don't exist."""
        try:
            for dir_path in (self.test_directories + self.error_directories + self.script_directories):
                path = Path(dir_path)
                if not path.exists():
                    print(f"Creating directory: {path}")
                    path.mkdir(parents=True)
            return True
        except Exception as e:
            print(f"Error creating directories: {str(e)}")
            return False
            
    def validate_python_version(self) -> bool:
        """Validate Python version meets requirements."""
        try:
            version = sys.version.split()[0]
            if version >= self.python_version:
                return True
            print(f"Python version {version} is below required version {self.python_version}")
            return False
        except Exception as e:
            print(f"Error checking Python version: {str(e)}")
            return False
            
    def initialize_logging(self) -> bool:
        """Initialize logging configuration."""
        try:
            log_path = Path('.errors')
            if not log_path.exists():
                log_path.mkdir(parents=True)
                
            log_file = log_path / 'chaos_test_log.md'
            if not log_file.exists():
                log_file.touch()
                
            return True
        except Exception as e:
            print(f"Error initializing logging: {str(e)}")
            return False
            
    def bootstrap(self) -> bool:
        """Bootstrap the testing environment."""
        steps = [
            (self.validate_python_version, "Validating Python version"),
            (self.create_virtual_environment, "Creating virtual environment"),
            (self.install_requirements, "Installing requirements"),
            (self.create_directories, "Creating directories"),
            (self.initialize_logging, "Initializing logging")
        ]
        
        for step_func, step_name in steps:
            print(f"\nExecuting: {step_name}")
            if not step_func():
                print(f"Failed: {step_name}")
                return False
            print(f"Success: {step_name}")
            
        return True
        
    def get_python_path(self) -> Optional[str]:
        """Get path to Python executable in virtual environment."""
        try:
            python_path = self.venv_path / 'Scripts' / 'python.exe'
            if python_path.exists():
                return str(python_path)
            return None
        except Exception:
            return None
            
    def get_environment_variables(self) -> Dict[str, str]:
        """Get environment variables for test execution."""
        return {
            'PYTHONPATH': str(Path('.').absolute()),
            'TEST_ENV': 'chaos',
            'LOG_LEVEL': 'INFO',
            'ERROR_DIR': str(Path('.errors').absolute())
        } 