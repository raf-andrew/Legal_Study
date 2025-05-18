#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import json
import subprocess
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/verification.log'),
        logging.StreamHandler()
    ]
)

class VerificationRunner:
    def __init__(self):
        self.workspace_root = Path(__file__).parent
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
    
    def run_script(self, script_name: str) -> bool:
        """Run a verification script and collect its results"""
        try:
            script_path = self.workspace_root / script_name
            if not script_path.exists():
                logging.error(f"Script not found: {script_name}")
                return False
            
            # Run the script
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True
            )
            
            # Check if script ran successfully
            if result.returncode != 0:
                logging.error(f"Script {script_name} failed with error: {result.stderr}")
                return False
            
            # Load results from the script's output file
            results_file = self.workspace_root / '.testing' / f'{script_name.replace(".py", "")}_results.json'
            if not results_file.exists():
                logging.error(f"Results file not found for {script_name}")
                return False
            
            with open(results_file) as f:
                script_results = json.load(f)
            
            # Merge results
            self.results['checks'][script_name] = script_results['checks']
            self.results['errors'].extend(script_results.get('errors', []))
            
            return True
            
        except Exception as e:
            logging.error(f"Error running {script_name}: {str(e)}")
            return False
    
    def generate_report(self) -> None:
        """Generate a comprehensive verification report"""
        try:
            # Calculate summary statistics
            total_checks = sum(len(checks) for checks in self.results['checks'].values())
            passed_checks = sum(
                sum(1 for check in checks.values() if check['status'] == 'pass')
                for checks in self.results['checks'].values()
            )
            failed_checks = sum(
                sum(1 for check in checks.values() if check['status'] == 'fail')
                for checks in self.results['checks'].values()
            )
            error_checks = sum(
                sum(1 for check in checks.values() if check['status'] == 'error')
                for checks in self.results['checks'].values()
            )
            
            # Create report
            report = {
                'timestamp': self.results['timestamp'],
                'summary': {
                    'total_checks': total_checks,
                    'passed_checks': passed_checks,
                    'failed_checks': failed_checks,
                    'error_checks': error_checks,
                    'success_rate': f"{(passed_checks / total_checks * 100):.2f}%" if total_checks > 0 else "0%"
                },
                'details': self.results['checks'],
                'errors': self.results['errors']
            }
            
            # Save report
            report_file = self.workspace_root / '.testing' / 'verification_report.json'
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Log summary
            logging.info("Verification Report Summary:")
            logging.info(f"Total checks: {total_checks}")
            logging.info(f"Passed: {passed_checks}")
            logging.info(f"Failed: {failed_checks}")
            logging.info(f"Errors: {error_checks}")
            logging.info(f"Success rate: {report['summary']['success_rate']}")
            
            if self.results['errors']:
                logging.error("Errors found:")
                for error in self.results['errors']:
                    logging.error(f"- {error}")
            
        except Exception as e:
            logging.error(f"Error generating report: {str(e)}")
    
    def run(self) -> bool:
        """Run all verification scripts"""
        logging.info("Starting verification process...")
        
        success = True
        for script in self.verification_scripts:
            logging.info(f"Running {script}...")
            if not self.run_script(script):
                success = False
                logging.error(f"{script} failed")
            else:
                logging.info(f"{script} completed successfully")
        
        # Generate report
        self.generate_report()
        
        return success

if __name__ == '__main__':
    runner = VerificationRunner()
    success = runner.run()
    sys.exit(0 if success else 1) 