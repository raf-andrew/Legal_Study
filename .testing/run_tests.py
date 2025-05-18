#!/usr/bin/env python3

import os
import sys
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/test_run.log'),
        logging.StreamHandler()
    ]
)

class TestRunner:
    def __init__(self):
        self.workspace_root = Path(os.getcwd())
        self.test_stages = [
            {
                'name': 'Environment Verification',
                'command': ['python', '.testing/run_verification.py'],
                'required': True
            },
            {
                'name': 'Unit Tests',
                'command': ['pytest', 'tests/unit', '-v'],
                'required': True
            },
            {
                'name': 'Integration Tests',
                'command': ['pytest', 'tests/integration', '-v'],
                'required': True
            },
            {
                'name': 'Security Tests',
                'command': ['pytest', 'tests/security', '-v'],
                'required': True
            },
            {
                'name': 'Performance Tests',
                'command': ['pytest', 'tests/performance', '-v'],
                'required': False
            },
            {
                'name': 'Chaos Tests',
                'command': ['pytest', 'tests/chaos', '-v'],
                'required': False
            }
        ]
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'stages': {},
            'summary': {
                'total': len(self.test_stages),
                'passed': 0,
                'failed': 0,
                'skipped': 0
            }
        }

    def run_stage(self, stage):
        """Run a test stage and return its status."""
        try:
            logging.info(f"\nRunning {stage['name']}...")
            
            result = subprocess.run(
                stage['command'],
                capture_output=True,
                text=True
            )

            status = 'pass' if result.returncode == 0 else 'fail'
            
            self.results['stages'][stage['name']] = {
                'status': status,
                'required': stage['required'],
                'output': result.stdout,
                'error': result.stderr if result.stderr else None
            }

            if status == 'pass':
                logging.info(f"{stage['name']} passed successfully")
                self.results['summary']['passed'] += 1
            else:
                logging.error(f"{stage['name']} failed")
                logging.error(f"Error output:\n{result.stderr}")
                self.results['summary']['failed'] += 1

            return status == 'pass'

        except FileNotFoundError:
            logging.warning(f"Skipping {stage['name']}: Test directory not found")
            self.results['stages'][stage['name']] = {
                'status': 'skipped',
                'required': stage['required'],
                'error': 'Test directory not found'
            }
            self.results['summary']['skipped'] += 1
            return True
        except Exception as e:
            logging.error(f"Error running {stage['name']}: {str(e)}")
            self.results['stages'][stage['name']] = {
                'status': 'fail',
                'required': stage['required'],
                'error': str(e)
            }
            self.results['summary']['failed'] += 1
            return False

    def save_results(self):
        """Save test results to a JSON file."""
        results_file = self.workspace_root / '.testing' / 'test_results.json'
        import json
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

    def run(self):
        """Run all test stages."""
        overall_status = True

        for stage in self.test_stages:
            stage_passed = self.run_stage(stage)
            if not stage_passed and stage['required']:
                overall_status = False
                if stage['name'] != 'Environment Verification':
                    logging.error(f"Required stage {stage['name']} failed. Stopping test execution.")
                    break

        self.save_results()

        logging.info("\nTest Run Summary:")
        logging.info(f"Total Stages: {self.results['summary']['total']}")
        logging.info(f"Passed: {self.results['summary']['passed']}")
        logging.info(f"Failed: {self.results['summary']['failed']}")
        logging.info(f"Skipped: {self.results['summary']['skipped']}")
        logging.info(f"Overall Status: {'PASS' if overall_status else 'FAIL'}")

        return overall_status

if __name__ == '__main__':
    runner = TestRunner()
    success = runner.run()
    sys.exit(0 if success else 1) 