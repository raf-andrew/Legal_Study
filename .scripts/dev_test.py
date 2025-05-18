#!/usr/bin/env python3
"""
Development Test Runner

This script runs tests in a development environment with additional debugging features.
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
import webbrowser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/dev_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DevTestRunner:
    def __init__(self):
        self.config = self._load_config()
        self.results = {
            'tests': {},
            'debugging': {},
            'performance': {}
        }
        self.error_count = 0

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = Path('.config/environment/development/config.yaml')
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def run_tests(self) -> None:
        """Run test suites with debugging enabled."""
        try:
            logger.info("Running test suites with debugging...")
            # Run tests with pytest and enable debugging
            subprocess.run(
                [
                    'pytest',
                    '--pdb',  # Enter debugger on failure
                    '--capture=no',  # Show output
                    '--verbose'  # Show detailed output
                ],
                check=True
            )
            self.results['tests']['status'] = 'success'
        except subprocess.CalledProcessError as e:
            logger.error(f"Tests failed: {e}")
            self.results['tests']['status'] = 'failed'
            self.error_count += 1

    def run_debugging_tools(self) -> None:
        """Run debugging tools."""
        try:
            logger.info("Running debugging tools...")
            # Run memory profiler
            subprocess.run(
                ['python', '-m', 'memory_profiler', '.scripts/run_tests.py'],
                check=True
            )
            # Run line profiler
            subprocess.run(
                ['kernprof', '-l', '-v', '.scripts/run_tests.py'],
                check=True
            )
            self.results['debugging']['status'] = 'success'
        except subprocess.CalledProcessError as e:
            logger.error(f"Debugging tools failed: {e}")
            self.results['debugging']['status'] = 'failed'
            self.error_count += 1

    def run_performance_checks(self) -> None:
        """Run performance checks."""
        try:
            logger.info("Running performance checks...")
            # Run cProfile
            subprocess.run(
                ['python', '-m', 'cProfile', '-o', '.tests/profile.out', '.scripts/run_tests.py'],
                check=True
            )
            # Generate performance report
            subprocess.run(
                ['python', '-m', 'pstats', '.tests/profile.out'],
                check=True
            )
            self.results['performance']['status'] = 'success'
        except subprocess.CalledProcessError as e:
            logger.error(f"Performance checks failed: {e}")
            self.results['performance']['status'] = 'failed'
            self.error_count += 1

    def generate_report(self) -> None:
        """Generate development test report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_errors': self.error_count,
            'results': self.results
        }

        # Save JSON report
        report_path = Path('.complete') / f"dev_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Save Markdown report
        md_report_path = Path('.complete') / f"dev_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md_report_path, 'w') as f:
            f.write("# Development Test Report\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total Errors: {self.error_count}\n\n")
            
            for check_type, result in self.results.items():
                f.write(f"## {check_type.title()} Checks\n\n")
                f.write(f"Status: {result['status']}\n\n")

        # Open report in browser
        webbrowser.open(f'file://{md_report_path.absolute()}')

    def run_all_checks(self) -> None:
        """Run all development checks."""
        try:
            self.run_tests()
            self.run_debugging_tools()
            self.run_performance_checks()
        except Exception as e:
            logger.error(f"Development checks failed: {e}")
            self.error_count += 1
        finally:
            self.generate_report()

if __name__ == "__main__":
    runner = DevTestRunner()
    runner.run_all_checks()
    
    # Print summary
    print("\nDevelopment Test Summary:")
    print(f"Total Errors: {runner.error_count}")
    print(f"Reports generated in .complete/ directory")
    print("Opening report in browser...") 