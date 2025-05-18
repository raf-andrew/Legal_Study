#!/usr/bin/env python3

import unittest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import tempfile
import time
import psutil
import threading

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wireframe_refinement import WireframeRefinementLoop

class TestPerformance(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.loop = WireframeRefinementLoop()
        self.loop.setup(self.test_dir)

        # Create test directories
        os.makedirs(os.path.join(self.test_dir, "versions"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "screenshots"), exist_ok=True)
        os.makedirs(os.path.join(self.test_dir, "logs"), exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        try:
            shutil.rmtree(self.test_dir)
        except PermissionError:
            # Handle Windows file locking
            pass

    def create_test_wireframe(self, name="test.html"):
        """Create a test wireframe file."""
        wireframe_dir = Path(self.test_dir) / ".wireframe"
        wireframe_dir.mkdir(parents=True, exist_ok=True)
        wireframe_path = wireframe_dir / name
        with open(wireframe_path, 'w') as f:
            f.write("<html><body><h1>Test Wireframe</h1></body></html>")
        return str(wireframe_path)

    @patch('subprocess.run')
    def test_cpu_utilization(self, mock_run):
        """Test CPU utilization during operations."""
        mock_run.return_value = MagicMock(returncode=0)

        wireframe_path = self.create_test_wireframe()
        process = psutil.Process()
        cpu_percent_before = process.cpu_percent()

        self.loop.run_refinement_loop(wireframe_path, max_iterations=1, skip_user_interaction=True)

        cpu_percent_after = process.cpu_percent()
        self.assertLess(cpu_percent_after - cpu_percent_before, 50)  # Max 50% CPU increase

    @patch('subprocess.run')
    def test_memory_usage(self, mock_run):
        """Test memory usage during operations."""
        mock_run.return_value = MagicMock(returncode=0)

        wireframe_path = self.create_test_wireframe()
        process = psutil.Process()
        memory_before = process.memory_info().rss

        self.loop.run_refinement_loop(wireframe_path, max_iterations=1, skip_user_interaction=True)

        memory_after = process.memory_info().rss
        self.assertLess(memory_after - memory_before, 100 * 1024 * 1024)  # Max 100MB increase

    @patch('subprocess.run')
    def test_disk_io(self, mock_run):
        """Test disk I/O during operations."""
        mock_run.return_value = MagicMock(returncode=0)

        wireframe_path = self.create_test_wireframe()
        io_counters_before = psutil.disk_io_counters()

        self.loop.run_refinement_loop(wireframe_path, max_iterations=1, skip_user_interaction=True)

        io_counters_after = psutil.disk_io_counters()
        self.assertLess(
            io_counters_after.write_bytes - io_counters_before.write_bytes,
            10 * 1024 * 1024  # Max 10MB written
        )

    @patch('subprocess.run')
    def test_network_operations(self, mock_run):
        """Test network operations during browser testing."""
        mock_run.return_value = MagicMock(returncode=0)

        wireframe_path = self.create_test_wireframe()
        net_io_before = psutil.net_io_counters()

        self.loop.run_refinement_loop(wireframe_path, max_iterations=1, skip_user_interaction=True)

        net_io_after = psutil.net_io_counters()
        self.assertLess(
            net_io_after.bytes_sent - net_io_before.bytes_sent,
            1024 * 1024  # Max 1MB sent
        )

    @patch('subprocess.run')
    def test_concurrent_operations(self, mock_run):
        """Test performance during concurrent operations."""
        mock_run.return_value = MagicMock(returncode=0)

        wireframe_path = self.create_test_wireframe()
        threads = []

        def run_operation():
            self.loop.run_refinement_loop(wireframe_path, max_iterations=1, skip_user_interaction=True)

        # Start multiple threads
        for _ in range(3):
            thread = threading.Thread(target=run_operation)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        self.assertTrue(all(thread.is_alive() is False for thread in threads))

    @patch('subprocess.run')
    def test_resource_cleanup(self, mock_run):
        """Test resource cleanup after operations."""
        mock_run.return_value = MagicMock(returncode=0)

        wireframe_path = self.create_test_wireframe()
        process = psutil.Process()

        # Run operations
        self.loop.run_refinement_loop(wireframe_path, max_iterations=1, skip_user_interaction=True)

        # Check resource cleanup
        self.assertEqual(len(self.loop.version_history), 1)
        self.assertIsNone(self.loop.current_wireframe)
        self.assertEqual(self.loop.current_iteration, 0)
        self.assertEqual(len(self.loop.analysis_results), 0)

if __name__ == '__main__':
    unittest.main()
