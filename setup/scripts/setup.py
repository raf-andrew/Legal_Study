#!/usr/bin/env python3

import os
import sys
import json
import yaml
import shutil
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional
import colorama
from colorama import Fore, Style
import inquirer
from inquirer import themes
import boto3
from botocore.exceptions import ClientError

# Initialize colorama
colorama.init()

class SetupManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.setup_dir = self.root_dir / "setup"
        self.config_dir = self.setup_dir / "config"
        self.templates_dir = self.setup_dir / "templates"
        self.checks_dir = self.setup_dir / "checks"
        self.scripts_dir = self.setup_dir / "scripts"

        # Load configuration
        self.config = self._load_config()

        # Setup status tracking
        self.setup_status = {
            "environment": False,
            "dependencies": False,
            "aws": False,
            "docker": False,
            "github": False,
            "database": False,
            "monitoring": False
        }

    def _load_config(self) -> Dict:
        """Load configuration from config files"""
        config_path = self.config_dir / "setup_config.yaml"
        if not config_path.exists():
            # Create default config
            default_config = {
                "environment": {
                    "python_version": "3.10",
                    "node_version": "18",
                    "docker_version": "20.10"
                },
                "aws": {
                    "enabled": False,
                    "region": "us-east-1",
                    "services": ["ec2", "rds", "s3", "cloudwatch"]
                },
                "docker": {
                    "compose_version": "2.0",
                    "services": ["api", "frontend", "database", "cache"]
                },
                "github": {
                    "enabled": False,
                    "branch_protection": True,
                    "required_checks": ["test", "lint", "security"]
                }
            }
            with open(config_path, "w") as f:
                yaml.dump(default_config, f)
            return default_config

        with open(config_path) as f:
            return yaml.safe_load(f)

    def _print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{text.center(80)}")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

    def _print_step(self, text: str):
        """Print a formatted step"""
        print(f"\n{Fore.GREEN}▶ {text}{Style.RESET_ALL}")

    def _print_success(self, text: str):
        """Print a success message"""
        print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

    def _print_error(self, text: str):
        """Print an error message"""
        print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

    def _print_warning(self, text: str):
        """Print a warning message"""
        print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")

    def check_environment(self) -> bool:
        """Check and setup the development environment"""
        self._print_header("Environment Setup")

        # Check Python version
        python_version = platform.python_version()
        required_version = self.config["environment"]["python_version"]
        if python_version < required_version:
            self._print_error(f"Python {required_version}+ required. Found {python_version}")
            return False
        self._print_success(f"Python version: {python_version}")

        # Check Node.js version
        try:
            node_version = subprocess.check_output(["node", "--version"]).decode().strip()
            required_version = self.config["environment"]["node_version"]
            if node_version < required_version:
                self._print_error(f"Node.js {required_version}+ required. Found {node_version}")
                return False
            self._print_success(f"Node.js version: {node_version}")
        except subprocess.CalledProcessError:
            self._print_error("Node.js not found")
            return False

        # Check Docker
        try:
            docker_version = subprocess.check_output(["docker", "--version"]).decode().strip()
            required_version = self.config["environment"]["docker_version"]
            if docker_version < required_version:
                self._print_error(f"Docker {required_version}+ required. Found {docker_version}")
                return False
            self._print_success(f"Docker version: {docker_version}")
        except subprocess.CalledProcessError:
            self._print_error("Docker not found")
            return False

        return True

    def setup_aws(self) -> bool:
        """Setup AWS configuration and credentials"""
        self._print_header("AWS Setup")

        # Ask if AWS setup is needed
        questions = [
            inquirer.Confirm('setup_aws', message='Do you want to set up AWS integration?', default=False)
        ]
        answers = inquirer.prompt(questions, theme=themes.GreenPassion())
        if not answers or not answers['setup_aws']:
            self._print_warning("AWS setup skipped")
            return True

        # Check AWS CLI
        try:
            aws_version = subprocess.check_output(["aws", "--version"]).decode().strip()
            self._print_success(f"AWS CLI version: {aws_version}")
        except subprocess.CalledProcessError:
            self._print_error("AWS CLI not found. Please install AWS CLI first.")
            self._print_warning("You can install AWS CLI from: https://aws.amazon.com/cli/")
            return False

        # Configure AWS credentials
        questions = [
            inquirer.Text('aws_access_key', message='Enter AWS Access Key ID'),
            inquirer.Text('aws_secret_key', message='Enter AWS Secret Access Key'),
            inquirer.Text('aws_region', message='Enter AWS Region', default=self.config["aws"]["region"])
        ]

        answers = inquirer.prompt(questions, theme=themes.GreenPassion())
        if not answers:
            return False

        # Test AWS credentials
        try:
            session = boto3.Session(
                aws_access_key_id=answers['aws_access_key'],
                aws_secret_access_key=answers['aws_secret_key'],
                region_name=answers['aws_region']
            )
            sts = session.client('sts')
            sts.get_caller_identity()
            self._print_success("AWS credentials verified")

            # Save AWS configuration
            aws_config = {
                "aws_access_key_id": answers['aws_access_key'],
                "aws_secret_access_key": answers['aws_secret_key'],
                "region": answers['aws_region']
            }
            with open(self.config_dir / "aws_config.json", "w") as f:
                json.dump(aws_config, f, indent=2)

            return True
        except ClientError as e:
            self._print_error(f"AWS credentials verification failed: {str(e)}")
            return False

    def setup_docker(self) -> bool:
        """Setup Docker environment"""
        self._print_header("Docker Setup")

        # Check Docker Compose
        try:
            compose_version = subprocess.check_output(["docker-compose", "--version"]).decode().strip()
            required_version = self.config["docker"]["compose_version"]
            if compose_version < required_version:
                self._print_error(f"Docker Compose {required_version}+ required. Found {compose_version}")
                return False
            self._print_success(f"Docker Compose version: {compose_version}")
        except subprocess.CalledProcessError:
            self._print_error("Docker Compose not found")
            return False

        # Build and test Docker services
        try:
            # Check if docker-compose.yml exists
            compose_file = self.root_dir / "docker-compose.yml"
            if not compose_file.exists():
                self._print_error("docker-compose.yml not found")
                return False

            subprocess.run(["docker-compose", "build"], check=True)
            self._print_success("Docker services built successfully")

            subprocess.run(["docker-compose", "up", "-d"], check=True)
            self._print_success("Docker services started successfully")

            # Run health checks
            health_check_script = self.scripts_dir / "check_docker_health.py"
            if health_check_script.exists():
                subprocess.run([sys.executable, str(health_check_script)], check=True)
                self._print_success("Docker services health check passed")

            return True
        except subprocess.CalledProcessError as e:
            self._print_error(f"Docker setup failed: {str(e)}")
            return False

    def setup_github(self) -> bool:
        """Setup GitHub integration"""
        self._print_header("GitHub Setup")

        # Ask if GitHub setup is needed
        questions = [
            inquirer.Confirm('setup_github', message='Do you want to set up GitHub integration?', default=False)
        ]
        answers = inquirer.prompt(questions, theme=themes.GreenPassion())
        if not answers or not answers['setup_github']:
            self._print_warning("GitHub setup skipped")
            return True

        # Check Git
        try:
            git_version = subprocess.check_output(["git", "--version"]).decode().strip()
            self._print_success(f"Git version: {git_version}")
        except subprocess.CalledProcessError:
            self._print_error("Git not found")
            return False

        # Configure GitHub
        questions = [
            inquirer.Text('github_token', message='Enter GitHub Personal Access Token'),
            inquirer.Text('github_repo', message='Enter GitHub repository (owner/repo)')
        ]

        answers = inquirer.prompt(questions, theme=themes.GreenPassion())
        if not answers:
            return False

        # Test GitHub connection
        try:
            subprocess.run(
                ["git", "remote", "set-url", "origin", f"https://{answers['github_token']}@github.com/{answers['github_repo']}.git"],
                check=True
            )
            self._print_success("GitHub connection verified")

            # Save GitHub configuration
            github_config = {
                "token": answers['github_token'],
                "repository": answers['github_repo']
            }
            with open(self.config_dir / "github_config.json", "w") as f:
                json.dump(github_config, f, indent=2)

            return True
        except subprocess.CalledProcessError as e:
            self._print_error(f"GitHub setup failed: {str(e)}")
            return False

    def run_setup(self):
        """Run the complete setup process"""
        self._print_header("Legal Study Platform Setup")

        # Environment setup
        if not self.check_environment():
            self._print_error("Environment setup failed")
            return False
        self.setup_status["environment"] = True

        # AWS setup
        if not self.setup_aws():
            self._print_error("AWS setup failed")
            return False
        self.setup_status["aws"] = True

        # Docker setup
        if not self.setup_docker():
            self._print_error("Docker setup failed")
            return False
        self.setup_status["docker"] = True

        # GitHub setup
        if not self.setup_github():
            self._print_error("GitHub setup failed")
            return False
        self.setup_status["github"] = True

        # Save setup status
        with open(self.config_dir / "setup_status.json", "w") as f:
            json.dump(self.setup_status, f, indent=2)

        self._print_header("Setup Complete")
        self._print_success("All components have been set up successfully!")
        return True

def main():
    setup_manager = SetupManager()
    setup_manager.run_setup()

if __name__ == "__main__":
    main()
