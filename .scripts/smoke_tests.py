#!/usr/bin/env python3
"""
Smoke Testing Module

This module provides smoke testing functionality, including:
- Basic functionality testing
- Core feature verification
- System initialization testing
- Configuration validation
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import requests
import json
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/smoke_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmokeTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = []
        self.error_count = 0

    def test_basic_functionality(self) -> None:
        """Test basic system functionality."""
        logger.info("Testing basic functionality...")
        try:
            # Test API endpoint availability
            response = requests.get("http://localhost:8000/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
            self.results.append("Basic Functionality: Health check successful")
        except Exception as e:
            logger.error(f"Basic functionality test failed: {e}")
            self.error_count += 1
            self.results.append(f"Basic Functionality: Failed - {str(e)}")

    def test_core_features(self) -> None:
        """Test core system features."""
        logger.info("Testing core features...")
        try:
            # Test authentication
            response = requests.post(
                "http://localhost:8000/auth/login",
                json={"username": "test", "password": "test"}
            )
            assert response.status_code == 200
            assert "token" in response.json()
            self.results.append("Core Features: Authentication successful")
        except Exception as e:
            logger.error(f"Core features test failed: {e}")
            self.error_count += 1
            self.results.append(f"Core Features: Failed - {str(e)}")

    def test_system_initialization(self) -> None:
        """Test system initialization."""
        logger.info("Testing system initialization...")
        try:
            # Check required directories
            required_dirs = [
                '.logs',
                '.errors',
                '.tests',
                '.config'
            ]
            for dir_path in required_dirs:
                assert Path(dir_path).exists()
            self.results.append("System Initialization: Required directories present")
        except Exception as e:
            logger.error(f"System initialization test failed: {e}")
            self.error_count += 1
            self.results.append(f"System Initialization: Failed - {str(e)}")

    def test_configuration(self) -> None:
        """Test configuration validation."""
        logger.info("Testing configuration...")
        try:
            # Verify required configuration values
            required_config = [
                'security',
                'database',
                'application',
                'monitoring'
            ]
            for config_key in required_config:
                assert config_key in self.config
            self.results.append("Configuration: Required settings present")
        except Exception as e:
            logger.error(f"Configuration test failed: {e}")
            self.error_count += 1
            self.results.append(f"Configuration: Failed - {str(e)}")

    def run_all_tests(self) -> List[str]:
        """Run all smoke tests."""
        self.test_basic_functionality()
        self.test_core_features()
        self.test_system_initialization()
        self.test_configuration()
        return self.results

if __name__ == "__main__":
    # Load configuration
    config_path = Path('.config/environment/development/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    tester = SmokeTester(config)
    results = tester.run_all_tests()
    
    # Print results
    print("\nSmoke Test Results:")
    for result in results:
        print(f"- {result}")
    print(f"\nTotal Errors: {tester.error_count}") 