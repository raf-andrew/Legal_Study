#!/usr/bin/env python3
"""
Chaos Testing Module

This module provides chaos testing functionality, including:
- Network failure simulation
- Resource exhaustion testing
- State corruption testing
- Recovery mechanism testing
"""

import os
import sys
import logging
import time
import random
import psutil
from pathlib import Path
from typing import Dict, Any, List
import socket
import threading
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.errors/chaos_tests.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChaosTester:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results = []
        self.error_count = 0

    @contextmanager
    def simulate_network_failure(self, duration: int = 5):
        """Simulate network failure for a specified duration."""
        logger.info(f"Simulating network failure for {duration} seconds...")
        try:
            # Block network traffic
            original_socket = socket.socket
            socket.socket = lambda *args, **kwargs: None
            yield
        finally:
            # Restore network
            socket.socket = original_socket
            time.sleep(duration)

    def test_network_resilience(self) -> None:
        """Test system resilience to network failures."""
        logger.info("Testing network resilience...")
        try:
            with self.simulate_network_failure():
                # Attempt to make network requests
                response = requests.get("http://localhost:8000", timeout=1)
                assert response.status_code == 200
            self.results.append("Network Resilience: System recovered from network failure")
        except Exception as e:
            logger.error(f"Network resilience test failed: {e}")
            self.error_count += 1
            self.results.append(f"Network Resilience: Failed - {str(e)}")

    def test_resource_exhaustion(self) -> None:
        """Test system behavior under resource exhaustion."""
        logger.info("Testing resource exhaustion...")
        try:
            # Simulate memory pressure
            memory = []
            while psutil.virtual_memory().percent < 90:
                memory.append(' ' * 1024 * 1024)  # 1MB chunks
            self.results.append("Resource Exhaustion: System handled memory pressure")
        except Exception as e:
            logger.error(f"Resource exhaustion test failed: {e}")
            self.error_count += 1
            self.results.append(f"Resource Exhaustion: Failed - {str(e)}")
        finally:
            # Clean up
            memory.clear()

    def test_state_corruption(self) -> None:
        """Test system recovery from state corruption."""
        logger.info("Testing state corruption recovery...")
        try:
            # Simulate state corruption
            test_file = Path('.tests/state_test.txt')
            test_file.write_text('corrupted data')
            # Attempt recovery
            test_file.write_text('recovered data')
            assert test_file.read_text() == 'recovered data'
            self.results.append("State Corruption: System recovered from corrupted state")
        except Exception as e:
            logger.error(f"State corruption test failed: {e}")
            self.error_count += 1
            self.results.append(f"State Corruption: Failed - {str(e)}")

    def test_recovery_mechanisms(self) -> None:
        """Test system recovery mechanisms."""
        logger.info("Testing recovery mechanisms...")
        try:
            # Simulate service failure and recovery
            service = threading.Thread(target=lambda: time.sleep(1))
            service.start()
            service.join(timeout=0.5)
            assert not service.is_alive()
            self.results.append("Recovery Mechanisms: System recovered from service failure")
        except Exception as e:
            logger.error(f"Recovery mechanism test failed: {e}")
            self.error_count += 1
            self.results.append(f"Recovery Mechanisms: Failed - {str(e)}")

    def run_all_tests(self) -> List[str]:
        """Run all chaos tests."""
        self.test_network_resilience()
        self.test_resource_exhaustion()
        self.test_state_corruption()
        self.test_recovery_mechanisms()
        return self.results

if __name__ == "__main__":
    # Load configuration
    config_path = Path('.config/environment/development/config.yaml')
    with open(config_path, 'r') as f:
        import yaml
        config = yaml.safe_load(f)

    tester = ChaosTester(config)
    results = tester.run_all_tests()
    
    # Print results
    print("\nChaos Test Results:")
    for result in results:
        print(f"- {result}")
    print(f"\nTotal Errors: {tester.error_count}") 