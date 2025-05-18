#!/usr/bin/env python3
import os
import sys
import subprocess
import json
from pathlib import Path
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/environment_verification.log'),
        logging.StreamHandler()
    ]
)

class EnvironmentVerifier:
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent
        self.env_file = self.workspace_root / 'env.dev'
        self.requirements_files = [
            'requirements.txt',
            'requirements-dev.txt',
            'requirements.test.txt'
        ]
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'errors': []
        }

    def verify_virtual_environment(self):
        """Verify virtual environment setup"""
        try:
            # Check if we're in a virtual environment
            has_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
            self.results['checks']['virtual_environment'] = {
                'status': 'pass' if has_venv else 'fail',
                'details': 'Virtual environment detected' if has_venv else 'No virtual environment detected'
            }
            if not has_venv:
                self.results['errors'].append('Virtual environment not detected')
        except Exception as e:
            self.results['checks']['virtual_environment'] = {
                'status': 'error',
                'details': str(e)
            }
            self.results['errors'].append(f'Error checking virtual environment: {str(e)}')

    def verify_dependencies(self):
        """Verify all dependencies are installed"""
        try:
            for req_file in self.requirements_files:
                if not (self.workspace_root / req_file).exists():
                    self.results['checks'][f'dependencies_{req_file}'] = {
                        'status': 'fail',
                        'details': f'Requirements file {req_file} not found'
                    }
                    self.results['errors'].append(f'Requirements file {req_file} not found')
                    continue

                # Check if pip is installed
                try:
                    subprocess.run(['pip', '--version'], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    self.results['checks'][f'dependencies_{req_file}'] = {
                        'status': 'fail',
                        'details': 'pip not installed'
                    }
                    self.results['errors'].append('pip not installed')
                    continue

                # Check if requirements are installed
                try:
                    subprocess.run(['pip', 'check'], check=True, capture_output=True)
                    self.results['checks'][f'dependencies_{req_file}'] = {
                        'status': 'pass',
                        'details': 'All dependencies installed correctly'
                    }
                except subprocess.CalledProcessError as e:
                    self.results['checks'][f'dependencies_{req_file}'] = {
                        'status': 'fail',
                        'details': str(e)
                    }
                    self.results['errors'].append(f'Dependency check failed: {str(e)}')
        except Exception as e:
            self.results['checks']['dependencies'] = {
                'status': 'error',
                'details': str(e)
            }
            self.results['errors'].append(f'Error checking dependencies: {str(e)}')

    def verify_env_file(self):
        """Verify environment file setup"""
        try:
            if not self.env_file.exists():
                self.results['checks']['env_file'] = {
                    'status': 'fail',
                    'details': 'env.dev file not found'
                }
                self.results['errors'].append('env.dev file not found')
                return

            # Check if env file has required variables
            required_vars = [
                'APP_NAME',
                'DEBUG',
                'API_VERSION',
                'DATABASE_URL',
                'SECRET_KEY'
            ]
            
            with open(self.env_file) as f:
                env_content = f.read()
                missing_vars = [var for var in required_vars if f'{var}=' not in env_content]
                
                if missing_vars:
                    self.results['checks']['env_file'] = {
                        'status': 'fail',
                        'details': f'Missing required variables: {", ".join(missing_vars)}'
                    }
                    self.results['errors'].append(f'Missing required environment variables: {", ".join(missing_vars)}')
                else:
                    self.results['checks']['env_file'] = {
                        'status': 'pass',
                        'details': 'All required variables present'
                    }
        except Exception as e:
            self.results['checks']['env_file'] = {
                'status': 'error',
                'details': str(e)
            }
            self.results['errors'].append(f'Error checking env file: {str(e)}')

    def run_verification(self):
        """Run all verification checks"""
        logging.info("Starting environment verification...")
        
        self.verify_virtual_environment()
        self.verify_dependencies()
        self.verify_env_file()
        
        # Save results
        results_file = self.workspace_root / '.testing' / 'environment_verification_results.json'
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
        
        return len(self.results['errors']) == 0

if __name__ == '__main__':
    verifier = EnvironmentVerifier()
    success = verifier.run_verification()
    sys.exit(0 if success else 1) 