#!/usr/bin/env python3

import os
import sys
import jwt
import time
import logging
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/security_test.log'),
        logging.StreamHandler()
    ]
)

class SecurityTest:
    def __init__(self):
        self.workspace_root = Path(os.getcwd())
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'errors': []
        }
        self.test_secret_key = secrets.token_urlsafe(32)
        self.test_user = {
            'id': 1,
            'username': 'test_user',
            'email': 'test@example.com'
        }
        
    def test_jwt_creation(self):
        """Test JWT token creation"""
        try:
            # Create access token
            access_token = jwt.encode(
                {
                    'sub': str(self.test_user['id']),
                    'username': self.test_user['username'],
                    'exp': datetime.utcnow() + timedelta(minutes=30)
                },
                self.test_secret_key,
                algorithm='HS256'
            )
            
            # Create refresh token
            refresh_token = jwt.encode(
                {
                    'sub': str(self.test_user['id']),
                    'type': 'refresh',
                    'exp': datetime.utcnow() + timedelta(days=7)
                },
                self.test_secret_key,
                algorithm='HS256'
            )
            
            assert isinstance(access_token, str)
            assert isinstance(refresh_token, str)
            
            self.results['tests']['jwt_creation'] = {
                'status': 'pass',
                'details': 'JWT tokens created successfully'
            }
            return True
        except Exception as e:
            self.results['tests']['jwt_creation'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"JWT creation test failed: {str(e)}")
            return False
            
    def test_jwt_validation(self):
        """Test JWT token validation"""
        try:
            # Create token
            token = jwt.encode(
                {
                    'sub': str(self.test_user['id']),
                    'username': self.test_user['username'],
                    'exp': datetime.utcnow() + timedelta(minutes=30)
                },
                self.test_secret_key,
                algorithm='HS256'
            )
            
            # Validate token
            payload = jwt.decode(
                token,
                self.test_secret_key,
                algorithms=['HS256']
            )
            
            assert payload['sub'] == str(self.test_user['id'])
            assert payload['username'] == self.test_user['username']
            
            self.results['tests']['jwt_validation'] = {
                'status': 'pass',
                'details': 'JWT token validation successful'
            }
            return True
        except Exception as e:
            self.results['tests']['jwt_validation'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"JWT validation test failed: {str(e)}")
            return False
            
    def test_jwt_expiration(self):
        """Test JWT token expiration"""
        try:
            # Create expired token
            token = jwt.encode(
                {
                    'sub': str(self.test_user['id']),
                    'username': self.test_user['username'],
                    'exp': datetime.utcnow() - timedelta(minutes=1)
                },
                self.test_secret_key,
                algorithm='HS256'
            )
            
            # Try to validate expired token
            try:
                jwt.decode(
                    token,
                    self.test_secret_key,
                    algorithms=['HS256']
                )
                assert False, "Should have raised ExpiredSignatureError"
            except jwt.ExpiredSignatureError:
                pass
                
            self.results['tests']['jwt_expiration'] = {
                'status': 'pass',
                'details': 'JWT token expiration handled correctly'
            }
            return True
        except Exception as e:
            self.results['tests']['jwt_expiration'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"JWT expiration test failed: {str(e)}")
            return False
            
    def test_jwt_invalid_signature(self):
        """Test JWT token invalid signature"""
        try:
            # Create token with one secret
            token = jwt.encode(
                {
                    'sub': str(self.test_user['id']),
                    'username': self.test_user['username'],
                    'exp': datetime.utcnow() + timedelta(minutes=30)
                },
                self.test_secret_key,
                algorithm='HS256'
            )
            
            # Try to validate with different secret
            different_secret = secrets.token_urlsafe(32)
            try:
                jwt.decode(
                    token,
                    different_secret,
                    algorithms=['HS256']
                )
                assert False, "Should have raised InvalidSignatureError"
            except jwt.InvalidSignatureError:
                pass
                
            self.results['tests']['jwt_invalid_signature'] = {
                'status': 'pass',
                'details': 'JWT invalid signature handled correctly'
            }
            return True
        except Exception as e:
            self.results['tests']['jwt_invalid_signature'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"JWT invalid signature test failed: {str(e)}")
            return False
            
    def test_jwt_refresh_flow(self):
        """Test JWT refresh token flow"""
        try:
            # Create refresh token
            refresh_token = jwt.encode(
                {
                    'sub': str(self.test_user['id']),
                    'type': 'refresh',
                    'exp': datetime.utcnow() + timedelta(days=7)
                },
                self.test_secret_key,
                algorithm='HS256'
            )
            
            # Validate refresh token
            payload = jwt.decode(
                refresh_token,
                self.test_secret_key,
                algorithms=['HS256']
            )
            
            # Create new access token
            if payload['type'] == 'refresh':
                new_access_token = jwt.encode(
                    {
                        'sub': payload['sub'],
                        'exp': datetime.utcnow() + timedelta(minutes=30)
                    },
                    self.test_secret_key,
                    algorithm='HS256'
                )
                assert isinstance(new_access_token, str)
                
            self.results['tests']['jwt_refresh_flow'] = {
                'status': 'pass',
                'details': 'JWT refresh flow working correctly'
            }
            return True
        except Exception as e:
            self.results['tests']['jwt_refresh_flow'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"JWT refresh flow test failed: {str(e)}")
            return False
            
    def save_results(self):
        """Save test results to file"""
        results_file = self.workspace_root / '.testing' / 'security_test_results.json'
        import json
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
    def run(self):
        """Run all security tests"""
        logging.info("Starting security tests...")
        
        success = True
        success &= self.test_jwt_creation()
        success &= self.test_jwt_validation()
        success &= self.test_jwt_expiration()
        success &= self.test_jwt_invalid_signature()
        success &= self.test_jwt_refresh_flow()
        
        self.save_results()
        
        if success:
            logging.info("All security tests passed")
        else:
            logging.error("Some security tests failed")
            for error in self.results['errors']:
                logging.error(error)
                
        return success

if __name__ == '__main__':
    test = SecurityTest()
    success = test.run()
    sys.exit(0 if success else 1) 