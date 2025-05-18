import os
import sys
import subprocess
import logging
import json
import yaml
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(".logs/test_runner.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

class TestRunner:
    """Test runner for console commands."""
    
    def __init__(self):
        self.results = {
            'unit_tests': {},
            'integration_tests': {},
            'performance_tests': {},
            'security_tests': {},
            'qa_tests': {}
        }
        self.timestamp = datetime.now().isoformat()

    def run_unit_tests(self):
        """Run unit tests."""
        logger.info("Running unit tests...")
        try:
            result = subprocess.run(
                [
                    "pytest",
                    ".unit",
                    "--cov=legal_study",
                    "--cov-report=xml:.coverage/coverage.xml",
                    "--cov-report=html:.coverage/html",
                    "--junit-xml=.test/reports/unit_tests.xml",
                    "-v"
                ],
                capture_output=True,
                text=True
            )
            
            self.results['unit_tests'] = {
                'returncode': result.returncode,
                'output': result.stdout,
                'error': result.stderr
            }
            
            if result.returncode == 0:
                logger.info("Unit tests completed successfully")
            else:
                logger.error("Unit tests failed")
                
        except Exception as e:
            logger.error(f"Error running unit tests: {e}")

    def run_integration_tests(self):
        """Run integration tests."""
        logger.info("Running integration tests...")
        try:
            result = subprocess.run(
                [
                    "pytest",
                    ".integration",
                    "--junit-xml=.test/reports/integration_tests.xml",
                    "-v"
                ],
                capture_output=True,
                text=True
            )
            
            self.results['integration_tests'] = {
                'returncode': result.returncode,
                'output': result.stdout,
                'error': result.stderr
            }
            
            if result.returncode == 0:
                logger.info("Integration tests completed successfully")
            else:
                logger.error("Integration tests failed")
                
        except Exception as e:
            logger.error(f"Error running integration tests: {e}")

    def run_performance_tests(self):
        """Run performance tests."""
        logger.info("Running performance tests...")
        try:
            # Run load tests
            load_result = subprocess.run(
                ["python", ".test/performance/load_test.py"],
                capture_output=True,
                text=True
            )
            
            # Run stress tests
            stress_result = subprocess.run(
                ["python", ".test/performance/stress_test.py"],
                capture_output=True,
                text=True
            )
            
            self.results['performance_tests'] = {
                'load_test': {
                    'returncode': load_result.returncode,
                    'output': load_result.stdout,
                    'error': load_result.stderr
                },
                'stress_test': {
                    'returncode': stress_result.returncode,
                    'output': stress_result.stdout,
                    'error': stress_result.stderr
                }
            }
            
            if load_result.returncode == 0 and stress_result.returncode == 0:
                logger.info("Performance tests completed successfully")
            else:
                logger.error("Performance tests failed")
                
        except Exception as e:
            logger.error(f"Error running performance tests: {e}")

    def run_security_tests(self):
        """Run security tests."""
        logger.info("Running security tests...")
        try:
            result = subprocess.run(
                ["python", ".security/scan.py"],
                capture_output=True,
                text=True
            )
            
            self.results['security_tests'] = {
                'returncode': result.returncode,
                'output': result.stdout,
                'error': result.stderr
            }
            
            if result.returncode == 0:
                logger.info("Security tests completed successfully")
            else:
                logger.error("Security tests failed")
                
        except Exception as e:
            logger.error(f"Error running security tests: {e}")

    def run_qa_tests(self):
        """Run QA tests."""
        logger.info("Running QA tests...")
        try:
            # Run code style checks
            style_result = subprocess.run(
                ["black", "--check", "."],
                capture_output=True,
                text=True
            )
            
            # Run type checks
            type_result = subprocess.run(
                ["mypy", "."],
                capture_output=True,
                text=True
            )
            
            # Run linting
            lint_result = subprocess.run(
                ["pylint", "legal_study"],
                capture_output=True,
                text=True
            )
            
            self.results['qa_tests'] = {
                'style_check': {
                    'returncode': style_result.returncode,
                    'output': style_result.stdout,
                    'error': style_result.stderr
                },
                'type_check': {
                    'returncode': type_result.returncode,
                    'output': type_result.stdout,
                    'error': type_result.stderr
                },
                'lint_check': {
                    'returncode': lint_result.returncode,
                    'output': lint_result.stdout,
                    'error': lint_result.stderr
                }
            }
            
            if (style_result.returncode == 0 and
                type_result.returncode == 0 and
                lint_result.returncode == 0):
                logger.info("QA tests completed successfully")
            else:
                logger.error("QA tests failed")
                
        except Exception as e:
            logger.error(f"Error running QA tests: {e}")

    def generate_report(self):
        """Generate test report."""
        report = {
            'timestamp': self.timestamp,
            'results': self.results,
            'summary': self.generate_summary()
        }
        
        # Save report
        report_path = f".test/reports/test_run_{self.timestamp}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Create YAML summary
        summary_path = f".test/reports/test_run_{self.timestamp}.yaml"
        with open(summary_path, 'w') as f:
            yaml.dump(self.generate_summary(), f)
        
        logger.info(f"Test report saved to {report_path}")
        logger.info(f"Test summary saved to {summary_path}")
        
        return report

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of test results."""
        return {
            'unit_tests': self.results['unit_tests'].get('returncode', -1) == 0,
            'integration_tests': self.results['integration_tests'].get('returncode', -1) == 0,
            'performance_tests': all(
                test.get('returncode', -1) == 0 
                for test in self.results['performance_tests'].values()
            ),
            'security_tests': self.results['security_tests'].get('returncode', -1) == 0,
            'qa_tests': all(
                test.get('returncode', -1) == 0 
                for test in self.results['qa_tests'].values()
            ),
            'overall_status': self.calculate_overall_status()
        }

    def calculate_overall_status(self) -> str:
        """Calculate overall test status."""
        summary = self.generate_summary()
        if all(summary.values()):
            return 'passed'
        return 'failed'

    def run(self):
        """Run all tests."""
        self.run_unit_tests()
        self.run_integration_tests()
        self.run_performance_tests()
        self.run_security_tests()
        self.run_qa_tests()
        return self.generate_report()

def main():
    """Main function to run tests."""
    runner = TestRunner()
    report = runner.run()
    
    # Log summary
    summary = report['summary']
    logger.info("\nTest Run Summary:")
    logger.info(f"Unit Tests: {'Passed' if summary['unit_tests'] else 'Failed'}")
    logger.info(f"Integration Tests: {'Passed' if summary['integration_tests'] else 'Failed'}")
    logger.info(f"Performance Tests: {'Passed' if summary['performance_tests'] else 'Failed'}")
    logger.info(f"Security Tests: {'Passed' if summary['security_tests'] else 'Failed'}")
    logger.info(f"QA Tests: {'Passed' if summary['qa_tests'] else 'Failed'}")
    logger.info(f"Overall Status: {summary['overall_status'].upper()}")

if __name__ == "__main__":
    main() 