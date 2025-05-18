#!/usr/bin/env python3

from pathlib import Path
# Ensure logs directory exists before configuring logging
Path('.wireframe/testing/logs').mkdir(parents=True, exist_ok=True)

import os
import sys
import json
import time
import logging
import unittest
from datetime import datetime
from playwright.sync_api import sync_playwright, expect

from test_data_generator import TestDataGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.wireframe/testing/logs/test_suite.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class TestWireframeRefinement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment before running tests."""
        cls.test_dir = Path(__file__).parent
        cls.results_dir = cls.test_dir / 'results'
        cls.screenshots_dir = cls.test_dir / 'screenshots'
        cls.logs_dir = cls.test_dir / 'logs'

        # Create necessary directories
        for directory in [cls.results_dir, cls.screenshots_dir, cls.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Load test configuration using absolute path
        config_path = cls.test_dir / 'test_config.json'
        with open(config_path, 'r') as f:
            cls.config = json.load(f)

        # Initialize test data generator
        cls.data_generator = TestDataGenerator()

        # Generate test report
        cls.test_report = cls.data_generator.generate_test_report()

        # Initialize Playwright
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(
            headless=cls.config['browser']['headless'],
            slow_mo=cls.config['browser']['slow_mo']
        )

        logging.info("Test environment setup completed")

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after running tests."""
        cls.browser.close()
        cls.playwright.stop()
        logging.info("Test environment cleanup completed")

    def setUp(self):
        """Set up each test case."""
        self.context = self.browser.new_context(
            viewport=self.config['viewport_sizes']['desktop']
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.config['test_timeouts']['page_load'])

        # Load the test report
        self.page.goto(f"file://{os.path.abspath(self.test_report['html_path'])}")
        logging.info(f"Test case setup completed: {self._testMethodName}")

    def tearDown(self):
        """Clean up after each test case."""
        self.context.close()
        logging.info(f"Test case cleanup completed: {self._testMethodName}")

    def test_report_loading(self):
        """Test that the report loads correctly."""
        # Check if the page title is correct
        expect(self.page).to_have_title(self.test_report['data']['metadata']['title'])

        # Check if all sections are present
        sections = self.test_report['data']['content']['sections']
        for section in sections:
            section_element = self.page.locator(f"#{section['id']}")
            expect(section_element).to_be_visible()
            expect(section_element.locator("h2")).to_have_text(section['title'])

    def test_option_selection(self):
        """Test the option selection functionality."""
        options = self.test_report['data']['content']['options']

        # Test clicking each option
        for option in options:
            option_element = self.page.locator(f"[data-option-id='{option['id']}']")

            # Click the option
            option_element.click()

            # Verify the option is selected
            expect(option_element).to_have_class("option selected")

            # Verify other options are not selected
            for other_option in options:
                if other_option['id'] != option['id']:
                    other_element = self.page.locator(f"[data-option-id='{other_option['id']}']")
                    expect(other_element).not_to_have_class("option selected")

    def test_report_responsiveness(self):
        """Test the report's responsiveness across different viewport sizes."""
        viewport_sizes = self.config['viewport_sizes']

        for device, size in viewport_sizes.items():
            # Set viewport size
            self.page.set_viewport_size(size)

            # Take screenshot
            screenshot_path = self.screenshots_dir / f"responsive_{device}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.page.screenshot(path=str(screenshot_path))

            # Verify content is visible
            expect(self.page.locator("body")).to_be_visible()

            # Verify options are clickable
            option = self.test_report['data']['content']['options'][0]
            option_element = self.page.locator(f"[data-option-id='{option['id']}']")
            expect(option_element).to_be_visible()
            option_element.click()
            expect(option_element).to_have_class("option selected")

    def test_report_accessibility(self):
        """Test the report's accessibility features."""
        # Check if all interactive elements have proper ARIA roles
        options = self.page.locator(".option")
        for i in range(options.count()):
            option = options.nth(i)
            expect(option).to_have_attribute("role", "button")
            expect(option).to_have_attribute("tabindex", "0")

        # Check if all images have alt text
        images = self.page.locator("img")
        for i in range(images.count()):
            image = images.nth(i)
            expect(image).to_have_attribute("alt")

        # Check if all sections have proper heading hierarchy
        sections = self.page.locator(".section")
        for i in range(sections.count()):
            section = sections.nth(i)
            expect(section.locator("h2")).to_be_visible()

    def test_report_performance(self):
        """Test the report's performance metrics."""
        # Measure page load time
        start_time = time.time()
        self.page.goto(f"file://{os.path.abspath(self.test_report['html_path'])}")
        load_time = time.time() - start_time

        # Verify load time is within acceptable range
        self.assertLess(load_time, self.config['test_timeouts']['page_load'] / 1000)

        # Measure interaction time
        option = self.test_report['data']['content']['options'][0]
        start_time = time.time()
        self.page.locator(f"[data-option-id='{option['id']}']").click()
        interaction_time = time.time() - start_time

        # Verify interaction time is within acceptable range
        self.assertLess(interaction_time, 0.5)  # 500ms threshold

    def test_report_error_handling(self):
        """Test the report's error handling capabilities."""
        # Test with invalid option ID
        invalid_option = self.page.locator("[data-option-id='invalid_option']")
        expect(invalid_option).to_have_count(0)

        # Test with invalid section ID
        invalid_section = self.page.locator("#invalid_section")
        expect(invalid_section).to_have_count(0)

    def test_report_metrics_display(self):
        """Test the display of metrics in the report."""
        metrics = self.test_report['data']['content']['metrics']

        # Check performance metrics
        performance_card = self.page.locator(".metric-card").first
        expect(performance_card.locator("h3")).to_have_text("Performance")
        expect(performance_card).to_contain_text(f"Load Time: {metrics['performance']['load_time']:.2f}s")

        # Check accessibility metrics
        accessibility_card = self.page.locator(".metric-card").nth(1)
        expect(accessibility_card.locator("h3")).to_have_text("Accessibility")
        expect(accessibility_card).to_contain_text(f"Score: {metrics['accessibility']['score']}/100")

        # Check responsiveness metrics
        responsiveness_card = self.page.locator(".metric-card").nth(2)
        expect(responsiveness_card.locator("h3")).to_have_text("Responsiveness")
        expect(responsiveness_card).to_contain_text(f"Desktop: {metrics['responsiveness']['desktop']}%")

    def test_report_version_tracking(self):
        """Test version tracking in the report."""
        # Check if version is present in the page
        version = self.test_report['data']['version']
        expect(self.page.locator("body")).to_contain_text(f"Version: {version}")

    def test_report_screenshot_capture(self):
        """Test screenshot capture functionality."""
        # Take screenshot of the entire page
        screenshot_path = self.screenshots_dir / f"full_page_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.page.screenshot(path=str(screenshot_path))

        # Verify screenshot was created
        self.assertTrue(screenshot_path.exists())

        # Take screenshot of a specific section
        section = self.test_report['data']['content']['sections'][0]
        section_element = self.page.locator(f"#{section['id']}")
        section_screenshot_path = self.screenshots_dir / f"section_{section['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        section_element.screenshot(path=str(section_screenshot_path))

        # Verify section screenshot was created
        self.assertTrue(section_screenshot_path.exists())

if __name__ == '__main__':
    unittest.main()
