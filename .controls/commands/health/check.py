#!/usr/bin/env python3
"""
Health Check Command

This command performs comprehensive health checks on the Legal Study System.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/health_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthCheck:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.root_dir / '.config'
        self.health_dir = self.root_dir / '.health'
        self.results: Dict[str, Any] = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'status': 'healthy',
            'errors': []
        }

    def check_system_health(self) -> bool:
        """Perform system health checks"""
        try:
            # Check directory structure
            self._check_directory_structure()
            
            # Check configuration
            self._check_configuration()
            
            # Check services
            self._check_services()
            
            # Check security
            self._check_security()
            
            # Check monitoring
            self._check_monitoring()
            
            # Update overall status
            if self.results['errors']:
                self.results['status'] = 'unhealthy'
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            self.results['status'] = 'error'
            self.results['errors'].append(str(e))
            return False

    def _check_directory_structure(self):
        """Check required directory structure"""
        required_dirs = [
            '.controls',
            '.security',
            '.chaos',
            '.ui',
            '.ux',
            '.refactoring',
            '.guide',
            '.api',
            '.integration',
            '.unit',
            '.sniff',
            '.test',
            '.completed',
            '.errors',
            '.qa'
        ]
        
        for dir_name in required_dirs:
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                self.results['errors'].append(f"Missing directory: {dir_name}")
                logger.error(f"Missing directory: {dir_name}")

    def _check_configuration(self):
        """Check system configuration"""
        config_files = [
            '.config/environment/development/config.json',
            '.config/environment/testing/config.json',
            '.config/environment/production/config.json'
        ]
        
        for config_file in config_files:
            file_path = self.root_dir / config_file
            if not file_path.exists():
                self.results['errors'].append(f"Missing configuration file: {config_file}")
                logger.error(f"Missing configuration file: {config_file}")

    def _check_services(self):
        """Check required services"""
        # Add service checks here
        pass

    def _check_security(self):
        """Check security configurations"""
        # Add security checks here
        pass

    def _check_monitoring(self):
        """Check monitoring setup"""
        # Add monitoring checks here
        pass

    def generate_report(self) -> str:
        """Generate health check report"""
        return json.dumps(self.results, indent=2)

def main():
    """Main entry point for health check command"""
    try:
        health_check = HealthCheck()
        if health_check.check_system_health():
            print("Health check passed")
            print(health_check.generate_report())
            sys.exit(0)
        else:
            print("Health check failed")
            print(health_check.generate_report())
            sys.exit(1)
    except Exception as e:
        logger.error(f"Health check command failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 