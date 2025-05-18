#!/usr/bin/env python3

import os
import sys
import json
import time
import logging
import unittest
import tempfile
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_reports.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('test_reports')

class TestWireframeReports(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create temporary test environment
        cls.test_dir = tempfile.mkdtemp()
        logger.info(f"Test environment set up in {cls.test_dir}")

        # Initialize Playwright
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.context = cls.browser.new_context()
        cls.page = cls.context.new_page()

        # Load config
        config_path = Path(__file__).parent / 'config.json'
        with open(config_path) as f:
            cls.config = json.load(f)

        # Create test report
        cls._create_test_report()

    @classmethod
    def tearDownClass(cls):
        cls.context.close()
        cls.browser.close()
        cls.playwright.stop()
        logger.info("Test environment cleaned up")

    @classmethod
    def _create_test_report(cls):
        """Create a test report file for testing"""
        report_path = Path(cls.test_dir) / 'test_report.html'
        with open(report_path, 'w') as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Report</title>
                <meta name="version" content="1.0.0">
                <style>
                    .option {
                        margin: 10px;
                        padding: 10px;
                        border: 1px solid #ccc;
                        cursor: pointer;
                        role: button;
                        tabindex: 0;
                    }
                    .option.selected { background-color: #e0e0e0; }
                </style>
            </head>
            <body>
                <div id="options">
                    <div class="option" data-option-id="option1" role="button" tabindex="0">Option 1</div>
                    <div class="option" data-option-id="option2" role="button" tabindex="0">Option 2</div>
                    <div class="option" data-option-id="option3" role="button" tabindex="0">Option 3</div>
                </div>
                <script>
                    document.querySelectorAll('.option').forEach(option => {
                        option.addEventListener('click', () => {
                            const optionId = option.dataset.optionId;
                            option.classList.add('selected');
                            window.location.href = `cursor://select/${optionId}`;
                        });
                    });
                </script>
            </body>
            </html>
            """)
        cls.report_path = report_path

    def test_report_loading(self):
        """Test that reports load correctly"""
        self.page.goto(f'file://{self.report_path}')
        self.assertEqual(self.page.title(), 'Test Report')
        self.assertTrue(self.page.locator('#options').is_visible())

    def test_option_selection(self):
        """Test option selection functionality"""
        self.page.goto(f'file://{self.report_path}')

        # Click the first option
        option = self.page.locator('.option').first
        option.click()

        # Wait for the selection to be processed
        time.sleep(1)

        # Check if the option was selected
        self.assertTrue(option.evaluate('el => el.classList.contains("selected")'))

        # Log the URL for debugging
        logger.info(f"Current URL: {self.page.url}")

        # Check if the URL contains the option ID
        self.assertTrue('cursor://select/option1' in self.page.url)

    def test_report_styling(self):
        """Test report styling and layout"""
        self.page.goto(f'file://{self.report_path}')

        # Check if options are properly styled
        option = self.page.locator('.option').first
        self.assertTrue(option.is_visible())

        # Check if selected state is properly styled
        option.click()
        self.assertTrue(option.evaluate('el => el.classList.contains("selected")'))

    def test_report_responsiveness(self):
        """Test report responsiveness"""
        viewport_sizes = self.config['viewport_sizes']

        for device, size in viewport_sizes.items():
            self.page.set_viewport_size(size)
            self.page.goto(f'file://{self.report_path}')

            # Check if options are visible at this viewport size
            options = self.page.locator('.option')
            self.assertTrue(options.count() > 0)

            # Check if options are properly laid out
            for option in options.all():
                self.assertTrue(option.is_visible())

    def test_report_interaction(self):
        """Test report interaction elements"""
        self.page.goto(f'file://{self.report_path}')

        # Test clicking each option
        options = self.page.locator('.option').all()
        for option in options:
            option.click()
            self.assertTrue(option.evaluate('el => el.classList.contains("selected")'))

    def test_report_accessibility(self):
        """Test report accessibility"""
        self.page.goto(f'file://{self.report_path}')

        # Check if options have proper ARIA attributes
        options = self.page.locator('.option').all()
        for option in options:
            self.assertTrue(option.get_attribute('role') == 'button')
            self.assertTrue(option.get_attribute('tabindex') == '0')

    def test_report_performance(self):
        """Test report performance"""
        start_time = time.time()
        self.page.goto(f'file://{self.report_path}')
        load_time = time.time() - start_time

        # Check if page loads within timeout
        self.assertLess(load_time, self.config['test_timeouts']['page_load'] / 1000)

    def test_report_error_handling(self):
        """Test report error handling"""
        # Test with invalid file path
        with self.assertRaises(Exception):
            self.page.goto('file://invalid/path.html')

    def test_report_version_tracking(self):
        """Test report version tracking"""
        self.page.goto(f'file://{self.report_path}')

        # Check if version information is present
        version_info = self.page.evaluate('() => document.querySelector("meta[name=version]")?.content')
        self.assertIsNotNone(version_info)

    def test_report_screenshot_capture(self):
        """Test report screenshot capture"""
        self.page.goto(f'file://{self.report_path}')

        # Take screenshot
        screenshot_path = Path(self.test_dir) / 'screenshot.png'
        self.page.screenshot(path=str(screenshot_path))

        # Verify screenshot was created
        self.assertTrue(screenshot_path.exists())
        self.assertGreater(screenshot_path.stat().st_size, 0)

if __name__ == '__main__':
    unittest.main()
