#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import logging
from datetime import datetime
import json
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class VerificationRunner:
    def __init__(self):
        self.workspace_root = Path(os.getcwd())
        self.verification_scripts = [
            'verify_env.py',
            'verify_database.py',
            'verify_security.py'
        ]
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'errors': []
        }

    def run_script(self, script_name):
        """Run a verification script and collect its results."""
        script_path = self.workspace_root / '.testing' / script_name
        try:
            if not script_path.exists():
                raise FileNotFoundError(f"Script not found: {script_name}")

            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True
            )

            # Check if script executed successfully
            if result.returncode != 0:
                self.results['errors'].append({
                    'script': script_name,
                    'error': result.stderr
                })
                return False

            # Load results from the script's JSON output
            results_file = self.workspace_root / '.testing' / f"{script_name.replace('.py', '')}_results.json"
            if not results_file.exists():
                raise FileNotFoundError(f"Results file not found: {results_file}")

            with open(results_file, 'r') as f:
                script_results = json.load(f)
                self.results['checks'][script_name] = script_results

            return True

        except Exception as e:
            self.results['errors'].append({
                'script': script_name,
                'error': str(e)
            })
            logging.error(f"Error running {script_name}: {str(e)}")
            return False

    def generate_report(self):
        """Generate a summary report of all verification results."""
        total_checks = 0
        passed_checks = 0
        failed_checks = 0
        error_checks = len(self.results['errors'])

        for script_results in self.results['checks'].values():
            if isinstance(script_results, dict):
                total_checks += script_results.get('total_checks', 0)
                passed_checks += script_results.get('passed_checks', 0)
                failed_checks += script_results.get('failed_checks', 0)

        summary = {
            'timestamp': self.results['timestamp'],
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'error_checks': error_checks,
            'status': 'pass' if (failed_checks == 0 and error_checks == 0) else 'fail'
        }

        self.results['summary'] = summary

        # Save the complete report
        report_path = self.workspace_root / '.testing' / 'verification_report.json'
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        logging.info(f"Verification Report Summary:")
        logging.info(f"Total Checks: {total_checks}")
        logging.info(f"Passed Checks: {passed_checks}")
        logging.info(f"Failed Checks: {failed_checks}")
        logging.info(f"Error Checks: {error_checks}")
        logging.info(f"Overall Status: {summary['status']}")

        if len(self.results['errors']) > 0:
            logging.error("Errors encountered during verification:")
            for error in self.results['errors']:
                logging.error(f"{error['script']}: {error['error']}")

    def update_checklist(self):
        """Update the testing checklist based on verification results."""
        try:
            subprocess.run(
                [sys.executable, str(self.workspace_root / '.testing' / 'update_checklist.py')],
                check=True
            )
            logging.info("Successfully updated testing checklist")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to update checklist: {str(e)}")
        except Exception as e:
            logging.error(f"Error updating checklist: {str(e)}")

    def run(self):
        """Run all verification scripts and generate report."""
        for script in self.verification_scripts:
            self.run_script(script)
        
        self.generate_report()
        self.update_checklist()

        # Exit with appropriate status code
        if self.results['summary']['status'] == 'fail':
            sys.exit(1)

if __name__ == '__main__':
    runner = VerificationRunner()
    runner.run() 