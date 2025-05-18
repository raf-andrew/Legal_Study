#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
import logging
from datetime import datetime
import re
import secrets
import jwt
from cryptography.fernet import Fernet
import hashlib
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/security_verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class SecurityVerifier:
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'errors': []
        }
        
    def _load_env_vars(self) -> dict:
        """Load environment variables from env.dev"""
        try:
            env_file = self.workspace_root / 'env.dev'
            if not env_file.exists():
                raise FileNotFoundError("env.dev file not found")
                
            env_vars = {}
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip("'").strip('"')
                        
            return env_vars
            
        except Exception as e:
            self.results['errors'].append(f"Failed to load environment variables: {str(e)}")
            raise
            
    def _calculate_entropy(self, value: str) -> float:
        """Calculate Shannon entropy of a string"""
        if not value:
            return 0.0
            
        entropy = 0
        size = len(value)
        for x in range(256):
            p_x = value.count(chr(x)) / size
            if p_x > 0:
                entropy += - p_x * math.log2(p_x)
                
        return entropy
        
    def verify_secret_key(self, env_vars: dict) -> bool:
        """Verify SECRET_KEY is present and strong"""
        try:
            secret_key = env_vars.get('SECRET_KEY')
            if not secret_key:
                self.results['checks']['secret_key'] = {
                    'status': 'fail',
                    'message': "SECRET_KEY not found in environment variables"
                }
                return False
                
            # Check length (minimum 32 bytes recommended)
            if len(secret_key) < 32:
                self.results['checks']['secret_key'] = {
                    'status': 'fail',
                    'message': f"SECRET_KEY length ({len(secret_key)}) is less than recommended minimum (32)"
                }
                return False
                
            # Check entropy (should be high for cryptographic keys)
            entropy = self._calculate_entropy(secret_key)
            if entropy < 3.0:  # Arbitrary threshold, adjust as needed
                self.results['checks']['secret_key'] = {
                    'status': 'fail',
                    'message': f"SECRET_KEY entropy ({entropy:.2f}) is too low"
                }
                return False
                
            self.results['checks']['secret_key'] = {
                'status': 'pass',
                'message': "SECRET_KEY meets security requirements"
            }
            return True
            
        except Exception as e:
            self.results['checks']['secret_key'] = {
                'status': 'fail',
                'message': f"Failed to verify SECRET_KEY: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return False
            
    def verify_jwt_config(self, env_vars: dict) -> bool:
        """Verify JWT configuration"""
        try:
            required_vars = ['JWT_SECRET_KEY', 'JWT_ALGORITHM', 'JWT_EXPIRATION_DELTA']
            missing_vars = [var for var in required_vars if var not in env_vars]
            
            if missing_vars:
                self.results['checks']['jwt_config'] = {
                    'status': 'fail',
                    'message': f"Missing JWT variables: {', '.join(missing_vars)}"
                }
                return False
                
            # Verify algorithm is secure
            algorithm = env_vars['JWT_ALGORITHM']
            secure_algorithms = ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512']
            if algorithm not in secure_algorithms:
                self.results['checks']['jwt_config'] = {
                    'status': 'fail',
                    'message': f"Insecure JWT algorithm: {algorithm}"
                }
                return False
                
            # Verify expiration is set
            try:
                expiration = int(env_vars['JWT_EXPIRATION_DELTA'])
                if expiration <= 0:
                    self.results['checks']['jwt_config'] = {
                        'status': 'fail',
                        'message': "JWT expiration must be positive"
                    }
                    return False
            except ValueError:
                self.results['checks']['jwt_config'] = {
                    'status': 'fail',
                    'message': "Invalid JWT expiration value"
                }
                return False
                
            self.results['checks']['jwt_config'] = {
                'status': 'pass',
                'message': "JWT configuration is secure"
            }
            return True
            
        except Exception as e:
            self.results['checks']['jwt_config'] = {
                'status': 'fail',
                'message': f"Failed to verify JWT configuration: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return False
            
    def verify_password_policy(self, env_vars: dict) -> bool:
        """Verify password policy configuration"""
        try:
            required_vars = ['PASSWORD_MIN_LENGTH', 'PASSWORD_REQUIRE_SPECIAL']
            missing_vars = [var for var in required_vars if var not in env_vars]
            
            if missing_vars:
                self.results['checks']['password_policy'] = {
                    'status': 'fail',
                    'message': f"Missing password policy variables: {', '.join(missing_vars)}"
                }
                return False
                
            # Check minimum length
            try:
                min_length = int(env_vars['PASSWORD_MIN_LENGTH'])
                if min_length < 8:
                    self.results['checks']['password_policy'] = {
                        'status': 'fail',
                        'message': f"Password minimum length ({min_length}) is too short"
                    }
                    return False
            except ValueError:
                self.results['checks']['password_policy'] = {
                    'status': 'fail',
                    'message': "Invalid PASSWORD_MIN_LENGTH value"
                }
                return False
                
            self.results['checks']['password_policy'] = {
                'status': 'pass',
                'message': "Password policy is secure"
            }
            return True
            
        except Exception as e:
            self.results['checks']['password_policy'] = {
                'status': 'fail',
                'message': f"Failed to verify password policy: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return False
            
    def verify_cors_config(self, env_vars: dict) -> bool:
        """Verify CORS configuration"""
        try:
            cors_origin = env_vars.get('CORS_ORIGIN', '*')
            
            # Check if CORS is too permissive
            if cors_origin == '*' and env_vars.get('ENV', 'development') == 'production':
                self.results['checks']['cors_config'] = {
                    'status': 'fail',
                    'message': "CORS allows all origins (*) in production"
                }
                return False
                
            # Validate CORS origins format
            if cors_origin != '*':
                origins = cors_origin.split(',')
                for origin in origins:
                    if not re.match(r'^https?://[\w\-\.]+(:\d+)?$', origin.strip()):
                        self.results['checks']['cors_config'] = {
                            'status': 'fail',
                            'message': f"Invalid CORS origin format: {origin}"
                        }
                        return False
                        
            self.results['checks']['cors_config'] = {
                'status': 'pass',
                'message': "CORS configuration is secure"
            }
            return True
            
        except Exception as e:
            self.results['checks']['cors_config'] = {
                'status': 'fail',
                'message': f"Failed to verify CORS configuration: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return False
            
    def verify_rate_limiting(self, env_vars: dict) -> bool:
        """Verify rate limiting configuration"""
        try:
            required_vars = ['RATE_LIMIT_PER_MINUTE', 'RATE_LIMIT_BURST']
            missing_vars = [var for var in required_vars if var not in env_vars]
            
            if missing_vars:
                self.results['checks']['rate_limiting'] = {
                    'status': 'fail',
                    'message': f"Missing rate limiting variables: {', '.join(missing_vars)}"
                }
                return False
                
            # Verify rate limit values
            try:
                per_minute = int(env_vars['RATE_LIMIT_PER_MINUTE'])
                burst = int(env_vars['RATE_LIMIT_BURST'])
                
                if per_minute <= 0 or burst <= 0:
                    self.results['checks']['rate_limiting'] = {
                        'status': 'fail',
                        'message': "Rate limit values must be positive"
                    }
                    return False
                    
                if burst > per_minute * 2:
                    self.results['checks']['rate_limiting'] = {
                        'status': 'fail',
                        'message': "Burst limit is too high compared to per-minute limit"
                    }
                    return False
                    
            except ValueError:
                self.results['checks']['rate_limiting'] = {
                    'status': 'fail',
                    'message': "Invalid rate limit values"
                }
                return False
                
            self.results['checks']['rate_limiting'] = {
                'status': 'pass',
                'message': "Rate limiting configuration is secure"
            }
            return True
            
        except Exception as e:
            self.results['checks']['rate_limiting'] = {
                'status': 'fail',
                'message': f"Failed to verify rate limiting: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return False
            
    def run_verification(self) -> bool:
        """Run all security verification checks"""
        success = True
        
        try:
            env_vars = self._load_env_vars()
            
            # Run all checks
            if not self.verify_secret_key(env_vars):
                success = False
                
            if not self.verify_jwt_config(env_vars):
                success = False
                
            if not self.verify_password_policy(env_vars):
                success = False
                
            if not self.verify_cors_config(env_vars):
                success = False
                
            if not self.verify_rate_limiting(env_vars):
                success = False
                
        except Exception as e:
            self.results['errors'].append(f"Fatal error during verification: {str(e)}")
            success = False
            
        # Save results
        results_file = self.workspace_root / '.testing' / 'security_verification_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        if success:
            logging.info("All security checks passed")
        else:
            logging.error("Some security checks failed")
            
        return success

if __name__ == '__main__':
    verifier = SecurityVerifier()
    success = verifier.run_verification()
    sys.exit(0 if success else 1) 