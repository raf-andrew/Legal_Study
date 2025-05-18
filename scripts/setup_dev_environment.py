#!/usr/bin/env python3
"""
Development Environment Setup Script
This script sets up the development environment.
"""

import os
import sys
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dev_environment_setup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class DevEnvironmentSetup:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "steps": {},
            "overall_status": "pending",
            "execution_time": 0,
            "summary": {}
        }

        # Define setup steps
        self.steps = [
            {
                "name": "python_environment",
                "description": "Setting up Python environment",
                "required": True
            },
            {
                "name": "dependencies",
                "description": "Installing dependencies",
                "required": True
            },
            {
                "name": "git_setup",
                "description": "Configuring Git",
                "required": True
            },
            {
                "name": "ide_setup",
                "description": "Setting up IDE configuration",
                "required": True
            },
            {
                "name": "test_environment",
                "description": "Setting up test environment",
                "required": True
            },
            {
                "name": "documentation",
                "description": "Setting up documentation",
                "required": False
            }
        ]

    def setup_python_environment(self) -> Dict:
        """Set up Python environment"""
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
                return {
                    "status": "fail",
                    "error": f"Python version {python_version.major}.{python_version.minor} is not supported. Please use Python 3.8 or higher."
                }

            # Create virtual environment if it doesn't exist
            if not Path("venv").exists():
                subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

            # Activate virtual environment and upgrade pip
            if os.name == 'nt':  # Windows
                pip_cmd = str(Path("venv/Scripts/pip.exe"))
            else:  # Unix
                pip_cmd = str(Path("venv/bin/pip"))

            subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)

            return {
                "status": "pass",
                "details": {
                    "python_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                    "virtual_env": "venv"
                }
            }
        except Exception as e:
            logger.error(f"Error setting up Python environment: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def install_dependencies(self) -> Dict:
        """Install project dependencies"""
        try:
            # Get the correct pip path
            if os.name == 'nt':  # Windows
                pip_cmd = str(Path("venv/Scripts/pip.exe"))
            else:  # Unix
                pip_cmd = str(Path("venv/bin/pip"))

            # Define package groups
            package_groups = {
                "core": [
                    "pytest==7.4.3",
                    "pytest-asyncio==0.21.1",
                    "pytest-cov==4.1.0",
                    "pytest-xdist==3.3.1",
                    "pytest-timeout==2.1.0",
                    "pytest-json-report==1.5.0"
                ],
                "http": [
                    "requests==2.31.0",
                    "aiohttp==3.9.1",
                    "httpx==0.25.2"
                ],
                "database": [
                    "psycopg2-binary==2.9.9",
                    "redis==5.0.1",
                    "SQLAlchemy==2.0.23"
                ],
                "queue": [
                    "pika==1.3.1",
                    "kombu==5.3.2"
                ],
                "monitoring": [
                    "prometheus-client==0.19.0",
                    "statsd==4.0.1",
                    "datadog==0.47.0"
                ],
                "performance": [
                    "locust==2.17.0"
                ],
                "security": [
                    "bandit==1.7.5",
                    "safety==2.3.5",
                    "cryptography>=41.0.0",
                    "python-jose>=3.3.0",
                    "passlib>=1.7.0"
                ],
                "ai": [
                    "torch==2.1.1",
                    "tensorflow==2.14.0",
                    "transformers==4.35.2",
                    "numpy==1.26.2",
                    "scipy==1.11.4",
                    "scikit-learn==1.3.2"
                ],
                "development": [
                    "black==23.11.0",
                    "flake8==6.1.0",
                    "mypy==1.7.1",
                    "isort==5.12.0",
                    "pre-commit==3.5.0"
                ],
                "documentation": [
                    "Sphinx==7.2.6",
                    "mkdocs>=1.5.3",
                    "mkdocs-material>=9.4.14",
                    "sphinx-rtd-theme>=1.2.0",
                    "sphinx-autodoc-typehints>=1.23.0",
                    "sphinx-click>=4.4.0",
                    "myst-parser>=2.0.0"
                ],
                "utilities": [
                    "python-dotenv==1.0.0",
                    "pyyaml==6.0.1",
                    "rich==13.7.0",
                    "tqdm==4.66.1"
                ]
            }

            installed_groups = []
            failed_groups = []

            # Install each group separately
            for group_name, packages in package_groups.items():
                try:
                    logger.info(f"Installing {group_name} packages...")
                    subprocess.run([pip_cmd, "install"] + packages, check=True)
                    installed_groups.append(group_name)
                except Exception as e:
                    logger.error(f"Error installing {group_name} packages: {e}")
                    failed_groups.append({
                        "group": group_name,
                        "error": str(e)
                    })

            if failed_groups:
                return {
                    "status": "fail",
                    "details": {
                        "installed_groups": installed_groups,
                        "failed_groups": failed_groups
                    }
                }

            return {
                "status": "pass",
                "details": {
                    "installed_groups": installed_groups
                }
            }
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_git(self) -> Dict:
        """Set up Git configuration"""
        try:
            # Check if Git is installed
            subprocess.run(["git", "--version"], check=True)

            # Create .gitignore if it doesn't exist
            gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Testing
.coverage
htmlcov/
.tox/
.pytest_cache/
test_results/
validation_results/

# Documentation
docs/_build/
site/

# Logs
*.log
logs/
"""
            with open(".gitignore", "w") as f:
                f.write(gitignore_content.strip())

            return {
                "status": "pass",
                "details": {
                    "gitignore": ".gitignore"
                }
            }
        except Exception as e:
            logger.error(f"Error setting up Git: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_ide(self) -> Dict:
        """Set up IDE configuration"""
        try:
            # Create VS Code settings
            vscode_settings = {
                "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
                "python.linting.enabled": True,
                "python.linting.flake8Enabled": True,
                "python.formatting.provider": "black",
                "editor.formatOnSave": True,
                "editor.rulers": [88, 100],
                "files.trimTrailingWhitespace": True,
                "files.insertFinalNewline": True
            }

            os.makedirs(".vscode", exist_ok=True)
            with open(".vscode/settings.json", "w") as f:
                json.dump(vscode_settings, f, indent=4)

            return {
                "status": "pass",
                "details": {
                    "vscode_settings": ".vscode/settings.json"
                }
            }
        except Exception as e:
            logger.error(f"Error setting up IDE: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_test_environment(self) -> Dict:
        """Set up test environment"""
        try:
            # Create pytest configuration
            pytest_ini = """
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    security: marks tests as security tests
    performance: marks tests as performance tests
"""
            with open("pytest.ini", "w") as f:
                f.write(pytest_ini.strip())

            # Create test directories
            test_dirs = [
                "tests/unit",
                "tests/integration",
                "tests/performance",
                "tests/security"
            ]
            for test_dir in test_dirs:
                os.makedirs(test_dir, exist_ok=True)
                # Create __init__.py files
                Path(f"{test_dir}/__init__.py").touch()

            return {
                "status": "pass",
                "details": {
                    "pytest_config": "pytest.ini",
                    "test_dirs": test_dirs
                }
            }
        except Exception as e:
            logger.error(f"Error setting up test environment: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_documentation(self) -> Dict:
        """Set up documentation"""
        try:
            # Create documentation directory
            os.makedirs("docs", exist_ok=True)

            # Create MkDocs configuration
            mkdocs_config = """
site_name: Platform Documentation
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - search.suggest
    - search.highlight

nav:
  - Home: index.md
  - User Guide:
    - Getting Started: user-guide/getting-started.md
    - Configuration: user-guide/configuration.md
  - Developer Guide:
    - Setup: developer-guide/setup.md
    - Architecture: developer-guide/architecture.md
    - Testing: developer-guide/testing.md
  - API Reference:
    - Overview: api-reference/overview.md
    - Endpoints: api-reference/endpoints.md
  - Monitoring:
    - Overview: monitoring/overview.md
    - Metrics: monitoring/metrics.md
    - Alerts: monitoring/alerts.md

markdown_extensions:
  - admonition
  - codehilite
  - footnotes
  - toc:
      permalink: true
  - pymdownx.highlight
  - pymdownx.superfences

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          setup_commands:
            - import sys
            - sys.path.append(".")
"""
            with open("mkdocs.yml", "w") as f:
                f.write(mkdocs_config.strip())

            # Create initial documentation files
            doc_files = {
                "docs/index.md": "# Platform Documentation\n\nWelcome to the platform documentation.",
                "docs/user-guide/getting-started.md": "# Getting Started\n\nThis guide will help you get started with the platform.",
                "docs/developer-guide/setup.md": "# Development Setup\n\nThis guide covers the development environment setup.",
                "docs/api-reference/overview.md": "# API Overview\n\nThis section provides an overview of the platform API."
            }

            for file_path, content in doc_files.items():
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(content)

            return {
                "status": "pass",
                "details": {
                    "mkdocs_config": "mkdocs.yml",
                    "doc_files": list(doc_files.keys())
                }
            }
        except Exception as e:
            logger.error(f"Error setting up documentation: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def run_setup(self):
        """Run all setup steps"""
        start_time = time.time()

        # Run setup steps
        self.results["steps"]["python_environment"] = self.setup_python_environment()
        if self.results["steps"]["python_environment"]["status"] == "pass":
            self.results["steps"]["dependencies"] = self.install_dependencies()
            self.results["steps"]["git_setup"] = self.setup_git()
            self.results["steps"]["ide_setup"] = self.setup_ide()
            self.results["steps"]["test_environment"] = self.setup_test_environment()
            self.results["steps"]["documentation"] = self.setup_documentation()

        self.results["execution_time"] = time.time() - start_time

        # Calculate overall status
        failed_steps = [
            step["name"] for step in self.steps
            if step["required"] and
            self.results["steps"][step["name"]]["status"] != "pass"
        ]
        self.results["overall_status"] = "fail" if failed_steps else "pass"

        # Generate summary
        self.generate_summary()

        return self.results

    def generate_summary(self):
        """Generate setup summary"""
        total_steps = len(self.steps)
        passed_steps = sum(
            1 for step in self.results["steps"].values()
            if step["status"] == "pass"
        )
        failed_steps = sum(
            1 for step in self.results["steps"].values()
            if step["status"] == "fail"
        )
        error_steps = sum(
            1 for step in self.results["steps"].values()
            if step["status"] == "error"
        )

        self.results["summary"] = {
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "failed_steps": failed_steps,
            "error_steps": error_steps,
            "success_rate": (passed_steps / total_steps) * 100 if total_steps > 0 else 0,
            "execution_time": self.results["execution_time"]
        }

    def save_results(self):
        """Save setup results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"setup_results/dev_environment_setup_{timestamp}.json"

        os.makedirs("setup_results", exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {results_file}")

    def generate_report(self) -> str:
        """Generate a human-readable setup report"""
        report = f"""
Development Environment Setup Report
================================
Generated at: {self.results['timestamp']}
Overall Status: {self.results['overall_status'].upper()}
Total Execution Time: {self.results['execution_time']:.2f} seconds

Summary:
--------
Total Steps: {self.results['summary']['total_steps']}
Passed Steps: {self.results['summary']['passed_steps']}
Failed Steps: {self.results['summary']['failed_steps']}
Error Steps: {self.results['summary']['error_steps']}
Success Rate: {self.results['summary']['success_rate']:.2f}%

Detailed Results:
---------------
"""

        for step in self.steps:
            step_result = self.results["steps"][step["name"]]
            report += f"\n{step['description'].upper()}:"
            report += f"\n  Status: {step_result['status'].upper()}"

            if step_result.get("details"):
                report += "\n  Details:"
                for key, value in step_result["details"].items():
                    if isinstance(value, list):
                        report += f"\n    {key}:"
                        for item in value:
                            report += f"\n      - {item}"
                    else:
                        report += f"\n    {key}: {value}"

            if step_result.get("error"):
                report += f"\n  Error: {step_result['error']}"

            report += "\n"

        return report

def main():
    setup = DevEnvironmentSetup()
    results = setup.run_setup()
    setup.save_results()

    # Print report
    print(setup.generate_report())

    # Exit with appropriate status code
    sys.exit(0 if results["overall_status"] == "pass" else 1)

if __name__ == "__main__":
    main()
