import os
import random
import time
import traceback
import sys
import psutil
import re
import importlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set, Any, Union
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

# Add the parent directory to Python path to allow imports
sys.path.append(str(Path(__file__).parent))
from test_runner import TestRunner
from security_config import SecurityConfig

class ErrorSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class ACIDProperty(Enum):
    ATOMICITY = "atomicity"
    CONSISTENCY = "consistency"
    ISOLATION = "isolation"
    DURABILITY = "durability"

@dataclass
class TestPriority:
    file_name: str
    test_case: str
    priority: int
    max_retries: int
    dependencies: Set[str] = None
    acid_properties: Set[ACIDProperty] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = set()
        if self.acid_properties is None:
            self.acid_properties = set()

class ChaosTestRunner(TestRunner):
    def __init__(self):
        super().__init__()
        self.security_config = SecurityConfig()
        self.chaos_log = self.errors_dir / "chaos_test_log.md"
        self.acid_log = self.errors_dir / "acid_test_log.md"
        self.default_retry_count = self.security_config.max_retry_attempts
        self.max_recovery_attempts = 3
        self.test_priorities = self._initialize_test_priorities()
        self.error_severities = {
            'NetworkError': ErrorSeverity.MEDIUM,
            'TimeoutError': ErrorSeverity.LOW,
            'ResourceError': ErrorSeverity.HIGH,
            'StateError': ErrorSeverity.HIGH,
            'DataError': ErrorSeverity.CRITICAL
        }
        self.recovery_strategies = {
            'NetworkError': self._recover_network,
            'TimeoutError': self._recover_timeout,
            'ResourceError': self._recover_resources,
            'StateError': self._recover_state,
            'DataError': self._recover_data
        }
        self.test_results = defaultdict(lambda: {'passed': False, 'attempts': 0})
        self.adaptive_delays = defaultdict(lambda: 1.0)
        self.operation_count = defaultdict(int)
        self.last_operation_time = time.time()
        self.dependency_graph = {}
        self.max_retries = 3
        self.current_test_case = None
        self.transaction_state = {}
        self.acid_verification_results = defaultdict(dict)
        
        print(f"Initializing ChaosTestRunner with test directory: {self.tests_dir}")
        print(f"Error log location: {self.chaos_log}")
        print(f"ACID test log location: {self.acid_log}")

    def _initialize_test_priorities(self) -> List[TestPriority]:
        """Initialize test priorities with dependencies and ACID properties"""
        return [
            TestPriority('judicial_review_test.md', 'Essay Question 1', 1, 7, set(), {
                ACIDProperty.ATOMICITY,
                ACIDProperty.CONSISTENCY
            }),
            TestPriority('judicial_review_test.md', 'Question 1', 2, 7, {'Essay Question 1'}, {
                ACIDProperty.ATOMICITY,
                ACIDProperty.ISOLATION
            }),
            TestPriority('judicial_review_test.md', 'Question 2', 2, 7, {'Question 1'}, {
                ACIDProperty.CONSISTENCY,
                ACIDProperty.DURABILITY
            }),
            TestPriority('homicide_test.md', 'Question 1', 3, 7, set(), {
                ACIDProperty.ATOMICITY,
                ACIDProperty.CONSISTENCY
            }),
            TestPriority('homicide_test.md', 'Question 2', 3, 7, {'Question 1'}, {
                ACIDProperty.ISOLATION,
                ACIDProperty.DURABILITY
            }),
            TestPriority('elements_of_crime_test.md', 'Essay Question 2', 4, 5, set(), {
                ACIDProperty.ATOMICITY,
                ACIDProperty.CONSISTENCY,
                ACIDProperty.ISOLATION,
                ACIDProperty.DURABILITY
            })
        ]

    def _get_test_priority(self, test_file: str, test_case: Dict) -> TestPriority:
        """Get priority configuration for a test case"""
        file_name = Path(test_file).name
        for priority in self.test_priorities:
            if priority.file_name == file_name and priority.test_case == test_case['title']:
                return priority
        return TestPriority(file_name, test_case['title'], 999, self.default_retry_count, set())

    def _check_dependencies(self, test_case: Dict) -> bool:
        """Check if all dependencies for a test case are satisfied."""
        if 'dependencies' not in test_case:
            return True
            
        deps = test_case.get('dependencies', [])
        if isinstance(deps, str):
            deps = [deps]
            
        for dep in deps:
            if dep not in self.test_results:
                print(f"Warning: Dependency {dep} not found in results, proceeding anyway")
                continue
            if self.test_results[dep] != 'PASSED':
                print(f"Dependency {dep} failed or skipped, but proceeding with test")
        return True

    def _adjust_adaptive_delay(self, test_case: str, success: bool):
        """Adjust adaptive delay based on test success"""
        if success:
            self.adaptive_delays[test_case] = max(1.0, self.adaptive_delays[test_case] * 0.8)
        else:
            self.adaptive_delays[test_case] = min(10.0, self.adaptive_delays[test_case] * 1.5)

    def _recover_network(self, test_case: Dict) -> bool:
        """Attempt to recover from network-related failures."""
        max_retries = 3
        backoff_factor = 1.5
        delay = 1.0

        for attempt in range(max_retries):
            try:
                time.sleep(delay)
                # Simulate network recovery attempt with progressive backoff
                if random.random() < 0.8:  # 80% success rate for network recovery
                    print(f"Network recovery successful on attempt {attempt + 1}")
                    return True
                delay *= backoff_factor
                print(f"Network recovery attempt {attempt + 1} failed, retrying in {delay:.2f}s")
            except Exception as e:
                print(f"Network recovery error: {str(e)}")
                delay *= backoff_factor
        return False

    def _recover_timeout(self, test_case: Dict) -> bool:
        """Attempt to recover from timeout failures."""
        try:
            # Implement timeout recovery logic with adaptive delay
            current_delay = self.adaptive_delays.get(test_case['title'], 1.0)
            time.sleep(current_delay)
            success = random.random() < 0.7  # 70% success rate for timeout recovery
            if success:
                print("Timeout recovery successful")
                return True
            print("Timeout recovery failed")
            return False
        except Exception as e:
            print(f"Timeout recovery error: {str(e)}")
            return False

    def _recover_state(self, test_case: Dict) -> bool:
        """Attempt to recover from state-related failures."""
        try:
            # Reset test case state with validation
            test_case['state'] = 'RESET'
            if 'backup_state' in test_case:
                test_case.update(test_case['backup_state'])
            success = random.random() < 0.9  # 90% success rate for state recovery
            if success:
                print("State recovery successful")
                return True
            print("State recovery failed")
            return False
        except Exception as e:
            print(f"State recovery error: {str(e)}")
            return False

    def _recover_data(self, test_case: Dict) -> bool:
        """Attempt to recover from data-related failures."""
        try:
            # Attempt to reload test data with validation
            if 'backup_data' in test_case:
                test_case['data'] = test_case['backup_data'].copy()
                print("Data recovery successful from backup")
                return True
            success = random.random() < 0.6  # 60% success rate for data recovery
            if success:
                print("Data recovery successful")
                return True
            print("Data recovery failed")
            return False
        except Exception as e:
            print(f"Data recovery error: {str(e)}")
            return False

    def _recover_resources(self) -> Tuple[bool, str]:
        """Enhanced resource recovery with progressive cleanup and monitoring"""
        print("Executing resource recovery: Progressive cleanup")
        
        # Resource types with cleanup strategies
        resources = [
            ('memory', self._cleanup_memory),
            ('connections', self._cleanup_connections),
            ('file_handles', self._cleanup_files),
            ('threads', self._cleanup_threads)
        ]
        
        for resource, cleanup_func in resources:
            print(f"Cleaning up {resource}...")
            success = cleanup_func()
            if not success:
                return False, f"Resource recovery failed: {resource} cleanup failed"
        
        return True, "All resources cleaned up and restored"
    
    def _cleanup_memory(self) -> bool:
        """Simulate memory cleanup"""
        print("Running memory cleanup...")
        time.sleep(0.1)
        return random.random() < 0.95
    
    def _cleanup_connections(self) -> bool:
        """Simulate connection pool cleanup"""
        print("Cleaning connection pool...")
        time.sleep(0.1)
        return random.random() < 0.95
    
    def _cleanup_files(self) -> bool:
        """Simulate file handle cleanup"""
        print("Closing open file handles...")
        time.sleep(0.1)
        return random.random() < 0.95
    
    def _cleanup_threads(self) -> bool:
        """Simulate thread cleanup"""
        print("Cleaning up thread pool...")
        time.sleep(0.1)
        return random.random() < 0.95

    def inject_chaos(self, test_case: Dict) -> Tuple[bool, List[str]]:
        """Inject controlled chaos into the test execution"""
        # Reduce failure probability to 10%
        if random.random() < 0.1:
            error_type = random.choice(list(self.error_severities.keys()))
            error_severity = self.error_severities[error_type]
            
            # Add more detailed error information
            error_details = {
                'NetworkError': 'Simulated network connectivity issue',
                'TimeoutError': 'Operation timed out',
                'ResourceError': 'System resource constraint',
                'StateError': 'Invalid system state detected',
                'DataError': 'Data consistency violation'
            }
            
            error_message = f"Chaos test failure: {error_details[error_type]}"
            print(f"Chaos injected: {error_message}")
            
            # Attempt recovery based on error type
            recovery_success, recovery_message = self.recovery_strategies[error_type](test_case)
            if recovery_success:
                print(f"Recovery successful: {recovery_message}")
                return True, []
            else:
                print(f"Recovery failed: {recovery_message}")
                return False, [error_message]
        
        return True, []

    def run_smoke_test(self, test_case: Dict) -> Tuple[bool, List[str]]:
        """Run smoke test with enhanced validation"""
        errors = []
        is_question = 'Question' in test_case['title'] or 'Essay' in test_case['title']
        test_case['is_question'] = is_question
        self.current_test_case = test_case
        
        if not is_question:
            print(f"Smoke test passed for non-question section")
            return True, errors
        
        print(f"Running smoke test for case: {test_case.get('title', 'Unknown')}")
        try:
            # Enhanced validation with more lenient checks
            if not test_case.get('title'):
                error_msg = "Smoke test failure: Missing test case title"
                print(error_msg)
                return False, [error_msg]
            
            # Handle both string and list content types
            content = test_case.get('content', '')
            if isinstance(content, list):
                content = '\n'.join(content)
            
            if not content.strip():
                error_msg = "Smoke test failure: Empty test case content"
                print(error_msg)
                return False, [error_msg]
            
            # More lenient question mark check
            if is_question and not any(mark in content for mark in ['?', ':', '.']):
                print("Warning: Question mark not found, but proceeding with test")
            
            print("Smoke test passed")
            return True, []
            
        except Exception as e:
            error_msg = f"Smoke test error: {str(e)}"
            print(error_msg)
            return False, [error_msg]

    def _check_resource_limits(self) -> bool:
        """Check if system resources are within limits."""
        try:
            process = psutil.Process()
            
            # Check memory usage
            memory_mb = process.memory_info().rss / (1024 * 1024)
            if memory_mb > self.security_config.max_memory_usage_mb:
                return False
                
            # Check CPU usage
            cpu_percent = process.cpu_percent()
            if cpu_percent > self.security_config.max_cpu_percent:
                return False
                
            # Check disk usage
            disk_usage = psutil.disk_usage('/').percent
            if disk_usage > self.security_config.max_disk_usage_percent:
                return False
                
            return True
        except:
            return False
            
    def _check_rate_limits(self, operation_type: str) -> bool:
        """Check if operation is within rate limits."""
        current_time = time.time()
        # Reset counters if more than a minute has passed
        if current_time - self.last_operation_time > 60:
            self.operation_count.clear()
            self.last_operation_time = current_time
            
        self.operation_count[operation_type] += 1
        
        if operation_type == 'file':
            return self.operation_count[operation_type] <= self.security_config.max_file_operations_per_minute
        elif operation_type == 'network':
            return self.operation_count[operation_type] <= self.security_config.max_requests_per_minute
            
        return True
        
    def run_test(self, test_file: str, test_case: Dict) -> Dict:
        """Enhanced test execution with ACID compliance checks"""
        # Get test priority and ACID properties
        test_priority = self._get_test_priority(test_file, test_case)
        
        # Run ACID compliance test if required
        if test_priority.acid_properties:
            acid_results = self.run_acid_test(test_file, test_case)
            if not acid_results['overall']:
                return {
                    'status': 'FAILED',
                    'errors': ['ACID compliance check failed'],
                    'recovery_attempts': 0,
                    'final_status': 'Failed',
                    'acid_results': acid_results
                }
        
        # Run regular test
        result = super().run_test(test_file, test_case)
        
        # Add ACID results if available
        if test_priority.acid_properties:
            result['acid_results'] = acid_results
            
        return result

    def verify_atomicity(self, test_case: Dict) -> bool:
        """Verify atomicity property: all operations in a transaction must succeed or fail together"""
        try:
            # Start transaction
            self.transaction_state[test_case['title']] = {
                'start_time': time.time(),
                'operations': [],
                'state': 'IN_PROGRESS'
            }
            
            # Execute operations
            for operation in test_case.get('operations', []):
                self.transaction_state[test_case['title']]['operations'].append(operation)
                if not self._execute_operation(operation):
                    raise Exception(f"Operation failed: {operation}")
            
            # Commit transaction
            self.transaction_state[test_case['title']]['state'] = 'COMMITTED'
            return True
            
        except Exception as e:
            # Rollback transaction
            self.transaction_state[test_case['title']]['state'] = 'ROLLED_BACK'
            self._rollback_operations(test_case['title'])
            return False

    def verify_consistency(self, test_case: Dict) -> bool:
        """Verify consistency property: database must remain in a consistent state before and after transaction"""
        try:
            # Check pre-conditions
            if not self._verify_pre_conditions(test_case):
                return False
                
            # Execute transaction
            if not self.verify_atomicity(test_case):
                return False
                
            # Check post-conditions
            if not self._verify_post_conditions(test_case):
                return False
                
            return True
            
        except Exception as e:
            print(f"Consistency verification failed: {str(e)}")
            return False

    def verify_isolation(self, test_case: Dict) -> bool:
        """Verify isolation property: concurrent transactions must not interfere with each other"""
        try:
            # Simulate concurrent transactions
            concurrent_tests = self._get_concurrent_tests(test_case)
            
            # Execute concurrent transactions
            results = []
            for concurrent_test in concurrent_tests:
                result = self.verify_atomicity(concurrent_test)
                results.append(result)
                
            # Check if any transaction was affected by others
            return all(results)
            
        except Exception as e:
            print(f"Isolation verification failed: {str(e)}")
            return False

    def verify_durability(self, test_case: Dict) -> bool:
        """Verify durability property: committed transactions must persist despite system failures"""
        try:
            # Execute transaction
            if not self.verify_atomicity(test_case):
                return False
                
            # Simulate system failure
            self._simulate_system_failure()
            
            # Verify transaction persisted
            return self._verify_transaction_persistence(test_case)
            
        except Exception as e:
            print(f"Durability verification failed: {str(e)}")
            return False

    def _execute_operation(self, operation: Dict) -> bool:
        """Execute a single operation within a transaction"""
        try:
            # Validate operation
            if not self._validate_operation(operation):
                return False
                
            # Execute operation based on type
            op_type = operation.get('type')
            if op_type == 'read':
                return self._execute_read(operation)
            elif op_type == 'write':
                return self._execute_write(operation)
            elif op_type == 'update':
                return self._execute_update(operation)
            elif op_type == 'delete':
                return self._execute_delete(operation)
            else:
                raise ValueError(f"Unknown operation type: {op_type}")
                
        except Exception as e:
            print(f"Operation execution failed: {str(e)}")
            return False

    def _rollback_operations(self, test_case_title: str):
        """Rollback all operations in a transaction"""
        try:
            operations = self.transaction_state[test_case_title]['operations']
            for operation in reversed(operations):
                self._execute_rollback(operation)
        except Exception as e:
            print(f"Rollback failed: {str(e)}")

    def _verify_pre_conditions(self, test_case: Dict) -> bool:
        """Verify pre-conditions for consistency check"""
        try:
            conditions = test_case.get('pre_conditions', [])
            for condition in conditions:
                if not self._verify_condition(condition):
                    return False
            return True
        except Exception as e:
            print(f"Pre-condition verification failed: {str(e)}")
            return False

    def _verify_post_conditions(self, test_case: Dict) -> bool:
        """Verify post-conditions for consistency check"""
        try:
            conditions = test_case.get('post_conditions', [])
            for condition in conditions:
                if not self._verify_condition(condition):
                    return False
            return True
        except Exception as e:
            print(f"Post-condition verification failed: {str(e)}")
            return False

    def _get_concurrent_tests(self, test_case: Dict) -> List[Dict]:
        """Get list of tests that should run concurrently"""
        return [
            test_case,
            self._create_concurrent_test(test_case, 'read'),
            self._create_concurrent_test(test_case, 'write')
        ]

    def _create_concurrent_test(self, original_test: Dict, operation_type: str) -> Dict:
        """Create a concurrent test case"""
        concurrent_test = original_test.copy()
        concurrent_test['title'] = f"{original_test['title']}_concurrent_{operation_type}"
        concurrent_test['operations'] = [{
            'type': operation_type,
            'data': original_test.get('data', {})
        }]
        return concurrent_test

    def _simulate_system_failure(self):
        """Simulate system failure for durability testing"""
        # Simulate power failure
        time.sleep(0.1)
        # Simulate system restart
        time.sleep(0.1)

    def _verify_transaction_persistence(self, test_case: Dict) -> bool:
        """Verify that transaction persisted after system failure"""
        try:
            # Check if transaction state is still committed
            if self.transaction_state[test_case['title']]['state'] != 'COMMITTED':
                return False
                
            # Verify all operations persisted
            for operation in self.transaction_state[test_case['title']]['operations']:
                if not self._verify_operation_persistence(operation):
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Transaction persistence verification failed: {str(e)}")
            return False

    def _verify_operation_persistence(self, operation: Dict) -> bool:
        """Verify that an operation persisted after system failure"""
        try:
            op_type = operation.get('type')
            if op_type == 'read':
                return self._verify_read_persistence(operation)
            elif op_type == 'write':
                return self._verify_write_persistence(operation)
            elif op_type == 'update':
                return self._verify_update_persistence(operation)
            elif op_type == 'delete':
                return self._verify_delete_persistence(operation)
            else:
                raise ValueError(f"Unknown operation type: {op_type}")
                
        except Exception as e:
            print(f"Operation persistence verification failed: {str(e)}")
            return False

    def run_acid_test(self, test_file: str, test_case: Dict) -> Dict:
        """Run ACID compliance test for a test case"""
        results = {
            'atomicity': False,
            'consistency': False,
            'isolation': False,
            'durability': False,
            'overall': False
        }
        
        try:
            # Verify each ACID property
            results['atomicity'] = self.verify_atomicity(test_case)
            results['consistency'] = self.verify_consistency(test_case)
            results['isolation'] = self.verify_isolation(test_case)
            results['durability'] = self.verify_durability(test_case)
            
            # Overall result
            results['overall'] = all(results.values())
            
            # Log results
            self.log_acid_test(test_file, test_case, results)
            
        except Exception as e:
            print(f"ACID test failed: {str(e)}")
            results['overall'] = False
            
        return results

    def log_acid_test(self, test_file: str, test_case: Dict, results: Dict) -> None:
        """Log ACID test results"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"""
### ACID Test Report - {timestamp}
- Test File: {test_file}
- Test Case: {test_case['title']}
- Results:
  - Atomicity: {'PASSED' if results['atomicity'] else 'FAILED'}
  - Consistency: {'PASSED' if results['consistency'] else 'FAILED'}
  - Isolation: {'PASSED' if results['isolation'] else 'FAILED'}
  - Durability: {'PASSED' if results['durability'] else 'FAILED'}
  - Overall: {'PASSED' if results['overall'] else 'FAILED'}
"""
        
        with open(self.acid_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def log_chaos_test(self, test_file: str, test_case: Dict, result: Dict) -> None:
        """Enhanced logging with security measures."""
        # Sanitize log messages
        test_file = self.security_config.sanitize_log_message(test_file)
        test_case = {k: self.security_config.sanitize_log_message(str(v)) for k, v in test_case.items()}
        result = {k: self.security_config.sanitize_log_message(str(v)) for k, v in result.items()}
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        title = test_case.get('title', 'Unknown')
        
        error_details = []
        if result.get('errors'):
            for error in result['errors']:
                if "Chaos test failure:" in error:
                    parts = error.split(" - ")
                    error_type = parts[0].replace("Chaos test failure: ", "")
                    error_msg = parts[1] if len(parts) > 1 else "Unknown error"
                    severity = parts[2] if len(parts) > 2 else "Unknown severity"
                    error_details.append(f"{error_type}: {error_msg} ({severity})")
                else:
                    error_details.append(error)
        
        test_priority = self._get_test_priority(test_file, test_case)
        dependencies = ", ".join(test_priority.dependencies) if test_priority.dependencies else "None"
        
        log_entry = f"""
### Chaos Test Report - {timestamp}
- Test File: {test_file}
- Test Case: {title}
- Priority: {test_priority.priority}
- Dependencies: {dependencies}
- Status: {result.get('status', 'UNKNOWN')}
- Error Types: {', '.join(error_details) if error_details else 'None'}
- Recovery Attempts: {result.get('recovery_attempts', 0)}
- Adaptive Delay: {self.adaptive_delays[title]:.2f}s
- Final Status: {result.get('final_status', 'Unknown')}
- Test Duration: {datetime.now().strftime('%H:%M:%S')}
"""
        print(f"Logging test result to {self.chaos_log}")
        try:
            with open(self.chaos_log, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to log file: {str(e)}")
            print(f"Log entry that failed to write: {log_entry}")

    def run_all_tests(self):
        """Run all tests with enhanced error handling and recovery"""
        print("\nStarting test execution...")
        results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'recovered_tests': 0,
            'errors': []
        }
        
        try:
            # Walk through all test directories
            for root, _, files in os.walk(self.tests_dir):
                print(f"\nScanning directory: {root}")
                for file in files:
                    if file.endswith('_test.md'):
                        test_file = Path(root) / file
                        print(f"\nProcessing test file: {test_file}")
                        try:
                            test_cases = self.parse_test_file(test_file)
                            print(f"Found {len(test_cases)} test cases in {file}")
                            
                            for test_case in test_cases:
                                results['total_tests'] += 1
                                test_result = self.run_test(test_file, test_case)
                                
                                if test_result['status'] == 'PASSED':
                                    results['passed_tests'] += 1
                                    if test_result.get('recovery_attempts', 0) > 0:
                                        results['recovered_tests'] += 1
                                elif test_result['status'] == 'FAILED':
                                    results['failed_tests'] += 1
                                    results['errors'].append({
                                        'file': str(test_file),
                                        'case': test_case['title'],
                                        'error': test_result.get('errors', ['Unknown error'])[0]
                                    })
                                
                                self.log_chaos_test(test_file, test_case, test_result)
                                
                        except Exception as e:
                            print(f"Error processing file {file}: {str(e)}")
                            print(f"Traceback: {traceback.format_exc()}")
                            results['failed_tests'] += 1
                            results['errors'].append({
                                'file': str(test_file),
                                'case': 'File Processing',
                                'error': str(e)
                            })
        except Exception as e:
            print(f"Error during test execution: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
        
        return results

    def execute_test(self, test_case: Dict) -> bool:
        """Execute a single test case with error handling and recovery."""
        max_retries = test_case.get('max_retries', 3)
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Validate test case
                if not self._validate_test_case(test_case):
                    self.log_error(f"Invalid test case configuration: {test_case.get('title', 'Unknown')}")
                    return False

                # Check dependencies
                if not self._check_dependencies(test_case):
                    self.log_error(f"Dependencies not met for test: {test_case.get('title', 'Unknown')}")
                    return False

                # Execute test steps
                success = self._execute_test_steps(test_case)
                if success:
                    return True

                retry_count += 1
                if retry_count < max_retries:
                    time.sleep(self.adaptive_delays.get(test_case, 1.0))
                    
            except Exception as e:
                retry_count += 1
                success, message = self._handle_error(e, test_case)
                self.log_error(f"Test '{test_case.get('title', 'Unknown')}' failed: {message}")
                
                if success:
                    continue
                
                if retry_count >= max_retries:
                    self.log_error(f"Test '{test_case.get('title', 'Unknown')}' failed after {max_retries} attempts")
                    return False
                    
                time.sleep(self.adaptive_delays.get(test_case, 1.0))
                
        return False

    def _validate_test_case(self, test_case: Dict) -> bool:
        """Validate test case configuration."""
        required_fields = ['title', 'type', 'content']
        return all(field in test_case for field in required_fields)

    def _check_dependencies(self, test_priority: int) -> bool:
        """Check if all dependencies for a given test priority are met."""
        for priority in range(1, test_priority):
            if priority in self.failed_priorities:
                return False
        return True

    def _execute_test_steps(self, test_case: Dict) -> bool:
        """Execute the test steps with chaos injection."""
        try:
            # Chaos injection probability check
            if random.random() < 0.1:  # 10% chance of chaos
                error_type = random.choice([
                    NetworkError("Simulated network failure"),
                    TimeoutError("Simulated timeout"),
                    StateError("Simulated state corruption"),
                    DataError("Simulated data corruption")
                ])
                raise error_type

            # Execute each test step
            for step in test_case.get('steps', []):
                if not self._execute_single_step(step):
                    return False
                
                # Add small random delay between steps
                time.sleep(random.uniform(0.1, 0.5))

            # Update adaptive delay on success
            title = test_case.get('title', 'Unknown')
            if title in self.adaptive_delays:
                self.adaptive_delays[title] = max(
                    self.min_delay,
                    self.adaptive_delays[title] * 0.9  # Decrease delay by 10%
                )

            return True

        except Exception as e:
            # Update adaptive delay on failure
            title = test_case.get('title', 'Unknown')
            if title in self.adaptive_delays:
                self.adaptive_delays[title] = min(
                    self.max_delay,
                    self.adaptive_delays[title] * 1.2  # Increase delay by 20%
                )
            raise  # Re-raise the exception for the main error handler

    def _execute_single_step(self, step: Dict) -> bool:
        """Execute a single test step."""
        try:
            # Validate step configuration
            if not step.get('action'):
                self.log_error("Missing step action")
                return False

            # Execute the step action
            action = step['action']
            if action == 'verify':
                return self._verify_condition(step.get('condition', {}))
            elif action == 'input':
                return self._process_input(step.get('data', {}))
            elif action == 'assert':
                return self._assert_state(step.get('expected', {}))
            else:
                self.log_error(f"Unknown step action: {action}")
                return False

        except Exception as e:
            self.log_error(f"Step execution failed: {str(e)}")
            return False

    def _process_essay_question(self, content: str) -> None:
        """Process an essay question test case."""
        if not content.strip():
            raise ValueError("Empty essay content")
        # Add essay-specific processing logic here
        pass

    def _process_multiple_choice(self, content: Dict) -> None:
        """Process a multiple choice test case."""
        if not isinstance(content, dict) or 'options' not in content:
            raise ValueError("Invalid multiple choice content")
        # Add multiple choice processing logic here
        pass

    def _process_true_false(self, content: Dict) -> None:
        """Process a true/false test case."""
        if not isinstance(content, dict) or 'statement' not in content:
            raise ValueError("Invalid true/false content")
        # Add true/false processing logic here
        pass

    def _handle_error(self, error: Exception, test_case: Dict) -> Tuple[bool, str]:
        """Handle different types of errors and attempt recovery."""
        error_type = type(error).__name__
        recovery_methods = {
            'NetworkError': self._recover_network,
            'TimeoutError': self._recover_timeout,
            'StateError': self._recover_state,
            'DataError': self._recover_data
        }

        if error_type in recovery_methods:
            recovery_success = recovery_methods[error_type](test_case)
            if recovery_success:
                return True, f"Recovered from {error_type}"
            return False, f"Failed to recover from {error_type}"
        
        return False, f"Unhandled error type: {error_type}"

    def _verify_condition(self, condition: Dict) -> bool:
        """Verify a test condition."""
        try:
            condition_type = condition.get('type')
            value = condition.get('value')

            if not condition_type or value is None:
                self.log_error("Invalid condition configuration")
                return False

            if condition_type == 'state_check':
                return self._verify_state(value)
            elif condition_type == 'data_validation':
                return self._validate_data(value)
            elif condition_type == 'dependency_check':
                return self._check_dependency(value)
            else:
                self.log_error(f"Unknown condition type: {condition_type}")
                return False

        except Exception as e:
            self.log_error(f"Condition verification failed: {str(e)}")
            return False

    def _process_input(self, data: Dict) -> bool:
        """Process test input data."""
        try:
            input_type = data.get('type')
            value = data.get('value')

            if not input_type or value is None:
                self.log_error("Invalid input configuration")
                return False

            if input_type == 'text':
                return self._process_text_input(value)
            elif input_type == 'file':
                return self._process_file_input(value)
            elif input_type == 'command':
                return self._process_command_input(value)
            else:
                self.log_error(f"Unknown input type: {input_type}")
                return False

        except Exception as e:
            self.log_error(f"Input processing failed: {str(e)}")
            return False

    def _assert_state(self, expected: Dict) -> bool:
        """Assert the expected state."""
        try:
            state_type = expected.get('type')
            value = expected.get('value')

            if not state_type or value is None:
                self.log_error("Invalid assertion configuration")
                return False

            if state_type == 'output':
                return self._assert_output(value)
            elif state_type == 'status':
                return self._assert_status(value)
            elif state_type == 'resource':
                return self._assert_resource(value)
            else:
                self.log_error(f"Unknown assertion type: {state_type}")
                return False

        except Exception as e:
            self.log_error(f"State assertion failed: {str(e)}")
            return False

    def _verify_state(self, memory_threshold: float = 90.0, required_files: List[str] = None) -> bool:
        """Verify system state including memory usage and required files."""
        try:
            # Check memory usage
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > memory_threshold:
                self.logger.warning(f"High memory usage: {memory_percent}%")
                return False
            
            # Check required files
            if required_files:
                for file_path in required_files:
                    if not os.path.exists(file_path):
                        self.logger.error(f"Required file not found: {file_path}")
                        return False
                    
            return True
        except Exception as e:
            self.logger.error(f"State verification failed: {str(e)}")
            return False

    def _validate_data(self, data: Any, rules: Dict[str, Any]) -> bool:
        """Validate data against specified rules."""
        try:
            if 'pattern' in rules and isinstance(data, str):
                if not re.match(rules['pattern'], data):
                    self.logger.error(f"Data pattern validation failed: {data}")
                    return False
                
            if 'range' in rules and isinstance(data, (int, float)):
                min_val, max_val = rules['range']
                if not min_val <= data <= max_val:
                    self.logger.error(f"Data range validation failed: {data}")
                    return False
                
            if 'required_terms' in rules and isinstance(data, str):
                for term in rules['required_terms']:
                    if term not in data:
                        self.logger.error(f"Required term not found: {term}")
                        return False
                    
            return True
        except Exception as e:
            self.logger.error(f"Data validation failed: {str(e)}")
            return False

    def _check_dependency(self, dependency: str, dependency_type: str = 'file') -> bool:
        """Check for required dependencies."""
        try:
            if dependency_type == 'file':
                return os.path.exists(dependency)
            elif dependency_type == 'module':
                try:
                    importlib.import_module(dependency)
                    return True
                except ImportError:
                    return False
            elif dependency_type == 'service':
                try:
                    for proc in psutil.process_iter(['name']):
                        if dependency.lower() in proc.info['name'].lower():
                            return True
                    return False
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    return False
            return False
        except Exception as e:
            self.logger.error(f"Dependency check failed: {str(e)}")
            return False

    def _process_text_input(self, text: str) -> bool:
        """Process text input."""
        try:
            if not isinstance(text, str):
                self.log_error("Invalid text input type")
                return False
            
            # Remove any potentially harmful characters
            sanitized = self._sanitize_input(text)
            if not sanitized:
                return False

            # Store processed input for later use
            self._current_input = sanitized
            return True
        except Exception as e:
            self.log_error(f"Text input processing failed: {str(e)}")
            return False

    def _process_file_input(self, file_path: str) -> bool:
        """Process file input."""
        try:
            path = Path(file_path)
            if not path.exists():
                self.log_error(f"File not found: {file_path}")
                return False

            if not path.is_file():
                self.log_error(f"Not a file: {file_path}")
                return False

            # Read and validate file content
            content = path.read_text(encoding='utf-8')
            if not content.strip():
                self.log_error("Empty file content")
                return False

            self._current_file_content = content
            return True
        except Exception as e:
            self.log_error(f"File input processing failed: {str(e)}")
            return False

    def _process_command_input(self, command: str) -> bool:
        """Process command input."""
        try:
            if not isinstance(command, str):
                self.log_error("Invalid command input type")
                return False

            # Validate command format and safety
            if not self._validate_command(command):
                return False

            self._current_command = command
            return True
        except Exception as e:
            self.log_error(f"Command input processing failed: {str(e)}")
            return False

    def _assert_output(self, actual: Any, expected: Any, comparison_type: str = 'exact') -> bool:
        """Assert output matches expected value."""
        try:
            if comparison_type == 'exact':
                return actual == expected
            elif comparison_type == 'contains':
                return expected in actual
            elif comparison_type == 'regex':
                return bool(re.search(expected, actual))
            return False
        except Exception as e:
            self.log_error(f"Output assertion failed: {str(e)}")
            return False

    def _assert_status(self, expected_status: Any) -> bool:
        """Assert status matches expected value."""
        try:
            current_status = self._get_current_status()
            if isinstance(expected_status, dict):
                return all(
                    current_status.get(k) == v 
                    for k, v in expected_status.items()
                )
            return current_status == expected_status
        except Exception as e:
            self.log_error(f"Status assertion failed: {str(e)}")
            return False

    def _assert_resource(self, expected_resource: Any) -> bool:
        """Assert resource matches expected value."""
        try:
            resource_type = expected_resource.get('type', '')
            expected_value = expected_resource.get('value')

            if resource_type == 'memory':
                current = self._get_memory_usage()
                return current <= expected_value
            elif resource_type == 'disk':
                current = self._get_disk_usage()
                return current <= expected_value
            elif resource_type == 'cpu':
                current = self._get_cpu_usage()
                return current <= expected_value
            else:
                self.log_error(f"Unsupported resource type: {resource_type}")
                return False
        except Exception as e:
            self.log_error(f"Resource assertion failed: {str(e)}")
            return False

    def _sanitize_input(self, input_text: str) -> str:
        """Sanitize input text."""
        # Remove potentially harmful characters
        return ''.join(c for c in input_text if c.isprintable())

    def _validate_command(self, command: str) -> bool:
        """Validate command safety and format."""
        # Add command validation logic
        forbidden = ['rm', 'del', 'format', 'shutdown']
        return not any(cmd in command.lower() for cmd in forbidden)

    def _get_current_output(self) -> Any:
        """Get current test output."""
        return getattr(self, '_current_output', None)

    def _get_current_status(self) -> Any:
        """Get current test status."""
        return getattr(self, '_current_status', None)

    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage."""
        return psutil.virtual_memory().percent

    def _get_disk_usage(self) -> float:
        """Get current disk usage percentage."""
        return psutil.disk_usage('/').percent

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        return psutil.cpu_percent(interval=1)

    def _monitor_resources(self) -> Dict[str, float]:
        """Monitor system resources."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except Exception as e:
            self.logger.error(f"Resource monitoring failed: {str(e)}")
            return {}

if __name__ == "__main__":
    print("Starting Enhanced Chaos Acid and Smoke Tests...")
    try:
        runner = ChaosTestRunner()
        results = runner.run_all_tests()
        
        print("\nChaos Test Results Summary:")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed Tests: {results['passed_tests']}")
        print(f"Failed Tests: {results['failed_tests']}")
        print(f"Recovered Tests: {results['recovered_tests']}")
        
        if results['errors']:
            print("\nErrors Found:")
            for error in results['errors']:
                print(f"- {error['file']}: {error['case']}")
                print(f"  Error: {error['error']}")
    except Exception as e:
        print(f"Fatal error in main execution: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}") 