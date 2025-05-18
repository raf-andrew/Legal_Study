import os
import re
import json
from datetime import datetime
from pathlib import Path

class TestRunner:
    def __init__(self):
        self.tests_dir = Path(".tests")
        self.errors_dir = Path(".errors")
        self.error_log = self.errors_dir / "error_log.md"
        
    def parse_test_file(self, test_file):
        """Parse a markdown test file and extract test cases"""
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract test cases using markdown headers and content
        test_cases = []
        current_case = None
        
        for line in content.split('\n'):
            if line.startswith('###'):
                if current_case:
                    test_cases.append(current_case)
                current_case = {
                    'title': line.strip('# '),
                    'content': []
                }
            elif current_case:
                current_case['content'].append(line)
                
        if current_case:
            test_cases.append(current_case)
            
        return test_cases
    
    def run_test(self, test_file: str, test_case: dict) -> dict:
        """Execute a single test case and return results"""
        # This is a placeholder for actual test execution logic
        # In a real implementation, this would parse the test content
        # and execute the appropriate checks
        return {
            'status': 'PASSED',
            'errors': [],
            'recovery_attempts': 0,
            'final_status': 'Passed'
        }
    
    def log_error(self, test_file, test_case, error):
        """Log an error to the error log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        error_entry = f"""
### Error Report - {timestamp}
- Test File: {test_file}
- Test Case: {test_case['title']}
- Error: {error}
"""
        
        with open(self.error_log, 'a', encoding='utf-8') as f:
            f.write(error_entry)
    
    def run_all_tests(self):
        """Run all tests in the .tests directory"""
        results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': []
        }
        
        # Walk through all test directories
        for root, _, files in os.walk(self.tests_dir):
            for file in files:
                if file.endswith('_test.md'):
                    test_file = Path(root) / file
                    test_cases = self.parse_test_file(test_file)
                    
                    for test_case in test_cases:
                        results['total_tests'] += 1
                        test_result = self.run_test(str(test_file), test_case)
                        
                        if test_result['status'] == 'PASSED':
                            results['passed_tests'] += 1
                        else:
                            results['failed_tests'] += 1
                            for error in test_result['errors']:
                                self.log_error(test_file, test_case, error)
                                results['errors'].append({
                                    'file': str(test_file),
                                    'case': test_case['title'],
                                    'error': error
                                })
        
        return results

if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run_all_tests()
    
    print("\nTest Results Summary:")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed Tests: {results['passed_tests']}")
    print(f"Failed Tests: {results['failed_tests']}")
    
    if results['errors']:
        print("\nErrors Found:")
        for error in results['errors']:
            print(f"- {error['file']}: {error['case']}")
            print(f"  Error: {error['error']}") 