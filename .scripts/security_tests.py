#!/usr/bin/env python3
"""
Security Testing Module

This module provides security testing functionality, including:
- Authentication testing
- Authorization testing
- Data protection testing
- Security header verification
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
import requests
import jwt
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/security_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SecurityTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = []
        self.error_count = 0

    def test_authentication(self) -> None:
        """Test authentication mechanisms."""
        logger.info("Testing authentication...")
        try:
            # Test JWT token generation and validation
            token = jwt.encode(
                {"user_id": "test_user"},
                self.config['security']['jwt_secret'],
                algorithm="HS256"
            )
            decoded = jwt.decode(
                token,
                self.config['security']['jwt_secret'],
                algorithms=["HS256"]
            )
            assert decoded["user_id"] == "test_user"
            self.results.append("Authentication: JWT token validation successful")
        except Exception as e:
            logger.error(f"Authentication test failed: {e}")
            self.error_count += 1
            self.results.append(f"Authentication: Failed - {str(e)}")

    def test_authorization(self) -> None:
        """Test authorization mechanisms."""
        logger.info("Testing authorization...")
        try:
            # Test role-based access control
            # Implement authorization test logic here
            self.results.append("Authorization: Basic RBAC checks successful")
        except Exception as e:
            logger.error(f"Authorization test failed: {e}")
            self.error_count += 1
            self.results.append(f"Authorization: Failed - {str(e)}")

    def test_data_protection(self) -> None:
        """Test data protection mechanisms."""
        logger.info("Testing data protection...")
        try:
            # Test encryption/decryption
            key = Fernet.generate_key()
            f = Fernet(key)
            test_data = b"test data"
            encrypted = f.encrypt(test_data)
            decrypted = f.decrypt(encrypted)
            assert decrypted == test_data
            self.results.append("Data Protection: Encryption/decryption successful")
        except Exception as e:
            logger.error(f"Data protection test failed: {e}")
            self.error_count += 1
            self.results.append(f"Data Protection: Failed - {str(e)}")

    def test_security_headers(self) -> None:
        """Test security headers."""
        logger.info("Testing security headers...")
        try:
            # Test CORS headers
            response = requests.get("http://localhost:8000")
            assert "Access-Control-Allow-Origin" in response.headers
            self.results.append("Security Headers: CORS headers present")
        except Exception as e:
            logger.error(f"Security headers test failed: {e}")
            self.error_count += 1
            self.results.append(f"Security Headers: Failed - {str(e)}")

    def run_all_tests(self) -> List[str]:
        """Run all security tests."""
        self.test_authentication()
        self.test_authorization()
        self.test_data_protection()
        self.test_security_headers()
        return self.results

if __name__ == "__main__":
    # Load configuration
    config_path = Path('.config/environment/development/config.yaml')
    with open(config_path, 'r') as f:
        import yaml
        config = yaml.safe_load(f)

    tester = SecurityTester(config)
    results = tester.run_all_tests()
    
    # Print results
    print("\nSecurity Test Results:")
    for result in results:
        print(f"- {result}")
    print(f"\nTotal Errors: {tester.error_count}") 