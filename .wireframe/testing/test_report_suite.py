#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import unittest
from pathlib import Path
import shutil
import tempfile
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser, expect

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('report_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TestReportGeneration(unittest.TestCase):
    """Test suite for report generation and UI/UX functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.test_dir = Path(tempfile.mkdtemp())
        cls.reports_dir = cls.test_dir / "reports"
        cls.screenshots_dir = cls.test_dir / "screenshots"
        cls.logs_dir = cls.test_dir / "logs"

        # Create necessary directories
        for directory in [cls.reports_dir, cls.screenshots_dir, cls.logs_dir]:
            directory.mkdir(exist_ok=True)

        # Load configuration
        config_path = Path(__file__).parent / "config.json"
        with open(config_path) as f:
            cls.config = json.load(f)

        # Initialize Playwright
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            headless=cls.config["browser"]["headless"],
            slow_mo=cls.config["browser"]["slow_mo"]
        )
        cls.context = cls.browser.new_context()
        cls.page = cls.context.new_page()

        logger.info(f"Test environment set up in {cls.test_dir}")

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        cls.context.close()
        cls.browser.close()
        cls.playwright.stop()
        shutil.rmtree(cls.test_dir)
        logger.info("Test environment cleaned up")

    def setUp(self):
        """Set up each test case."""
        self.page = self.context.new_page()
        self.iteration = getattr(self, '_testMethodName', '').split('_')[-1]
        logger.info(f"Starting test iteration {self.iteration}")

    def tearDown(self):
        """Clean up after each test case."""
        self.page.close()
        logger.info(f"Completed test iteration {self.iteration}")

    def test_report_generation_1(self):
        """Test basic report generation and structure."""
        report_path = self.reports_dir / f"report_{self.iteration}.html"
        self._generate_test_report(report_path)

        # Load and verify report
        self.page.goto(f"file://{report_path}")
        self.assertEqual(self.page.title(), f"Test Report {self.iteration}")
        self.assertTrue(self.page.locator('#content').is_visible())

    def test_ui_interaction_1(self):
        """Test UI interaction elements."""
        report_path = self.reports_dir / f"report_{self.iteration}.html"
        self._generate_test_report(report_path)

        self.page.goto(f"file://{report_path}")

        # Test button interactions
        button = self.page.locator('.action-button').first
        button.click()
        expect(button).to_have_class(/active/)

    def test_responsive_design_1(self):
        """Test responsive design across different viewport sizes."""
        report_path = self.reports_dir / f"report_{self.iteration}.html"
        self._generate_test_report(report_path)

        self.page.goto(f"file://{report_path}")

        for viewport_name, viewport in self.config["viewport_sizes"].items():
            self.page.set_viewport_size(viewport)
            # Verify responsive layout
            container = self.page.locator('.container')
            style = self.page.evaluate("(el) => window.getComputedStyle(el)", container)
            if viewport["width"] < 800:
                self.assertLessEqual(int(style["width"].replace("px", "")), viewport["width"])

    def test_accessibility_1(self):
        """Test accessibility features."""
        report_path = self.reports_dir / f"report_{self.iteration}.html"
        self._generate_test_report(report_path)

        self.page.goto(f"file://{report_path}")

        # Check ARIA attributes
        elements = self.page.locator('[role]').all()
        self.assertGreater(len(elements), 0)

        # Check keyboard navigation
        self.page.keyboard.press('Tab')
        focused = self.page.evaluate('document.activeElement')
        self.assertIsNotNone(focused)

    def test_performance_1(self):
        """Test report performance metrics."""
        report_path = self.reports_dir / f"report_{self.iteration}.html"
        self._generate_test_report(report_path)

        start_time = time.time()
        self.page.goto(f"file://{report_path}")
        load_time = time.time() - start_time

        self.assertLess(load_time, self.config['test_timeouts']['page_load'] / 1000)

    def _generate_test_report(self, report_path: Path):
        """Generate a test report with various UI elements."""
        with open(report_path, 'w') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Report {self.iteration}</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    .container {{
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .action-button {{
                        padding: 10px 20px;
                        background: #007bff;
                        color: white;
                        border: none;
                        cursor: pointer;
                    }}
                    .action-button.active {{
                        background: #0056b3;
                    }}
                    @media (max-width: 800px) {{
                        .container {{
                            padding: 10px;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="container" role="main">
                    <h1>Test Report {self.iteration}</h1>
                    <div id="content">
                        <button class="action-button" role="button" tabindex="0">Test Button</button>
                        <div class="test-content">
                            <p>This is test content for iteration {self.iteration}</p>
                        </div>
                    </div>
                </div>
                <script>
                    document.querySelector('.action-button').addEventListener('click', function() {{
                        this.classList.add('active');
                    }});
                </script>
            </body>
            </html>
            """)

if __name__ == "__main__":
    unittest.main()
