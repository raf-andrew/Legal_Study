#!/usr/bin/env python3

import os
import sys
import logging
import time
import random
import psutil
import threading
import requests
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/chaos_test.log'),
        logging.StreamHandler()
    ]
)

class ChaosTest:
    def __init__(self):
        self.workspace_root = Path(os.getcwd())
        self.base_url = "http://localhost:8000"
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'errors': []
        }
        self.stop_flag = False
        
    def simulate_high_cpu(self, duration=5):
        """Simulate high CPU usage"""
        end_time = time.time() + duration
        while time.time() < end_time:
            _ = [i * i for i in range(1000)]
            
    def simulate_memory_pressure(self, size_mb=100):
        """Simulate memory pressure"""
        try:
            # Allocate memory
            data = [bytearray(1024 * 1024) for _ in range(size_mb)]
            time.sleep(2)  # Hold memory for 2 seconds
            return True
        except MemoryError:
            return False
            
    def simulate_disk_pressure(self, size_mb=100):
        """Simulate disk pressure"""
        try:
            temp_file = self.workspace_root / 'chaos_test.tmp'
            with open(temp_file, 'wb') as f:
                f.write(os.urandom(size_mb * 1024 * 1024))
            time.sleep(2)  # Hold file for 2 seconds
            os.remove(temp_file)
            return True
        except Exception as e:
            self.results['errors'].append(f"Disk pressure simulation failed: {str(e)}")
            return False
            
    def simulate_network_latency(self):
        """Simulate network latency"""
        time.sleep(random.uniform(0.1, 0.5))
        
    def test_under_cpu_pressure(self):
        """Test system under CPU pressure"""
        try:
            # Start CPU pressure in a separate thread
            with ThreadPoolExecutor(max_workers=2) as executor:
                cpu_future = executor.submit(self.simulate_high_cpu)
                
                # Make API requests
                response = requests.get(f"{self.base_url}/health")
                assert response.status_code == 200
                
            self.results['tests']['cpu_pressure'] = {
                'status': 'pass',
                'response_time': response.elapsed.total_seconds()
            }
            return True
        except Exception as e:
            self.results['tests']['cpu_pressure'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"CPU pressure test failed: {str(e)}")
            return False
            
    def test_under_memory_pressure(self):
        """Test system under memory pressure"""
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                memory_future = executor.submit(self.simulate_memory_pressure)
                
                # Make API requests
                response = requests.get(f"{self.base_url}/health")
                assert response.status_code == 200
                
            self.results['tests']['memory_pressure'] = {
                'status': 'pass',
                'response_time': response.elapsed.total_seconds()
            }
            return True
        except Exception as e:
            self.results['tests']['memory_pressure'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Memory pressure test failed: {str(e)}")
            return False
            
    def test_under_disk_pressure(self):
        """Test system under disk pressure"""
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                disk_future = executor.submit(self.simulate_disk_pressure)
                
                # Make API requests
                response = requests.get(f"{self.base_url}/health")
                assert response.status_code == 200
                
            self.results['tests']['disk_pressure'] = {
                'status': 'pass',
                'response_time': response.elapsed.total_seconds()
            }
            return True
        except Exception as e:
            self.results['tests']['disk_pressure'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Disk pressure test failed: {str(e)}")
            return False
            
    def test_under_network_latency(self):
        """Test system under network latency"""
        try:
            original_sleep = time.sleep
            time.sleep = self.simulate_network_latency
            
            # Make API requests
            response = requests.get(f"{self.base_url}/health")
            assert response.status_code == 200
            
            self.results['tests']['network_latency'] = {
                'status': 'pass',
                'response_time': response.elapsed.total_seconds()
            }
            return True
        except Exception as e:
            self.results['tests']['network_latency'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Network latency test failed: {str(e)}")
            return False
        finally:
            time.sleep = original_sleep
            
    def test_concurrent_load(self):
        """Test system under concurrent load"""
        try:
            def make_request():
                response = requests.get(f"{self.base_url}/health")
                return response.status_code == 200
                
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(50)]
                results = [f.result() for f in futures]
                
            assert all(results)
            
            self.results['tests']['concurrent_load'] = {
                'status': 'pass',
                'requests_completed': len(results)
            }
            return True
        except Exception as e:
            self.results['tests']['concurrent_load'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Concurrent load test failed: {str(e)}")
            return False
            
    def test_resource_limits(self):
        """Test system behavior near resource limits"""
        try:
            # Get current resource usage
            process = psutil.Process()
            
            # Memory usage
            memory_percent = process.memory_percent()
            
            # CPU usage
            cpu_percent = process.cpu_percent(interval=1)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            self.results['tests']['resource_limits'] = {
                'status': 'pass',
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent,
                'disk_percent': disk_percent
            }
            return True
        except Exception as e:
            self.results['tests']['resource_limits'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Resource limits test failed: {str(e)}")
            return False
            
    def save_results(self):
        """Save test results to file"""
        results_file = self.workspace_root / '.testing' / 'chaos_test_results.json'
        import json
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
    def run(self):
        """Run all chaos tests"""
        logging.info("Starting chaos tests...")
        
        success = True
        success &= self.test_under_cpu_pressure()
        success &= self.test_under_memory_pressure()
        success &= self.test_under_disk_pressure()
        success &= self.test_under_network_latency()
        success &= self.test_concurrent_load()
        success &= self.test_resource_limits()
        
        self.save_results()
        
        if success:
            logging.info("All chaos tests passed")
        else:
            logging.error("Some chaos tests failed")
            for error in self.results['errors']:
                logging.error(error)
                
        return success

if __name__ == '__main__':
    test = ChaosTest()
    success = test.run()
    sys.exit(0 if success else 1) 