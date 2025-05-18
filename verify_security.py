#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import json
import re
from typing import Dict, Any, List
import hashlib
import secrets
import jwt
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/security_verification.log'),
        logging.StreamHandler()
    ]
)

class SecurityVerifier:
    def __init__(self):
        self.workspace_root = Path(__file__).parent
        self.env_file = self.workspace_root / 'env.dev'
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'errors': []
        }
        self.env_vars = self._load_env_vars()
        
    def _load_env_vars(self) -> Dict[str, str]:
        """Load environment variables from env.dev"""
        env_vars = {}
        if not self.env_file.exists():
            raise FileNotFoundError(f"Environment file not found: {self.env_file}")
            
        with open(self.env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
        return env_vars
    
    def verify_secret_key(self) -> bool:
        """Verify SECRET_KEY is properly configured"""
        try:
            secret_key = self.env_vars.get('SECRET_KEY')
            if not secret_key:
                self.results['checks']['secret_key'] = {
                    'status': 'fail',
                    'details': 'SECRET_KEY not found in environment'
                }
                self.results['errors'].append('SECRET_KEY not found in environment')
                return False
            
            # Check length (should be at least 32 bytes)
            if len(secret_key) < 32:
                self.results['checks']['secret_key'] = {
                    'status': 'fail',
                    'details': 'SECRET_KEY is too short (minimum 32 bytes)'
                }
                self.results['errors'].append('SECRET_KEY is too short')
                return False
            
            # Check entropy
            entropy = len(set(secret_key)) / len(secret_key)
            if entropy < 0.5:
                self.results['checks']['secret_key'] = {
                    'status': 'fail',
                    'details': 'SECRET_KEY has low entropy'
                }
                self.results['errors'].append('SECRET_KEY has low entropy')
                return False
            
            self.results['checks']['secret_key'] = {
                'status': 'pass',
                'details': 'SECRET_KEY is properly configured'
            }
            return True
            
        except Exception as e:
            self.results['checks']['secret_key'] = {
                'status': 'error',
                'details': str(e)
            }
            self.results['errors'].append(f'Error checking SECRET_KEY: {str(e)}')
            return False
    
    def verify_jwt_config(self) -> bool:
        """Verify JWT configuration"""
        try:
            required_vars = [
                'JWT_SECRET_KEY',
                'JWT_ALGORITHM',
                'JWT_ACCESS_TOKEN_EXPIRES',
                'JWT_REFRESH_TOKEN_EXPIRES'
            ]
            
            missing_vars = [var for var in required_vars if var not in self.env_vars]
            if missing_vars:
                self.results['checks']['jwt_config'] = {
                    'status': 'fail',
                    'details': f'Missing JWT variables: {", ".join(missing_vars)}'
                }
                self.results['errors'].append(f'Missing JWT variables: {", ".join(missing_vars)}')
                return False
            
            # Verify JWT algorithm
            algorithm = self.env_vars['JWT_ALGORITHM']
            if algorithm not in ['HS256', 'HS384', 'HS512']:
                self.results['checks']['jwt_config'] = {
                    'status': 'fail',
                    'details': f'Invalid JWT algorithm: {algorithm}'
                }
                self.results['errors'].append(f'Invalid JWT algorithm: {algorithm}')
                return False
            
            self.results['checks']['jwt_config'] = {
                'status': 'pass',
                'details': 'JWT configuration is valid'
            }
            return True
            
        except Exception as e:
            self.results['checks']['jwt_config'] = {
                'status': 'error',
                'details': str(e)
            }
            self.results['errors'].append(f'Error checking JWT configuration: {str(e)}')
            return False
    
    def verify_password_policy(self) -> bool:
        """Verify password policy configuration"""
        try:
            required_vars = [
                'PASSWORD_MIN_LENGTH',
                'PASSWORD_REQUIRE_UPPERCASE',
                'PASSWORD_REQUIRE_LOWERCASE',
                'PASSWORD_REQUIRE_NUMBERS',
                'PASSWORD_REQUIRE_SPECIAL'
            ]
            
            missing_vars = [var for var in required_vars if var not in self.env_vars]
            if missing_vars:
                self.results['checks']['password_policy'] = {
                    'status': 'fail',
                    'details': f'Missing password policy variables: {", ".join(missing_vars)}'
                }
                self.results['errors'].append(f'Missing password policy variables: {", ".join(missing_vars)}')
                return False
            
            # Verify minimum length
            min_length = int(self.env_vars['PASSWORD_MIN_LENGTH'])
            if min_length < 8:
                self.results['checks']['password_policy'] = {
                    'status': 'fail',
                    'details': f'Password minimum length ({min_length}) is too short'
                }
                self.results['errors'].append('Password minimum length is too short')
                return False
            
            self.results['checks']['password_policy'] = {
                'status': 'pass',
                'details': 'Password policy is properly configured'
            }
            return True
            
        except Exception as e:
            self.results['checks']['password_policy'] = {
                'status': 'error',
                'details': str(e)
            }
            self.results['errors'].append(f'Error checking password policy: {str(e)}')
            return False
    
    def verify_cors_config(self) -> bool:
        """Verify CORS configuration"""
        try:
            required_vars = [
                'CORS_ORIGINS',
                'CORS_METHODS',
                'CORS_HEADERS',
                'CORS_EXPOSE_HEADERS',
                'CORS_SUPPORTS_CREDENTIALS'
            ]
            
            missing_vars = [var for var in required_vars if var not in self.env_vars]
            if missing_vars:
                self.results['checks']['cors_config'] = {
                    'status': 'fail',
                    'details': f'Missing CORS variables: {", ".join(missing_vars)}'
                }
                self.results['errors'].append(f'Missing CORS variables: {", ".join(missing_vars)}')
                return False
            
            # Verify CORS origins
            origins = self.env_vars['CORS_ORIGINS'].split(',')
            if not any(origin.strip() for origin in origins):
                self.results['checks']['cors_config'] = {
                    'status': 'fail',
                    'details': 'No valid CORS origins configured'
                }
                self.results['errors'].append('No valid CORS origins configured')
                return False
            
            self.results['checks']['cors_config'] = {
                'status': 'pass',
                'details': 'CORS configuration is valid'
            }
            return True
            
        except Exception as e:
            self.results['checks']['cors_config'] = {
                'status': 'error',
                'details': str(e)
            }
            self.results['errors'].append(f'Error checking CORS configuration: {str(e)}')
            return False
    
    def verify_rate_limiting(self) -> bool:
        """Verify rate limiting configuration"""
        try:
            required_vars = [
                'RATE_LIMIT_REQUESTS',
                'RATE_LIMIT_PERIOD',
                'RATE_LIMIT_STORAGE_URL'
            ]
            
            missing_vars = [var for var in required_vars if var not in self.env_vars]
            if missing_vars:
                self.results['checks']['rate_limiting'] = {
                    'status': 'fail',
                    'details': f'Missing rate limiting variables: {", ".join(missing_vars)}'
                }
                self.results['errors'].append(f'Missing rate limiting variables: {", ".join(missing_vars)}')
                return False
            
            # Verify rate limit values
            requests = int(self.env_vars['RATE_LIMIT_REQUESTS'])
            period = int(self.env_vars['RATE_LIMIT_PERIOD'])
            
            if requests <= 0 or period <= 0:
                self.results['checks']['rate_limiting'] = {
                    'status': 'fail',
                    'details': 'Invalid rate limit values'
                }
                self.results['errors'].append('Invalid rate limit values')
                return False
            
            self.results['checks']['rate_limiting'] = {
                'status': 'pass',
                'details': 'Rate limiting is properly configured'
            }
            return True
            
        except Exception as e:
            self.results['checks']['rate_limiting'] = {
                'status': 'error',
                'details': str(e)
            }
            self.results['errors'].append(f'Error checking rate limiting: {str(e)}')
            return False
    
    def run_verification(self) -> bool:
        """Run all security verification checks"""
        logging.info("Starting security verification...")
        
        success = True
        success &= self.verify_secret_key()
        success &= self.verify_jwt_config()
        success &= self.verify_password_policy()
        success &= self.verify_cors_config()
        success &= self.verify_rate_limiting()
        
        # Save results
        results_file = self.workspace_root / '.testing' / 'security_verification_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Log summary
        total_checks = len(self.results['checks'])
        passed_checks = sum(1 for check in self.results['checks'].values() if check['status'] == 'pass')
        failed_checks = sum(1 for check in self.results['checks'].values() if check['status'] == 'fail')
        error_checks = sum(1 for check in self.results['checks'].values() if check['status'] == 'error')
        
        logging.info(f"Verification complete. Results:")
        logging.info(f"Total checks: {total_checks}")
        logging.info(f"Passed: {passed_checks}")
        logging.info(f"Failed: {failed_checks}")
        logging.info(f"Errors: {error_checks}")
        
        if self.results['errors']:
            logging.error("Errors found:")
            for error in self.results['errors']:
                logging.error(f"- {error}")
        
        return success

if __name__ == '__main__':
    verifier = SecurityVerifier()
    success = verifier.run_verification()
    sys.exit(0 if success else 1) 