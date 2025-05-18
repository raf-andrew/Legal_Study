#!/usr/bin/env python3

import unittest
import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import tempfile
import stat
import re
import hashlib
import ssl
import socket
import urllib.request
import urllib.error

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wireframe_refinement import WireframeRefinementLoop, RefinementState, RefinementStatus

class TestSecurity(unittest.TestCase):
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

    def test_file_permissions(self):
        """Test file permissions."""
        test_file = os.path.join(self.test_dir, "test.html")
        with open(test_file, 'w') as f:
            f.write("<html><body>Test</body></html>")

        # Set permissions to 644 (rw-r--r--)
        os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

        # Validate file permissions
        self.assertTrue(self.loop.validate_file(test_file))

        # Test with overly permissive file
        os.chmod(test_file, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        with self.assertRaises(ValueError):
            self.loop.validate_file(test_file)

    def test_file_extension_validation(self):
        """Test file extension validation."""
        # Test allowed extension
        test_file = os.path.join(self.test_dir, "test.html")
        with open(test_file, 'w') as f:
            f.write("<html><body>Test</body></html>")
        self.assertTrue(self.loop.validate_file(test_file))

        # Test disallowed extension
        test_file = os.path.join(self.test_dir, "test.exe")
        with open(test_file, 'w') as f:
            f.write("test")
        with self.assertRaises(ValueError):
            self.loop.validate_file(test_file)

    def test_file_size_limits(self):
        """Test file size limits."""
        test_file = os.path.join(self.test_dir, "test.html")
        with open(test_file, 'w') as f:
            f.write("<html><body>Test</body></html>")
        self.assertTrue(self.loop.validate_file(test_file))

        # Create a large file
        with open(test_file, 'w') as f:
            f.write("x" * (10 * 1024 * 1024))  # 10MB
        with self.assertRaises(ValueError):
            self.loop.validate_file(test_file)

    def test_ssl_configuration(self):
        """Test SSL configuration."""
        ssl_context = self.loop.configure_ssl()
        self.assertIsInstance(ssl_context, ssl.SSLContext)
        self.assertEqual(ssl_context.protocol, ssl.PROTOCOL_TLS)
        self.assertTrue(ssl_context.verify_mode, ssl.CERT_REQUIRED)

    def test_input_sanitization(self):
        """Test input sanitization."""
        malicious_input = """
        <script>alert('xss')</script>
        ../../../etc/passwd
        ' OR '1'='1
        <?php echo 'test'; ?>
        """
        sanitized = self.loop.sanitize_input(malicious_input)
        self.assertNotIn("<script>", sanitized)
        self.assertNotIn("../../../", sanitized)
        self.assertNotIn("' OR '1'='1", sanitized)
        self.assertNotIn("<?php", sanitized)

    def test_secure_communication(self):
        """Test secure communication settings."""
        ssl_context = self.loop.configure_ssl()
        self.assertTrue(ssl_context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(ssl_context.check_hostname)
        self.assertIn(ssl.PROTOCOL_TLS, ssl_context.protocol)

if __name__ == '__main__':
    unittest.main()
