import os
import sys
import time
import threading
import queue
import random
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from click.testing import CliRunner
from legal_study.console.cli import cli, check, version

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(".logs/stress_test.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

class StressTest:
    """Stress test class for console commands."""
    
    def __init__(self, num_threads: int = 10, duration: int = 60):
        self.num_threads = num_threads
        self.duration = duration
        self.runner = CliRunner()
        self.results_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
        }

    def worker(self, worker_id: int):
        """Worker function for stress testing."""
        while not self.stop_event.is_set():
            try:
                # Choose random command and options
                command = random.choice(['check', 'version'])
                options = self.generate_random_options()
                
                # Execute command and measure time
                start_time = time.time()
                if command == 'check':
                    result = self.runner.invoke(check, options)
                else:
                    result = self.runner.invoke(version)
                end_time = time.time()
                
                # Record results
                response_time = end_time - start_time
                success = result.exit_code == 0
                
                self.results_queue.put({
                    'worker_id': worker_id,
                    'command': command,
                    'options': options,
                    'success': success,
                    'response_time': response_time,
                    'exit_code': result.exit_code,
                    'output': result.output,
                })
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                self.results_queue.put({
                    'worker_id': worker_id,
                    'error': str(e),
                    'success': False,
                })

    def generate_random_options(self) -> List[str]:
        """Generate random command options."""
        options = []
        
        # Random checks
        if random.random() < 0.7:
            checks = ['directories', 'configurations', 'security', 'monitoring']
            for _ in range(random.randint(1, len(checks))):
                check = random.choice(checks)
                options.extend(['--check', check])
        
        # Random report generation
        if random.random() < 0.3:
            options.append('--report')
        
        # Random log level
        if random.random() < 0.2:
            log_level = random.choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'])
            options.extend(['--log-level', log_level])
        
        # Random output format
        if random.random() < 0.5:
            output_format = random.choice(['json', 'yaml', 'text'])
            options.extend(['--output', output_format])
        
        return options

    def process_results(self):
        """Process and analyze test results."""
        while not self.results_queue.empty():
            result = self.results_queue.get()
            self.metrics['total_requests'] += 1
            
            if result.get('success', False):
                self.metrics['successful_requests'] += 1
            else:
                self.metrics['failed_requests'] += 1
            
            if 'response_time' in result:
                self.metrics['response_times'].append(result['response_time'])

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate test statistics."""
        response_times = self.metrics['response_times']
        return {
            'total_requests': self.metrics['total_requests'],
            'successful_requests': self.metrics['successful_requests'],
            'failed_requests': self.metrics['failed_requests'],
            'success_rate': (self.metrics['successful_requests'] / self.metrics['total_requests'] * 100 
                           if self.metrics['total_requests'] > 0 else 0),
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'requests_per_second': self.metrics['total_requests'] / self.duration,
        }

    def run(self):
        """Run the stress test."""
        logger.info(f"Starting stress test with {self.num_threads} threads for {self.duration} seconds")
        
        # Start worker threads
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []
            for i in range(self.num_threads):
                futures.append(executor.submit(self.worker, i))
            
            # Wait for duration
            time.sleep(self.duration)
            
            # Stop workers
            self.stop_event.set()
            
            # Wait for all workers to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Worker thread error: {e}")
        
        # Process results
        self.process_results()
        stats = self.calculate_statistics()
        
        # Log results
        logger.info("Stress test completed")
        logger.info("Statistics:")
        for key, value in stats.items():
            logger.info(f"{key}: {value}")
        
        return stats

def main():
    """Main function to run stress test."""
    # Run stress test with different configurations
    configs = [
        {'num_threads': 10, 'duration': 30},
        {'num_threads': 50, 'duration': 30},
        {'num_threads': 100, 'duration': 30},
    ]
    
    results = []
    for config in configs:
        logger.info(f"Running stress test with configuration: {config}")
        test = StressTest(**config)
        stats = test.run()
        results.append({
            'config': config,
            'stats': stats
        })
    
    # Compare results
    logger.info("\nTest Results Comparison:")
    for result in results:
        logger.info(f"\nConfiguration: {result['config']}")
        logger.info("Statistics:")
        for key, value in result['stats'].items():
            logger.info(f"{key}: {value}")

if __name__ == "__main__":
    main() 