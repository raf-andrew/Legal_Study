#!/usr/bin/env python3

import unittest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import tempfile
import subprocess

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wireframe_refinement import WireframeRefinementLoop, VersionTracker

class TestFeatureTests(unittest.TestCase):
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

    def create_test_wireframe(self, content: str = "<html><body>Test</body></html>") -> str:
        """Create a test wireframe file."""
        wireframe_path = os.path.join(self.test_dir, "test_wireframe.html")
        with open(wireframe_path, "w") as f:
            f.write(content)
        return wireframe_path

    @patch('subprocess.run')
    def test_feature_tests(self, mock_run):
        """Test feature test execution."""
        wireframe_path = self.create_test_wireframe()
        version_id = self.loop.version_tracker.create_version(wireframe_path)

        # Mock subprocess calls
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )

        # Run feature tests
        tests = self.loop._run_feature_tests(version_id)

        # Verify test results
        self.assertGreater(len(tests), 0)
        self.assertTrue(any(test["name"] == "Wireframe Load" for test in tests))
        self.assertTrue(any(test["name"] == "HTML Validation" for test in tests))
        self.assertTrue(any(test["name"].startswith("Responsive Design") for test in tests))

    @patch('subprocess.run')
    def test_feature_tests_failure(self, mock_run):
        """Test feature test failure handling."""
        wireframe_path = self.create_test_wireframe()
        version_id = self.loop.version_tracker.create_version(wireframe_path)

        # Mock subprocess calls to fail
        mock_run.side_effect = subprocess.CalledProcessError(1, "cursor", stderr=b"Test failed")

        # Run feature tests
        tests = self.loop._run_feature_tests(version_id)

        # Verify test results
        self.assertGreater(len(tests), 0)
        self.assertTrue(any(test["status"] == "fail" for test in tests))

    def test_feature_tests_html_generation(self):
        """Test HTML generation for feature test results."""
        tests = [
            {
                "name": "Test 1",
                "status": "pass",
                "message": "Test passed"
            },
            {
                "name": "Test 2",
                "status": "fail",
                "message": "Test failed"
            }
        ]

        html = self.loop._generate_feature_tests_html(tests)

        # Verify HTML content
        self.assertIn("Test 1", html)
        self.assertIn("Test 2", html)
        self.assertIn("pass", html)
        self.assertIn("fail", html)
        self.assertIn("Test passed", html)
        self.assertIn("Test failed", html)

    @patch('subprocess.run')
    def test_diff_view_generation(self, mock_run):
        """Test diff view generation."""
        # Create test versions
        wireframe_path = self.create_test_wireframe()
        version_id1 = self.loop.version_tracker.create_version(wireframe_path)
        version_id2 = self.loop.version_tracker.create_version(wireframe_path)

        # Mock diff output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="+ Added line\n- Removed line\n Unchanged line",
            stderr=""
        )

        # Generate diff view
        diff_html = self.loop._generate_diff_view(version_id1, version_id2)

        # Verify diff HTML
        self.assertIn("Added line", diff_html)
        self.assertIn("Removed line", diff_html)
        self.assertIn("Unchanged line", diff_html)
        self.assertIn("diff-line added", diff_html)
        self.assertIn("diff-line removed", diff_html)

    @patch('subprocess.run')
    def test_diff_view_failure(self, mock_run):
        """Test diff view generation failure."""
        # Create test versions
        wireframe_path = self.create_test_wireframe()
        version_id1 = self.loop.version_tracker.create_version(wireframe_path)
        version_id2 = self.loop.version_tracker.create_version(wireframe_path)

        # Mock diff failure
        mock_run.side_effect = subprocess.CalledProcessError(1, "cursor", stderr=b"Diff failed")

        # Generate diff view
        diff_html = self.loop._generate_diff_view(version_id1, version_id2)

        # Verify error message
        self.assertIn("Failed to generate diff", diff_html)

if __name__ == '__main__':
    unittest.main()
