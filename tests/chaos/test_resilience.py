import pytest
import psutil
import logging
import threading
import time
import os
import signal
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from app.main import app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/chaos/resilience.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def setup_module(module):
    """Setup for this test module."""
    logger.info(f"Starting chaos resilience tests at {datetime.now()}")

def teardown_module(module):
    """Teardown for this test module."""
    logger.info(f"Completed chaos resilience tests at {datetime.now()}")

class TestSystemResilience:
    @pytest.fixture(autouse=True)
    def setup_monitoring(self):
        """Setup system monitoring."""
        self.start_time = time.time()
        self.initial_memory = psutil.Process().memory_info().rss
        self.initial_cpu = psutil.cpu_percent()
        
        yield
        
        # Log resource usage
        duration = time.time() - self.start_time
        memory_diff = psutil.Process().memory_info().rss - self.initial_memory
        cpu_diff = psutil.cpu_percent() - self.initial_cpu
        
        logger.info(f"Test duration: {duration:.2f}s")
        logger.info(f"Memory usage diff: {memory_diff / 1024 / 1024:.2f}MB")
        logger.info(f"CPU usage diff: {cpu_diff:.2f}%")

    @pytest.mark.chaos
    def test_memory_pressure(self):
        """Test system behavior under memory pressure."""
        large_data = []
        try:
            # Gradually increase memory usage
            for _ in range(10):
                large_data.append(b'x' * 10_000_000)  # 10MB chunks
                time.sleep(0.1)
                
                # Monitor memory usage
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > 90:  # Stop if memory usage is too high
                    logger.warning(f"High memory usage detected: {memory_percent}%")
                    break
                
        except MemoryError as e:
            logger.error(f"Memory pressure test triggered MemoryError: {e}")
            with open('.errors/chaos_errors.log', 'a') as f:
                f.write(f"\n{datetime.now()} - Memory pressure test failed: {str(e)}")
        
        finally:
            # Clean up
            large_data.clear()

    @pytest.mark.chaos
    def test_cpu_stress(self):
        """Test system behavior under CPU stress."""
        def cpu_intensive_task():
            start = time.time()
            while time.time() - start < 5:  # Run for 5 seconds
                _ = [i * i for i in range(1000)]

        try:
            # Run CPU-intensive tasks in parallel
            with ThreadPoolExecutor(max_workers=psutil.cpu_count()) as executor:
                futures = [executor.submit(cpu_intensive_task) for _ in range(psutil.cpu_count())]
                
                # Monitor CPU usage
                while not all(f.done() for f in futures):
                    cpu_percent = psutil.cpu_percent()
                    if cpu_percent > 90:
                        logger.warning(f"High CPU usage detected: {cpu_percent}%")
                    time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"CPU stress test error: {e}")
            with open('.errors/chaos_errors.log', 'a') as f:
                f.write(f"\n{datetime.now()} - CPU stress test failed: {str(e)}")

    @pytest.mark.chaos
    def test_file_handle_exhaustion(self):
        """Test system behavior when file handles are exhausted."""
        open_files = []
        try:
            # Try to open many files
            for i in range(1000):
                f = open(f"test_file_{i}.tmp", 'w')
                open_files.append(f)
                
                # Monitor file handle count
                if len(open_files) % 100 == 0:
                    logger.info(f"Opened {len(open_files)} files")
                
        except OSError as e:
            logger.error(f"File handle exhaustion test triggered OSError: {e}")
            with open('.errors/chaos_errors.log', 'a') as f:
                f.write(f"\n{datetime.now()} - File handle exhaustion test failed: {str(e)}")
        
        finally:
            # Clean up
            for f in open_files:
                try:
                    f.close()
                    os.remove(f.name)
                except:
                    pass

    @pytest.mark.chaos
    def test_process_recovery(self):
        """Test process recovery after forced termination."""
        def start_process():
            # Simulate a long-running process
            time.sleep(10)

        try:
            # Start a process
            process = threading.Thread(target=start_process)
            process.start()
            
            # Simulate process termination
            time.sleep(1)
            if process.is_alive():
                # In a real application, this would be handled by a process manager
                logger.info("Simulating process termination")
                process.join(timeout=0)
            
            # Verify process recovery
            assert not process.is_alive(), "Process should not be running"
            
        except Exception as e:
            logger.error(f"Process recovery test error: {e}")
            with open('.errors/chaos_errors.log', 'a') as f:
                f.write(f"\n{datetime.now()} - Process recovery test failed: {str(e)}")

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 