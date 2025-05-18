import subprocess
import json
import logging
import os
import sys
import shutil
import venv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DevEnvironmentSetup:
    def __init__(self, config_path: str = "config/dev_environment.json"):
        self.config = self._load_config(config_path)
        self.results = {}
        
    def _load_config(self, config_path: str) -> Dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return {
                "python": {
                    "version": "3.9",
                    "packages": [
                        "pytest>=7.0.0",
                        "black>=22.0.0",
                        "flake8>=4.0.0",
                        "mypy>=0.9.0",
                        "requests>=2.28.0",
                        "psutil>=5.9.0"
                    ],
                    "venv_name": "venv"
                },
                "git": {
                    "hooks": {
                        "pre-commit": [
                            "black .",
                            "flake8 .",
                            "mypy ."
                        ],
                        "pre-push": [
                            "pytest tests/"
                        ]
                    },
                    "config": {
                        "core.autocrlf": "input",
                        "pull.rebase": "true"
                    }
                },
                "directories": [
                    "src",
                    "tests",
                    "docs",
                    "config",
                    "scripts",
                    "data",
                    "logs",
                    "reports"
                ],
                "ide": {
                    "vscode": {
                        "extensions": [
                            "ms-python.python",
                            "ms-python.vscode-pylance",
                            "eamodio.gitlens",
                            "streetsidesoftware.code-spell-checker"
                        ],
                        "settings": {
                            "python.formatting.provider": "black",
                            "python.linting.enabled": true,
                            "python.linting.flake8Enabled": true,
                            "editor.formatOnSave": true
                        }
                    }
                }
            }

    def setup_python_environment(self) -> Dict:
        """Set up Python virtual environment and install packages."""
        try:
            venv_path = Path(self.config["python"]["venv_name"])
            
            # Create virtual environment
            if not venv_path.exists():
                logger.info("Creating virtual environment...")
                venv.create(venv_path, with_pip=True)
            
            # Get pip path
            pip_path = str(venv_path / "Scripts" / "pip.exe") if os.name == "nt" else str(venv_path / "bin" / "pip")
            
            # Install packages
            logger.info("Installing Python packages...")
            requirements_path = Path("requirements.txt")
            with open(requirements_path, "w") as f:
                f.write("\n".join(self.config["python"]["packages"]))
            
            subprocess.run([pip_path, "install", "-r", str(requirements_path)], check=True)
            
            return {
                "status": "success",
                "venv_path": str(venv_path),
                "packages_installed": len(self.config["python"]["packages"])
            }
        except Exception as e:
            logger.error(f"Error setting up Python environment: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_git(self) -> Dict:
        """Set up Git configuration and hooks."""
        try:
            # Set Git config
            for key, value in self.config["git"]["config"].items():
                subprocess.run(["git", "config", "--local", key, value], check=True)
            
            # Set up Git hooks
            hooks_dir = Path(".git/hooks")
            if not hooks_dir.exists():
                logger.info("Initializing Git repository...")
                subprocess.run(["git", "init"], check=True)
                hooks_dir.mkdir(exist_ok=True)
            
            for hook_name, commands in self.config["git"]["hooks"].items():
                hook_path = hooks_dir / hook_name
                with open(hook_path, "w") as f:
                    f.write("#!/bin/sh\n\n")
                    f.write(f"source {self.config['python']['venv_name']}/bin/activate\n\n")
                    for cmd in commands:
                        f.write(f"{cmd}\n")
                
                # Make hook executable
                hook_path.chmod(0o755)
            
            return {
                "status": "success",
                "hooks_installed": list(self.config["git"]["hooks"].keys()),
                "config_set": list(self.config["git"]["config"].keys())
            }
        except Exception as e:
            logger.error(f"Error setting up Git: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_directories(self) -> Dict:
        """Create project directory structure."""
        try:
            created_dirs = []
            for directory in self.config["directories"]:
                dir_path = Path(directory)
                if not dir_path.exists():
                    dir_path.mkdir(parents=True)
                    created_dirs.append(directory)
            
            return {
                "status": "success",
                "directories_created": created_dirs
            }
        except Exception as e:
            logger.error(f"Error creating directories: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def setup_ide(self) -> Dict:
        """Set up IDE configuration."""
        try:
            if "vscode" in self.config["ide"]:
                vscode_config = self.config["ide"]["vscode"]
                
                # Create .vscode directory
                vscode_dir = Path(".vscode")
                vscode_dir.mkdir(exist_ok=True)
                
                # Create settings.json
                settings_path = vscode_dir / "settings.json"
                with open(settings_path, "w") as f:
                    json.dump(vscode_config["settings"], f, indent=2)
                
                # Install extensions
                for extension in vscode_config["extensions"]:
                    subprocess.run(["code", "--install-extension", extension], check=True)
                
                return {
                    "status": "success",
                    "ide": "vscode",
                    "settings_path": str(settings_path),
                    "extensions_installed": vscode_config["extensions"]
                }
        except Exception as e:
            logger.error(f"Error setting up IDE: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def validate_environment(self) -> Dict:
        """Validate the development environment setup."""
        results = {
            "python": self._validate_python(),
            "git": self._validate_git(),
            "directories": self._validate_directories(),
            "ide": self._validate_ide()
        }
        
        return {
            "status": "success" if all(r["status"] == "success" for r in results.values()) else "error",
            "components": results
        }

    def _validate_python(self) -> Dict:
        """Validate Python environment."""
        try:
            venv_path = Path(self.config["python"]["venv_name"])
            if not venv_path.exists():
                return {"status": "error", "error": "Virtual environment not found"}
            
            # Check Python version
            python_path = str(venv_path / "Scripts" / "python.exe") if os.name == "nt" else str(venv_path / "bin" / "python")
            result = subprocess.run([python_path, "--version"], capture_output=True, text=True)
            version = result.stdout.strip()
            
            # Check installed packages
            pip_path = str(venv_path / "Scripts" / "pip.exe") if os.name == "nt" else str(venv_path / "bin" / "pip")
            result = subprocess.run([pip_path, "freeze"], capture_output=True, text=True)
            installed_packages = result.stdout.strip().split("\n")
            
            return {
                "status": "success",
                "python_version": version,
                "packages_installed": len(installed_packages)
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _validate_git(self) -> Dict:
        """Validate Git setup."""
        try:
            hooks_dir = Path(".git/hooks")
            if not hooks_dir.exists():
                return {"status": "error", "error": "Git hooks directory not found"}
            
            installed_hooks = []
            for hook_name in self.config["git"]["hooks"]:
                hook_path = hooks_dir / hook_name
                if hook_path.exists():
                    installed_hooks.append(hook_name)
            
            return {
                "status": "success",
                "hooks_installed": installed_hooks
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _validate_directories(self) -> Dict:
        """Validate directory structure."""
        try:
            missing_dirs = []
            for directory in self.config["directories"]:
                if not Path(directory).exists():
                    missing_dirs.append(directory)
            
            return {
                "status": "success" if not missing_dirs else "error",
                "missing_directories": missing_dirs
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _validate_ide(self) -> Dict:
        """Validate IDE setup."""
        try:
            if "vscode" in self.config["ide"]:
                settings_path = Path(".vscode/settings.json")
                if not settings_path.exists():
                    return {"status": "error", "error": "VSCode settings not found"}
                
                with open(settings_path) as f:
                    settings = json.load(f)
                
                return {
                    "status": "success",
                    "settings_found": list(settings.keys())
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def setup_environment(self) -> Dict:
        """Set up the complete development environment."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "python": self.setup_python_environment(),
            "git": self.setup_git(),
            "directories": self.setup_directories(),
            "ide": self.setup_ide()
        }
        
        # Validate the setup
        validation = self.validate_environment()
        results["validation"] = validation
        
        self.results = results
        return results

    def generate_report(self, output_format: str = "text") -> str:
        """Generate a setup report."""
        if not self.results:
            self.setup_environment()
            
        if output_format == "json":
            return json.dumps(self.results, indent=2)
            
        elif output_format == "text":
            report = []
            report.append("Development Environment Setup Report")
            report.append(f"Generated: {self.results['timestamp']}")
            
            for component, result in self.results.items():
                if component != "timestamp":
                    report.append(f"\n{component.title()}:")
                    report.append(f"Status: {result['status'].upper()}")
                    
                    if result["status"] == "error":
                        report.append(f"Error: {result.get('error', 'Unknown error')}")
                    else:
                        for key, value in result.items():
                            if key != "status":
                                report.append(f"{key}: {value}")
            
            return "\n".join(report)
            
        elif output_format == "html":
            html = [
                "<html>",
                "<head>",
                "<style>",
                "body { font-family: Arial, sans-serif; margin: 20px; }",
                ".success { color: green; }",
                ".error { color: red; }",
                ".component { margin: 20px 0; padding: 10px; border: 1px solid #ccc; }",
                "</style>",
                "</head>",
                "<body>",
                "<h1>Development Environment Setup Report</h1>",
                f"<p>Generated: {self.results['timestamp']}</p>"
            ]
            
            for component, result in self.results.items():
                if component != "timestamp":
                    html.append(f'<div class="component">')
                    html.append(f"<h2>{component.title()}</h2>")
                    html.append(f"<p>Status: <span class='{result['status']}'>{result['status'].upper()}</span></p>")
                    
                    if result["status"] == "error":
                        html.append(f"<p class='error'>Error: {result.get('error', 'Unknown error')}</p>")
                    else:
                        html.append("<ul>")
                        for key, value in result.items():
                            if key != "status":
                                html.append(f"<li><strong>{key}:</strong> {value}</li>")
                        html.append("</ul>")
                    
                    html.append("</div>")
            
            html.extend(["</body>", "</html>"])
            return "\n".join(html)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def save_report(self, output_dir: str = "reports") -> None:
        """Save setup results in multiple formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON report
        with open(f"{output_dir}/dev_setup_{timestamp}.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        # Save text report
        with open(f"{output_dir}/dev_setup_{timestamp}.txt", "w") as f:
            f.write(self.generate_report("text"))
        
        # Save HTML report
        with open(f"{output_dir}/dev_setup_{timestamp}.html", "w") as f:
            f.write(self.generate_report("html"))

def main():
    setup = DevEnvironmentSetup()
    
    # Set up environment
    setup.setup_environment()
    
    # Generate and print text report
    print(setup.generate_report("text"))
    
    # Save reports in all formats
    setup.save_report()
    
    # Exit with appropriate status code
    validation = setup.results["validation"]
    if validation["status"] == "error":
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main() 