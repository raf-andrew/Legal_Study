"""
Smoke tests for basic functionality verification.
"""
import os
import sys
import time
import psutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class SmokeTestRunner:
    def __init__(self):
        self.tests_dir = Path(".tests")
        self.errors_dir = Path(".errors")
        self.smoke_log = self.errors_dir / "smoke_test_log.md"
        self.resource_limits = {
            'memory_mb': 256,
            'cpu_percent': 70,
            'disk_percent': 85,
            'file_size_mb': 5
        }
        self.required_directories = {
            '.tests',
            '.errors',
            '.scripts',
            '.research',
            '.qa'
        }
        self.required_files = {
            '.tests/README.md',
            '.scripts/automation/test_runner.py',
            '.scripts/automation/chaos_tests.py',
            '.scripts/automation/security_config.py'
        }
        
    def run_smoke_tests(self) -> Dict:
        """Run all smoke tests and return results"""
        results = {
            'passed': True,
            'errors': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'details': {}
        }
        
        try:
            # Test 1: Directory Structure
            dir_results = self._test_directory_structure()
            results['details']['directory_structure'] = dir_results
            if not dir_results['passed']:
                results['passed'] = False
                results['errors'].extend(dir_results['errors'])
                
            # Test 2: File Permissions
            perm_results = self._test_file_permissions()
            results['details']['file_permissions'] = perm_results
            if not perm_results['passed']:
                results['passed'] = False
                results['errors'].extend(perm_results['errors'])
                
            # Test 3: Resource Usage
            resource_results = self._test_resource_usage()
            results['details']['resource_usage'] = resource_results
            if not resource_results['passed']:
                results['passed'] = False
                results['errors'].extend(resource_results['errors'])
                
            # Test 4: Basic Operations
            op_results = self._test_basic_operations()
            results['details']['basic_operations'] = op_results
            if not op_results['passed']:
                results['passed'] = False
                results['errors'].extend(op_results['errors'])
                
            # Test 5: Security Checks
            security_results = self._test_security_checks()
            results['details']['security_checks'] = security_results
            if not security_results['passed']:
                results['passed'] = False
                results['errors'].extend(security_results['errors'])
                
        except Exception as e:
            results['passed'] = False
            results['errors'].append(f"Smoke test execution failed: {str(e)}")
            
        finally:
            results['end_time'] = datetime.now().isoformat()
            self._log_smoke_test_results(results)
            
        return results
        
    def _test_directory_structure(self) -> Dict:
        """Test if required directories and files exist"""
        results = {
            'passed': True,
            'errors': [],
            'missing_dirs': [],
            'missing_files': []
        }
        
        # Check required directories
        for dir_path in self.required_directories:
            if not os.path.isdir(dir_path):
                results['passed'] = False
                results['missing_dirs'].append(dir_path)
                
        # Check required files
        for file_path in self.required_files:
            if not os.path.isfile(file_path):
                results['passed'] = False
                results['missing_files'].append(file_path)
                
        if not results['passed']:
            if results['missing_dirs']:
                results['errors'].append(f"Missing directories: {', '.join(results['missing_dirs'])}")
            if results['missing_files']:
                results['errors'].append(f"Missing files: {', '.join(results['missing_files'])}")
                
        return results
        
    def _test_file_permissions(self) -> Dict:
        """Test file permissions and access"""
        results = {
            'passed': True,
            'errors': [],
            'permission_issues': []
        }
        
        try:
            # Check test directory permissions
            if not os.access(self.tests_dir, os.R_OK):
                results['passed'] = False
                results['permission_issues'].append(f"Cannot read test directory: {self.tests_dir}")
                
            # Check error directory permissions
            if not os.access(self.errors_dir, os.W_OK):
                results['passed'] = False
                results['permission_issues'].append(f"Cannot write to error directory: {self.errors_dir}")
                
            # Check required file permissions
            for file_path in self.required_files:
                if os.path.exists(file_path):
                    if not os.access(file_path, os.R_OK):
                        results['passed'] = False
                        results['permission_issues'].append(f"Cannot read file: {file_path}")
                        
        except Exception as e:
            results['passed'] = False
            results['errors'].append(f"File permission test failed: {str(e)}")
            
        if results['permission_issues']:
            results['errors'].extend(results['permission_issues'])
            
        return results
        
    def _test_resource_usage(self) -> Dict:
        """Test system resource usage"""
        results = {
            'passed': True,
            'errors': [],
            'resource_issues': []
        }
        
        try:
            process = psutil.Process()
            
            # Check memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            if memory_mb > self.resource_limits['memory_mb']:
                results['passed'] = False
                results['resource_issues'].append(
                    f"Memory usage ({memory_mb:.2f}MB) exceeds limit ({self.resource_limits['memory_mb']}MB)"
                )
                
            # Check CPU usage
            cpu_percent = process.cpu_percent(interval=1)
            if cpu_percent > self.resource_limits['cpu_percent']:
                results['passed'] = False
                results['resource_issues'].append(
                    f"CPU usage ({cpu_percent}%) exceeds limit ({self.resource_limits['cpu_percent']}%)"
                )
                
            # Check disk usage
            disk_usage = psutil.disk_usage('/').percent
            if disk_usage > self.resource_limits['disk_percent']:
                results['passed'] = False
                results['resource_issues'].append(
                    f"Disk usage ({disk_usage}%) exceeds limit ({self.resource_limits['disk_percent']}%)"
                )
                
            # Check file sizes
            for file_path in self.required_files:
                if os.path.exists(file_path):
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    if size_mb > self.resource_limits['file_size_mb']:
                        results['passed'] = False
                        results['resource_issues'].append(
                            f"File size ({size_mb:.2f}MB) exceeds limit ({self.resource_limits['file_size_mb']}MB): {file_path}"
                        )
                        
        except Exception as e:
            results['passed'] = False
            results['errors'].append(f"Resource usage test failed: {str(e)}")
            
        if results['resource_issues']:
            results['errors'].extend(results['resource_issues'])
            
        return results
        
    def _test_basic_operations(self) -> Dict:
        """Test basic file operations"""
        results = {
            'passed': True,
            'errors': [],
            'operation_issues': []
        }
        
        try:
            # Test file reading
            for file_path in self.required_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            f.read(1024)  # Read first 1KB
                    except Exception as e:
                        results['passed'] = False
                        results['operation_issues'].append(f"Cannot read file: {file_path} - {str(e)}")
                        
            # Test file writing
            test_file = self.errors_dir / "smoke_test_write.tmp"
            try:
                with open(test_file, 'w', encoding='utf-8') as f:
                    f.write("Smoke test write operation")
                os.remove(test_file)
            except Exception as e:
                results['passed'] = False
                results['operation_issues'].append(f"Cannot write file: {str(e)}")
                
        except Exception as e:
            results['passed'] = False
            results['errors'].append(f"Basic operations test failed: {str(e)}")
            
        if results['operation_issues']:
            results['errors'].extend(results['operation_issues'])
            
        return results
        
    def _test_security_checks(self) -> Dict:
        """Test basic security measures"""
        results = {
            'passed': True,
            'errors': [],
            'security_issues': []
        }
        
        try:
            # Check for sensitive files
            sensitive_patterns = [
                '*.pem', '*.key', '*.cert', '*.env',
                'config.json', 'secrets.json', 'credentials.json'
            ]
            
            for pattern in sensitive_patterns:
                for root, _, files in os.walk('.'):
                    for file in files:
                        if file.endswith(pattern):
                            results['passed'] = False
                            results['security_issues'].append(f"Sensitive file found: {os.path.join(root, file)}")
                            
            # Check file permissions
            for file_path in self.required_files:
                if os.path.exists(file_path):
                    mode = os.stat(file_path).st_mode
                    if mode & 0o777 > 0o644:  # More permissive than rw-r--r--
                        results['passed'] = False
                        results['security_issues'].append(f"File permissions too permissive: {file_path}")
                        
        except Exception as e:
            results['passed'] = False
            results['errors'].append(f"Security checks failed: {str(e)}")
            
        if results['security_issues']:
            results['errors'].extend(results['security_issues'])
            
        return results
        
    def _log_smoke_test_results(self, results: Dict) -> None:
        """Log smoke test results to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"""
### Smoke Test Report - {timestamp}
- Status: {'PASSED' if results['passed'] else 'FAILED'}
- Start Time: {results['start_time']}
- End Time: {results['end_time']}

Details:
"""
        
        # Add test details
        for test_name, test_results in results['details'].items():
            log_entry += f"\n#### {test_name.replace('_', ' ').title()}\n"
            log_entry += f"- Status: {'PASSED' if test_results['passed'] else 'FAILED'}\n"
            if test_results['errors']:
                log_entry += "- Errors:\n"
                for error in test_results['errors']:
                    log_entry += f"  - {error}\n"
                    
        # Add overall errors if any
        if results['errors']:
            log_entry += "\n#### Overall Errors\n"
            for error in results['errors']:
                log_entry += f"- {error}\n"
                
        with open(self.smoke_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

if __name__ == "__main__":
    runner = SmokeTestRunner()
    results = runner.run_smoke_tests()
    
    print("\nSmoke Test Results:")
    print(f"Status: {'PASSED' if results['passed'] else 'FAILED'}")
    print(f"Start Time: {results['start_time']}")
    print(f"End Time: {results['end_time']}")
    
    if results['errors']:
        print("\nErrors Found:")
        for error in results['errors']:
            print(f"- {error}") 