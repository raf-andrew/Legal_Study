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

class TestCursorAnalysis(unittest.TestCase):
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
    def test_cursor_analysis_execution(self, mock_run):
        """Test execution of Cursor CLI analysis."""
        wireframe_path = self.create_test_wireframe()
        version_id = self.loop.version_tracker.create_version(wireframe_path)

        # Mock Cursor CLI response
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "content_density": 0.5,
                "line_length": 80,
                "color_count": 3
            })
        )

        # Run analysis
        result = self.loop.analyze_version(version_id)

        # Verify results
        self.assertIsNotNone(result)
        self.assertEqual(result["content_density"], 0.5)
        self.assertEqual(result["line_length"], 80)
        self.assertEqual(result["color_count"], 3)

        # Verify Cursor CLI was called correctly
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn("cursor", args)
        self.assertIn("analyze", args)
        self.assertIn(wireframe_path, args)

    @patch('subprocess.run')
    def test_cursor_analysis_error_handling(self, mock_run):
        """Test error handling when analysis fails."""
        wireframe_path = self.create_test_wireframe()
        version_id = self.loop.version_tracker.create_version(wireframe_path)

        # Mock Cursor CLI error
        mock_run.side_effect = subprocess.CalledProcessError(1, "cursor")

        # Run analysis and verify error handling
        with self.assertRaises(subprocess.CalledProcessError):
            self.loop.analyze_version(version_id)

    @patch('subprocess.run')
    def test_cursor_analysis_integration(self, mock_run):
        """Test integration of Cursor analysis with refinement loop."""
        wireframe_path = self.create_test_wireframe()

        # Mock Cursor CLI responses
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

        # Verify analysis results were used
        self.assertIsNotNone(result)
        self.assertIn("analysis_results", result)
        self.assertEqual(result["analysis_results"]["content_density"], 0.5)

    def test_cursor_analysis_config_validation(self):
        """Test validation of analysis configuration."""
        wireframe_path = self.create_test_wireframe()
        version_id = self.loop.version_tracker.create_version(wireframe_path)

        # Test with invalid configuration
        with self.assertRaises(ValueError):
            self.loop.analyze_version(version_id, config={"invalid": "config"})

        # Test with valid configuration
        config = {
            "content_density_threshold": 0.5,
            "line_length_threshold": 80,
            "color_count_threshold": 3
        }
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "content_density": 0.5,
                    "line_length": 80,
                    "color_count": 3
                })
            )
            result = self.loop.analyze_version(version_id, config=config)
            self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()
