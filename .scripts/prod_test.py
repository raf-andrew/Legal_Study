#!/usr/bin/env python3
"""
Production Test Runner

This script runs tests in a production environment with additional safety checks.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any
import json
import yaml
from datetime import datetime
import subprocess
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/prod_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProdTestRunner:
    def __init__(self):
        self.config = self._load_config()
        self.results = {
            'tests': {},
            'safety': {},
            'backup': {}
        }
        self.error_count = 0
        self.backup_dir = Path('.backup') / datetime.now().strftime('%Y%m%d_%H%M%S')

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = Path('.config/environment/production/config.yaml')
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def create_backup(self) -> None:
        """Create backup of critical files."""
        try:
            logger.info("Creating backup...")
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup critical directories
            critical_dirs = [
                '.config',
                '.scripts',
                '.tests',
                '.errors'
            ]
            
            for dir_path in critical_dirs:
                src = Path(dir_path)
                if src.exists():
                    dst = self.backup_dir / dir_path
                    shutil.copytree(src, dst)
            
            self.results['backup']['status'] = 'success'
            self.results['backup']['location'] = str(self.backup_dir)
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            self.results['backup']['status'] = 'failed'
            self.error_count += 1

    def run_safety_checks(self) -> None:
        """Run safety checks before testing."""
        try:
            logger.info("Running safety checks...")
            # Check disk space
            total, used, free = shutil.disk_usage('/')
            if free < 1024 * 1024 * 1024:  # Less than 1GB free
                raise Exception("Insufficient disk space")
            
            # Check memory
            import psutil
            if psutil.virtual_memory().percent > 90:
                raise Exception("High memory usage")
            
            self.results['safety']['status'] = 'success'
        except Exception as e:
            logger.error(f"Safety checks failed: {e}")
            self.results['safety']['status'] = 'failed'
            self.error_count += 1

    def run_tests(self) -> None:
        """Run test suites with production settings."""
        try:
            logger.info("Running test suites...")
            # Run tests with production settings
            subprocess.run(
                [
                    'pytest',
                    '--no-cov',  # Disable coverage in production
                    '--quiet',  # Minimal output
                    '--tb=short'  # Short traceback
                ],
                check=True
            )
            self.results['tests']['status'] = 'success'
        except subprocess.CalledProcessError as e:
            logger.error(f"Tests failed: {e}")
            self.results['tests']['status'] = 'failed'
            self.error_count += 1

    def generate_report(self) -> None:
        """Generate production test report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_errors': self.error_count,
            'results': self.results
        }

        # Save JSON report
        report_path = Path('.complete') / f"prod_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Save Markdown report
        md_report_path = Path('.complete') / f"prod_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md_report_path, 'w') as f:
            f.write("# Production Test Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total Errors: {self.error_count}\n")
            f.write(f"Backup Location: {self.backup_dir}\n\n")
            
            for check_type, result in self.results.items():
                f.write(f"## {check_type.title()} Checks\n\n")
                f.write(f"Status: {result['status']}\n")
                if 'location' in result:
                    f.write(f"Location: {result['location']}\n")
                f.write("\n")

    def run_all_checks(self) -> None:
        """Run all production checks."""
        try:
            self.create_backup()
            self.run_safety_checks()
            if self.results['safety']['status'] == 'success':
                self.run_tests()
        except Exception as e:
            logger.error(f"Production checks failed: {e}")
            self.error_count += 1
        finally:
            self.generate_report()

if __name__ == "__main__":
    runner = ProdTestRunner()
    runner.run_all_checks()
    
    # Print summary
    print("\nProduction Test Summary:")
    print(f"Total Errors: {runner.error_count}")
    print(f"Backup Location: {runner.backup_dir}")
    print(f"Reports generated in .complete/ directory")
    
    # Exit with appropriate status code
    sys.exit(1 if runner.error_count > 0 else 0) 