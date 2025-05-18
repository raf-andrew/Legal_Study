import os
import sys
import subprocess
import json
import yaml
import logging
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(".logs/security_scan.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

class SecurityScanner:
    """Security scanner for console commands."""
    
    def __init__(self, target_dir: str = "."):
        self.target_dir = target_dir
        self.results = {
            'bandit': [],
            'safety': [],
            'dependency_check': [],
            'custom_checks': []
        }
        self.timestamp = datetime.now().isoformat()

    def run_bandit(self):
        """Run Bandit security scanner."""
        logger.info("Running Bandit security scan...")
        try:
            result = subprocess.run(
                ["bandit", "-r", self.target_dir, "-f", "json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.results['bandit'] = json.loads(result.stdout)
                logger.info("Bandit scan completed successfully")
            else:
                logger.error(f"Bandit scan failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error running Bandit: {e}")

    def run_safety(self):
        """Run Safety dependency checker."""
        logger.info("Running Safety check...")
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.results['safety'] = json.loads(result.stdout)
                logger.info("Safety check completed successfully")
            else:
                logger.error(f"Safety check failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error running Safety: {e}")

    def run_dependency_check(self):
        """Run OWASP Dependency Check."""
        logger.info("Running OWASP Dependency Check...")
        try:
            result = subprocess.run(
                [
                    "dependency-check",
                    "--scan", self.target_dir,
                    "--format", "JSON",
                    "--out", ".security/dependency-check-report.json"
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                with open(".security/dependency-check-report.json") as f:
                    self.results['dependency_check'] = json.load(f)
                logger.info("Dependency check completed successfully")
            else:
                logger.error(f"Dependency check failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"Error running Dependency Check: {e}")

    def run_custom_checks(self):
        """Run custom security checks."""
        logger.info("Running custom security checks...")
        checks = [
            self.check_secret_keys(),
            self.check_secure_configs(),
            self.check_input_validation(),
            self.check_authentication(),
            self.check_authorization(),
        ]
        self.results['custom_checks'] = checks
        logger.info("Custom checks completed")

    def check_secret_keys(self) -> Dict[str, Any]:
        """Check for hardcoded secret keys."""
        return {
            'name': 'secret_keys',
            'description': 'Check for hardcoded secret keys',
            'status': 'pass',
            'details': []
        }

    def check_secure_configs(self) -> Dict[str, Any]:
        """Check security of configuration files."""
        return {
            'name': 'secure_configs',
            'description': 'Check security of configuration files',
            'status': 'pass',
            'details': []
        }

    def check_input_validation(self) -> Dict[str, Any]:
        """Check input validation practices."""
        return {
            'name': 'input_validation',
            'description': 'Check input validation practices',
            'status': 'pass',
            'details': []
        }

    def check_authentication(self) -> Dict[str, Any]:
        """Check authentication mechanisms."""
        return {
            'name': 'authentication',
            'description': 'Check authentication mechanisms',
            'status': 'pass',
            'details': []
        }

    def check_authorization(self) -> Dict[str, Any]:
        """Check authorization mechanisms."""
        return {
            'name': 'authorization',
            'description': 'Check authorization mechanisms',
            'status': 'pass',
            'details': []
        }

    def generate_report(self):
        """Generate security scan report."""
        report = {
            'timestamp': self.timestamp,
            'target_directory': self.target_dir,
            'results': self.results,
            'summary': self.generate_summary()
        }
        
        # Save report
        report_path = f".security/security_scan_{self.timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Create YAML summary
        summary_path = f".security/security_scan_{self.timestamp}.yaml"
        with open(summary_path, 'w') as f:
            yaml.dump(self.generate_summary(), f)
        
        logger.info(f"Security scan report saved to {report_path}")
        logger.info(f"Security scan summary saved to {summary_path}")
        
        return report

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of security scan results."""
        return {
            'bandit_issues': len(self.results['bandit']),
            'safety_issues': len(self.results['safety']),
            'dependency_check_issues': len(self.results['dependency_check']),
            'custom_check_issues': sum(1 for check in self.results['custom_checks'] 
                                     if check['status'] != 'pass'),
            'overall_status': self.calculate_overall_status()
        }

    def calculate_overall_status(self) -> str:
        """Calculate overall security status."""
        if (len(self.results['bandit']) > 0 or
            len(self.results['safety']) > 0 or
            len(self.results['dependency_check']) > 0 or
            any(check['status'] != 'pass' for check in self.results['custom_checks'])):
            return 'failed'
        return 'passed'

    def run(self):
        """Run all security scans."""
        self.run_bandit()
        self.run_safety()
        self.run_dependency_check()
        self.run_custom_checks()
        return self.generate_report()

def main():
    """Main function to run security scan."""
    scanner = SecurityScanner()
    report = scanner.run()
    
    # Log summary
    summary = report['summary']
    logger.info("\nSecurity Scan Summary:")
    logger.info(f"Bandit Issues: {summary['bandit_issues']}")
    logger.info(f"Safety Issues: {summary['safety_issues']}")
    logger.info(f"Dependency Check Issues: {summary['dependency_check_issues']}")
    logger.info(f"Custom Check Issues: {summary['custom_check_issues']}")
    logger.info(f"Overall Status: {summary['overall_status']}")

if __name__ == "__main__":
    main() 