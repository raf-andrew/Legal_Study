#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def setup_local_environment(config: Dict[str, Any]) -> bool:
    """Setup local development environment."""
    try:
        # Create virtual environment
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)

        # Activate virtual environment and install dependencies
        if os.name == 'nt':  # Windows
            activate_script = 'venv\\Scripts\\activate'
            pip_cmd = 'venv\\Scripts\\pip'
        else:  # Unix/Linux
            activate_script = 'source venv/bin/activate'
            pip_cmd = 'venv/bin/pip'

        # Install requirements
        subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
        subprocess.run([pip_cmd, 'install', '-r', 'requirements-test.txt'], check=True)

        logger.info("Local environment setup completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup local environment: {str(e)}")
        return False

def setup_codespaces_environment(config: Dict[str, Any]) -> bool:
    """Setup GitHub Codespaces environment."""
    try:
        # Install system dependencies
        subprocess.run(['apt-get', 'update'], check=True)
        subprocess.run(['apt-get', 'install', '-y', 'python3-venv', 'python3-pip'], check=True)

        # Create and activate virtual environment
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)

        # Install Python dependencies
        subprocess.run(['venv/bin/pip', 'install', '-r', 'requirements.txt'], check=True)
        subprocess.run(['venv/bin/pip', 'install', '-r', 'requirements-test.txt'], check=True)

        logger.info("Codespaces environment setup completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup Codespaces environment: {str(e)}")
        return False

def setup_aws_environment(config: Dict[str, Any]) -> bool:
    """Setup AWS cloud environment."""
    try:
        # Install AWS CLI
        if os.name == 'nt':  # Windows
            subprocess.run(['powershell', '-Command',
                          'Invoke-WebRequest -Uri https://awscli.amazonaws.com/AWSCLIV2.msi -OutFile AWSCLIV2.msi'],
                         check=True)
            subprocess.run(['msiexec.exe', '/i', 'AWSCLIV2.msi', '/quiet', '/norestart'], check=True)
        else:  # Unix/Linux
            subprocess.run(['curl', 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip', '-o', 'awscliv2.zip'],
                         check=True)
            subprocess.run(['unzip', 'awscliv2.zip'], check=True)
            subprocess.run(['sudo', './aws/install'], check=True)

        # Configure AWS credentials
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

        if not all([aws_access_key, aws_secret_key]):
            logger.error("AWS credentials not found in environment variables")
            return False

        # Create virtual environment and install dependencies
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)

        if os.name == 'nt':  # Windows
            pip_cmd = 'venv\\Scripts\\pip'
        else:  # Unix/Linux
            pip_cmd = 'venv/bin/pip'

        # Install requirements
        subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
        subprocess.run([pip_cmd, 'install', '-r', 'requirements-test.txt'], check=True)

        # Install AWS-specific dependencies
        subprocess.run([pip_cmd, 'install', 'boto3', 'awscli'], check=True)

        logger.info("AWS environment setup completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to setup AWS environment: {str(e)}")
        return False

def setup_environment(config: Dict[str, Any]) -> bool:
    """Main environment setup function."""
    environment = config.get('environment', 'local')

    setup_functions = {
        'local': setup_local_environment,
        'codespaces': setup_codespaces_environment,
        'aws': setup_aws_environment
    }

    setup_function = setup_functions.get(environment)
    if not setup_function:
        logger.error(f"Unknown environment: {environment}")
        return False

    return setup_function(config)

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test configuration
    test_config = {
        'environment': 'local',
        'database': {
            'type': 'postgresql',
            'host': 'localhost',
            'port': '5432',
            'name': 'legal_study',
            'user': 'postgres',
            'password': 'postgres'
        }
    }

    success = setup_environment(test_config)
    sys.exit(0 if success else 1)
