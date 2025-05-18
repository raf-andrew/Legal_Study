#!/usr/bin/env python3

import unittest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import tempfile

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wireframe_refinement import WireframeRefinementLoop, VersionTracker

class TestWireframeRefinementLoop(unittest.TestCase):
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

    def test_version_tracker_initialization(self):
        """Test initialization of version tracker."""
        tracker = VersionTracker(self.test_dir)
        self.assertTrue(os.path.exists(tracker.versions_dir))
        self.assertTrue(os.path.exists(tracker.screenshots_dir))
        self.assertTrue(os.path.exists(tracker.logs_dir))
        self.assertEqual(len(tracker.versions), 0)
        self.assertIsNone(tracker.current_version)

    def test_version_creation_and_tracking(self):
        """Test version creation and tracking."""
        wireframe_path = self.create_test_wireframe()
        version_id = self.loop.version_tracker.create_version(wireframe_path, "test_version")

        self.assertEqual(version_id, "v1")
        self.assertEqual(self.loop.version_tracker.current_version, "v1")

        version_meta = self.loop.version_tracker.get_version_metadata(version_id)
        self.assertEqual(version_meta["tag"], "test_version")
        self.assertTrue(os.path.exists(version_meta["html_path"]))

    def test_screenshot_tracking(self):
        """Test screenshot tracking in versions."""
        wireframe_path = self.create_test_wireframe()
        version_id = self.loop.version_tracker.create_version(wireframe_path)

        screenshot_path = os.path.join(self.loop.version_tracker.screenshots_dir, "test.png")
        viewport = {"width": 800, "height": 600, "name": "test"}

        self.loop.version_tracker.add_screenshot(version_id, screenshot_path, viewport)

        version_meta = self.loop.version_tracker.get_version_metadata(version_id)
        self.assertEqual(len(version_meta["screenshots"]), 1)
        self.assertEqual(version_meta["screenshots"][0]["path"], screenshot_path)

    def test_step_tracking(self):
        """Test step tracking in versions."""
        wireframe_path = self.create_test_wireframe()
        version_id = self.loop.version_tracker.create_version(wireframe_path)

        self.loop.version_tracker.add_step(
            version_id,
            "test_step",
            {"details": "test details"}
        )

        version_meta = self.loop.version_tracker.get_version_metadata(version_id)
        self.assertEqual(len(version_meta["steps"]), 1)
        self.assertEqual(version_meta["steps"][0]["type"], "test_step")

    @patch('subprocess.run')
    def test_refinement_loop_with_tracking(self, mock_run):
        """Test refinement loop with version tracking."""
        mock_run.return_value = MagicMock(returncode=0)

        wireframe_path = self.create_test_wireframe()
        result = self.loop.run_refinement_loop(
            wireframe_path,
            max_iterations=1,
            skip_user_interaction=True
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["iterations"], 1)

        versions = result["versions"]
        self.assertEqual(len(versions), 1)

        version_meta = versions[0]
        self.assertEqual(len(version_meta["steps"]), 4)  # creation, screenshots, analysis, report
        self.assertIn("version_creation", [step["type"] for step in version_meta["steps"]])
        self.assertIn("screenshot_capture", [step["type"] for step in version_meta["steps"]])
        self.assertIn("analysis", [step["type"] for step in version_meta["steps"]])
        self.assertIn("report_generation", [step["type"] for step in version_meta["steps"]])

    @patch('subprocess.run')
    @patch('builtins.input')
    def test_refinement_loop_with_rejection(self, mock_input, mock_run):
        """Test refinement loop with version rejection."""
        mock_run.return_value = MagicMock(returncode=0)
        mock_input.return_value = "n"  # Reject changes

        wireframe_path = self.create_test_wireframe()
        result = self.loop.run_refinement_loop(wireframe_path, max_iterations=2)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["iterations"], 1)  # Should stop after rejection
        self.assertEqual(len(result["versions"]), 1)

if __name__ == '__main__':
    unittest.main()
