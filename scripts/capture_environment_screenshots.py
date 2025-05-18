#!/usr/bin/env python3
"""
Environment Screenshot Capture
This script captures screenshots for environment documentation.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnvironmentScreenshotCapture:
    def __init__(self, config_path: str, output_dir: str, github_token: str):
        self.config_path = config_path
        self.output_dir = Path(output_dir)
        self.github_token = github_token
        self.config = self.load_config()
        self.driver = self.setup_driver()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            sys.exit(1)

    def setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        return webdriver.Chrome(options=chrome_options)

    def login_to_github(self) -> None:
        """Log in to GitHub using token."""
        try:
            self.driver.get('https://github.com/login')
            token_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'token'))
            )
            token_input.send_keys(self.github_token)
            self.driver.find_element(By.NAME, 'commit').click()
            logger.info("Successfully logged in to GitHub")
        except Exception as e:
            logger.error(f"Failed to log in to GitHub: {str(e)}")
            sys.exit(1)

    def capture_environment_screenshots(self) -> None:
        """Capture screenshots for environment setup."""
        try:
            # Navigate to repository settings
            repo_url = f"https://github.com/{self.config['repository']['name']}/settings"
            self.driver.get(repo_url)

            # Capture environment creation screenshot
            self.driver.get(f"{repo_url}/environments")
            time.sleep(2)  # Wait for page load
            self.driver.save_screenshot(
                self.output_dir / "create_environment.png"
            )

            # Capture protection rules screenshot
            self.driver.get(f"{repo_url}/environments/new")
            time.sleep(2)
            self.driver.save_screenshot(
                self.output_dir / "protection_rules.png"
            )

            # Capture environment secrets screenshot
            self.driver.get(f"{repo_url}/environments/new")
            time.sleep(2)
            self.driver.save_screenshot(
                self.output_dir / "environment_secrets.png"
            )

            # Capture deployment workflow screenshot
            self.driver.get(f"{repo_url}/actions")
            time.sleep(2)
            self.driver.save_screenshot(
                self.output_dir / "deployment_workflow.png"
            )

            logger.info("Successfully captured environment screenshots")
        except Exception as e:
            logger.error(f"Failed to capture screenshots: {str(e)}")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.driver.quit()

def main():
    parser = argparse.ArgumentParser(description='Capture environment screenshots')
    parser.add_argument('--config', default='docs/github/config.yaml', help='Path to configuration file')
    parser.add_argument('--output', default='docs/github/images/environments', help='Output directory')
    parser.add_argument('--token', required=True, help='GitHub token for authentication')
    args = parser.parse_args()

    capture = EnvironmentScreenshotCapture(args.config, args.output, args.token)
    try:
        capture.login_to_github()
        capture.capture_environment_screenshots()
    finally:
        capture.cleanup()

if __name__ == '__main__':
    main()
