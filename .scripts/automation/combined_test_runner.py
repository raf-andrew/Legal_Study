"""
Combined test runner that orchestrates smoke, chaos, and ACID tests.
"""
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent))

from test_runner import TestRunner
from chaos_tests import ChaosTestRunner
from smoke_tests import SmokeTestRunner

class CombinedTestRunner:
    def __init__(self):
        self.tests_dir = Path(".tests")
        self.errors_dir = Path(".errors")
        self.combined_log = self.errors_dir / "combined_test_log.md"
        
        # Initialize individual test runners
        self.smoke_runner = SmokeTestRunner()
        self.chaos_runner = ChaosTestRunner()
        self.base_runner = TestRunner()
        
        # Test execution order
        self.test_phases = [
            ('smoke', self._run_smoke_tests),
            ('chaos', self._run_chaos_tests),
            ('acid', self._run_acid_tests)
        ]
        
    def run_all_tests(self) -> Dict:
        """Run all test phases and return combined results"""
        results = {
            'passed': True,
            'errors': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'phases': {}
        }
        
        try:
            # Run each test phase
            for phase_name, phase_runner in self.test_phases:
                print(f"\nRunning {phase_name} tests...")
                phase_results = phase_runner()
                results['phases'][phase_name] = phase_results
                
                # Update overall status
                if not phase_results['passed']:
                    results['passed'] = False
                    results['errors'].extend(phase_results['errors'])
                    
        except Exception as e:
            results['passed'] = False
            results['errors'].append(f"Test execution failed: {str(e)}")
            
        finally:
            results['end_time'] = datetime.now().isoformat()
            self._log_combined_results(results)
            
        return results
        
    def _run_smoke_tests(self) -> Dict:
        """Run smoke tests"""
        return self.smoke_runner.run_smoke_tests()
        
    def _run_chaos_tests(self) -> Dict:
        """Run chaos tests"""
        results = {
            'passed': True,
            'errors': [],
            'details': {}
        }
        
        try:
            # Run all tests with chaos injection
            test_results = self.chaos_runner.run_all_tests()
            
            # Process results
            results['passed'] = test_results['passed']
            if not test_results['passed']:
                results['errors'].extend(test_results['errors'])
                
            # Add detailed results
            results['details'] = {
                'total_tests': test_results['total_tests'],
                'passed_tests': test_results['passed_tests'],
                'failed_tests': test_results['failed_tests'],
                'recovered_tests': test_results.get('recovered_tests', 0)
            }
            
        except Exception as e:
            results['passed'] = False
            results['errors'].append(f"Chaos test execution failed: {str(e)}")
            
        return results
        
    def _run_acid_tests(self) -> Dict:
        """Run ACID compliance tests"""
        results = {
            'passed': True,
            'errors': [],
            'details': {}
        }
        
        try:
            # Get all test files
            test_files = self._get_test_files()
            
            # Run ACID tests for each file
            for test_file in test_files:
                test_cases = self.chaos_runner.parse_test_file(test_file)
                for test_case in test_cases:
                    acid_results = self.chaos_runner.run_acid_test(test_file, test_case)
                    
                    # Update results
                    if not acid_results['overall']:
                        results['passed'] = False
                        results['errors'].append(
                            f"ACID test failed for {test_file}: {test_case['title']}"
                        )
                        
                    # Add detailed results
                    test_key = f"{test_file}:{test_case['title']}"
                    results['details'][test_key] = acid_results
                    
        except Exception as e:
            results['passed'] = False
            results['errors'].append(f"ACID test execution failed: {str(e)}")
            
        return results
        
    def _get_test_files(self) -> List[Path]:
        """Get all test files from the test directory"""
        test_files = []
        for root, _, files in os.walk(self.tests_dir):
            for file in files:
                if file.endswith('_test.md'):
                    test_files.append(Path(root) / file)
        return test_files
        
    def _log_combined_results(self, results: Dict) -> None:
        """Log combined test results to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"""
### Combined Test Report - {timestamp}
- Overall Status: {'PASSED' if results['passed'] else 'FAILED'}
- Start Time: {results['start_time']}
- End Time: {results['end_time']}

Test Phases:
"""
        
        # Add phase results
        for phase_name, phase_results in results['phases'].items():
            log_entry += f"\n#### {phase_name.title()} Tests\n"
            log_entry += f"- Status: {'PASSED' if phase_results['passed'] else 'FAILED'}\n"
            
            # Add phase details
            if 'details' in phase_results:
                log_entry += "- Details:\n"
                for key, value in phase_results['details'].items():
                    if isinstance(value, dict):
                        log_entry += f"  - {key}:\n"
                        for k, v in value.items():
                            log_entry += f"    - {k}: {v}\n"
                    else:
                        log_entry += f"  - {key}: {value}\n"
                        
            # Add phase errors
            if phase_results['errors']:
                log_entry += "- Errors:\n"
                for error in phase_results['errors']:
                    log_entry += f"  - {error}\n"
                    
        # Add overall errors
        if results['errors']:
            log_entry += "\n#### Overall Errors\n"
            for error in results['errors']:
                log_entry += f"- {error}\n"
                
        with open(self.combined_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

if __name__ == "__main__":
    runner = CombinedTestRunner()
    results = runner.run_all_tests()
    
    print("\nCombined Test Results:")
    print(f"Overall Status: {'PASSED' if results['passed'] else 'FAILED'}")
    print(f"Start Time: {results['start_time']}")
    print(f"End Time: {results['end_time']}")
    
    # Print phase results
    for phase_name, phase_results in results['phases'].items():
        print(f"\n{phase_name.title()} Tests:")
        print(f"Status: {'PASSED' if phase_results['passed'] else 'FAILED'}")
        if 'details' in phase_results:
            print("Details:")
            for key, value in phase_results['details'].items():
                print(f"  {key}: {value}")
                
    if results['errors']:
        print("\nErrors Found:")
        for error in results['errors']:
            print(f"- {error}") 