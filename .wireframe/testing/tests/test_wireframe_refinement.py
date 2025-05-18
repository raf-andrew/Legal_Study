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

class TestWireframeRefinement(unittest.TestCase):
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

    def test_initialization(self):
        """Test initialization of refinement loop."""
        self.assertIsNotNone(self.loop.logger)
        self.assertEqual(self.loop.current_iteration, 0)
        self.assertIsNone(self.loop.current_wireframe)
        self.assertEqual(self.loop.analysis_results, {})
        self.assertIsNotNone(self.loop.version_tracker)
        self.assertIsNone(self.loop.original_wireframe)

    def test_version_tracking(self):
        """Test version tracking functionality."""
        wireframe_path = self.create_test_wireframe()

        # Test original wireframe tracking
        self.loop.original_wireframe = wireframe_path
        self.assertEqual(self.loop.original_wireframe, wireframe_path)

        # Test version creation
        version_id = self.loop.version_tracker.create_version(wireframe_path)
        self.assertIsNotNone(version_id)

        # Test version metadata
        metadata = self.loop.version_tracker.get_version_metadata(version_id)
        self.assertEqual(metadata["wireframe_path"], wireframe_path)
        self.assertTrue(metadata["is_original"])

    def test_improvement_tracking(self):
        """Test improvement tracking functionality."""
        wireframe_path = self.create_test_wireframe()
        version_id = self.loop.version_tracker.create_version(wireframe_path)

        # Test adding improvements
        improvement = {
            "type": "content_density",
            "suggestion": "Add more content",
            "priority": "high"
        }
        self.loop.version_tracker.add_improvement(version_id, improvement)

        # Test getting improvement history
        history = self.loop.version_tracker.get_improvement_history(version_id)
        self.assertEqual(len(history["accepted"]), 1)
        self.assertEqual(len(history["rejected"]), 0)

        # Test rejecting improvements
        self.loop.version_tracker.add_rejected_improvement(version_id, improvement)
        history = self.loop.version_tracker.get_improvement_history(version_id)
        self.assertEqual(len(history["rejected"]), 1)

    @patch('subprocess.run')
    def test_refinement_loop(self, mock_run):
        """Test refinement loop execution."""
        wireframe_path = self.create_test_wireframe()

        # Mock subprocess calls
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "content_density": 0.5,
                "line_length": 80,
                "color_count": 3
            })
        )

        # Run refinement loop
        result = self.loop.run_refinement_loop(wireframe_path, max_iterations=1, skip_user_interaction=True)

        # Verify results
        self.assertIsNotNone(result)
        self.assertIn("versions", result)
        self.assertIn("improvements", result)
        self.assertIn("screenshots", result)

    def test_report_generation(self):
        """Test report generation."""
        wireframe_path = self.create_test_wireframe()
        version_id = self.loop.version_tracker.create_version(wireframe_path)

        # Add some improvements
        improvement = {
            "type": "content_density",
            "suggestion": "Add more content",
            "priority": "high"
        }
        self.loop.version_tracker.add_improvement(version_id, improvement)

        # Generate report
        report_path = self.loop.generate_report(version_id)

        # Verify report exists and contains expected content
        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r") as f:
            content = f.read()
            self.assertIn("Refinement Report", content)
            self.assertIn("Add more content", content)
            self.assertIn("high", content)

    def test_screenshot_capture(self):
        """Test screenshot capture functionality."""
        wireframe_path = self.create_test_wireframe()
        version_id = self.loop.version_tracker.create_version(wireframe_path)

        # Capture screenshots
        screenshots = self.loop.capture_screenshots(wireframe_path, version_id)

        # Verify screenshots were created
        self.assertIsNotNone(screenshots)
        self.assertEqual(len(screenshots), 3)  # mobile, tablet, desktop

        # Verify screenshot files exist
        for screenshot in screenshots:
            self.assertTrue(os.path.exists(screenshot))

        # Verify screenshot metadata was added to version
        metadata = self.loop.version_tracker.get_version_metadata(version_id)
        self.assertIn("screenshots", metadata)
        self.assertEqual(len(metadata["screenshots"]), 3)

if __name__ == '__main__':
    unittest.main()
