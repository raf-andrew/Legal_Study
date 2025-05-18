#!/usr/bin/env python3

import os
import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def install_playwright_browsers():
    """Install Playwright browsers."""
    print("Installing Playwright browsers...")
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

def create_directories():
    """Create necessary directories for testing."""
    print("Creating test directories...")
    directories = [
        ".wireframe/testing/results",
        ".wireframe/testing/screenshots",
        ".wireframe/testing/logs"
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def main():
    """Main setup function."""
    try:
        install_dependencies()
        install_playwright_browsers()
        create_directories()
        print("Setup completed successfully!")
    except Exception as e:
        print(f"Error during setup: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
