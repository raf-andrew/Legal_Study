#!/usr/bin/env python3
"""
Smoke tests for deployment verification.
This script runs basic health checks on deployed services.
"""

import argparse
import json
import logging
import sys
import time
from typing import Dict, List, Optional
import urllib.request
from urllib.error import URLError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SmokeTest:
    def __init__(self, name: str, url: str, expected_status: int = 200):
        self.name = name
        self.url = url
        self.expected_status = expected_status

    def run(self) -> bool:
        try:
            with urllib.request.urlopen(self.url) as response:
                status = response.getcode()
                if status == self.expected_status:
                    logger.info(f"✅ {self.name} passed")
                    return True
                else:
                    logger.error(f"❌ {self.name} failed: Expected status {self.expected_status}, got {status}")
                    return False
        except URLError as e:
            logger.error(f"❌ {self.name} failed: {str(e)}")
            return False

def load_config(config_path: str) -> Dict:
    """Load smoke test configuration from JSON file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load config: {str(e)}")
        sys.exit(1)

def run_tests(tests: List[SmokeTest], max_retries: int = 3, retry_delay: int = 5) -> bool:
    """Run smoke tests with retries."""
    for test in tests:
        for attempt in range(max_retries):
            if test.run():
                break
            if attempt < max_retries - 1:
                logger.info(f"Retrying {test.name} in {retry_delay} seconds...")
                time.sleep(retry_delay)
        else:
            logger.error(f"❌ {test.name} failed after {max_retries} attempts")
            return False
    return True

def main():
    parser = argparse.ArgumentParser(description='Run smoke tests for deployment verification')
    parser.add_argument('--config', default='smoke_tests.json', help='Path to smoke test configuration file')
    parser.add_argument('--retries', type=int, default=3, help='Maximum number of retry attempts')
    parser.add_argument('--delay', type=int, default=5, help='Delay between retries in seconds')
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Create test instances
    tests = [
        SmokeTest(
            name=test['name'],
            url=test['url'],
            expected_status=test.get('expected_status', 200)
        )
        for test in config['tests']
    ]

    # Run tests
    success = run_tests(tests, args.retries, args.delay)

    if success:
        logger.info("✅ All smoke tests passed")
        sys.exit(0)
    else:
        logger.error("❌ Smoke tests failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
