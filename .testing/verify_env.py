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
        logging.StreamHandler(sys.stdout)
    ]
)

class EnvironmentVerifier:
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'errors': []
        }
        
    def verify_virtual_environment(self) -> bool:
        """Verify virtual environment is active"""
        try:
            venv = os.environ.get('VIRTUAL_ENV')
            if venv:
                logging.info(f"Virtual environment active: {venv}")
                self.results['checks']['virtual_env'] = {
                    'status': 'pass',
                    'message': f"Virtual environment active at {venv}"
                }
                return True
            else:
                logging.warning("No virtual environment detected")
                self.results['checks']['virtual_env'] = {
                    'status': 'fail',
                    'message': "No virtual environment active"
                }
                return False
        except Exception as e:
            self.results['errors'].append(str(e))
            return False
            
    def verify_dependencies(self) -> bool:
        """Verify required dependencies are installed"""
        try:
            # Check requirements files exist
            req_files = ['requirements.txt', 'requirements-dev.txt', 'requirements.test.txt']
            for req_file in req_files:
                if not (self.workspace_root / req_file).exists():
                    logging.error(f"Missing requirements file: {req_file}")
                    self.results['checks'][f'req_file_{req_file}'] = {
                        'status': 'fail',
                        'message': f"Missing requirements file: {req_file}"
                    }
                    return False
                    
            # Check pip is installed
            try:
                subprocess.run([sys.executable, '-m', 'pip', '--version'], check=True)
            except subprocess.CalledProcessError:
                logging.error("pip not installed")
                self.results['checks']['pip_installed'] = {
                    'status': 'fail',
                    'message': "pip not installed"
                }
                return False
                
            # Check dependencies are installed
            for req_file in req_files:
                try:
                    subprocess.run(
                        [sys.executable, '-m', 'pip', 'check'],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    self.results['checks'][f'dependencies_{req_file}'] = {
                        'status': 'pass',
                        'message': f"All dependencies in {req_file} are satisfied"
                    }
                except subprocess.CalledProcessError as e:
                    logging.error(f"Dependency check failed for {req_file}: {e.stderr}")
                    self.results['checks'][f'dependencies_{req_file}'] = {
                        'status': 'fail',
                        'message': f"Dependency check failed: {e.stderr}"
                    }
                    return False
                    
            return True
            
        except Exception as e:
            self.results['errors'].append(str(e))
            return False
            
    def verify_env_file(self) -> bool:
        """Verify env.dev file exists and contains required variables"""
        try:
            env_file = self.workspace_root / 'env.dev'
            if not env_file.exists():
                logging.error("env.dev file not found")
                self.results['checks']['env_file'] = {
                    'status': 'fail',
                    'message': "env.dev file not found"
                }
                return False
                
            # Check required variables
            required_vars = ['APP_NAME', 'DEBUG', 'API_VERSION', 'DATABASE_URL', 'SECRET_KEY']
            with open(env_file) as f:
                env_contents = f.read()
                
            missing_vars = []
            for var in required_vars:
                if var not in env_contents:
                    missing_vars.append(var)
                    
            if missing_vars:
                logging.error(f"Missing environment variables: {', '.join(missing_vars)}")
                self.results['checks']['env_vars'] = {
                    'status': 'fail',
                    'message': f"Missing environment variables: {', '.join(missing_vars)}"
                }
                return False
                
            self.results['checks']['env_vars'] = {
                'status': 'pass',
                'message': "All required environment variables present"
            }
            return True
            
        except Exception as e:
            self.results['errors'].append(str(e))
            return False
            
    def run_verification(self) -> bool:
        """Run all verification checks"""
        success = True
        
        if not self.verify_virtual_environment():
            success = False
            
        if not self.verify_dependencies():
            success = False
            
        if not self.verify_env_file():
            success = False
            
        # Save results
        results_file = self.workspace_root / '.testing' / 'environment_verification_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        if success:
            logging.info("All environment checks passed")
        else:
            logging.error("Some environment checks failed")
            
        return success

if __name__ == '__main__':
    verifier = EnvironmentVerifier()
    success = verifier.run_verification()
    sys.exit(0 if success else 1) 