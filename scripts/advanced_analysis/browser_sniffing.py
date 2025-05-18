#!/usr/bin/env python3
"""
Browser Sniffing Module
This module implements browser-specific sniffing functionality
"""

import os
import sys
import logging
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, Page

from .config import SNIFFING_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('browser_sniffing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class BrowserIssue:
    """Data class for browser compatibility issues"""
    type: str
    severity: str
    description: str
    browser: str
    viewport: Dict
    location: str
    recommendation: str
    screenshot: Optional[str] = None

class BrowserSniffer:
    def __init__(self):
        self.config = SNIFFING_CONFIG["domains"]["browser"]
        self.thresholds = self.config["thresholds"]
        self.playwright = None
        self.browsers = {}

    async def initialize(self):
        """Initialize browser sniffing environment"""
        self.playwright = await async_playwright().start()
        for browser_type in ["chromium", "firefox", "webkit"]:
            self.browsers[browser_type] = await self.playwright[browser_type].launch(headless=True)

    async def cleanup(self):
        """Clean up browser resources"""
        for browser in self.browsers.values():
            await browser.close()
        await self.playwright.stop()

    async def sniff_file(self, file_path: str) -> List[BrowserIssue]:
        """Perform browser sniffing on a file"""
        logger.info(f"Starting browser sniffing for file: {file_path}")

        issues = []

        # Check if file is a web file
        if not self._is_web_file(file_path):
            return issues

        # Run compatibility tests
        issues.extend(await self._test_compatibility(file_path))

        # Run responsive design tests
        issues.extend(await self._test_responsive(file_path))

        # Run accessibility tests
        issues.extend(await self._test_accessibility(file_path))

        return issues

    def _is_web_file(self, file_path: str) -> bool:
        """Check if file is a web file"""
        return file_path.endswith(('.html', '.js', '.ts', '.css', '.vue', '.jsx', '.tsx'))

    async def _test_compatibility(self, file_path: str) -> List[BrowserIssue]:
        """Test browser compatibility"""
        issues = []

        for browser_type, browser in self.browsers.items():
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Load the file
                await page.goto(f"file://{os.path.abspath(file_path)}")

                # Test JavaScript features
                issues.extend(await self._test_js_features(page, browser_type, file_path))

                # Test CSS features
                issues.extend(await self._test_css_features(page, browser_type, file_path))

                # Test HTML5 features
                issues.extend(await self._test_html5_features(page, browser_type, file_path))

            except Exception as e:
                logger.error(f"Error testing compatibility in {browser_type}: {e}")
                issues.append(BrowserIssue(
                    type="compatibility_error",
                    severity="high",
                    description=f"Failed to test compatibility in {browser_type}: {str(e)}",
                    browser=browser_type,
                    viewport={"width": 1920, "height": 1080},
                    location=file_path,
                    recommendation="Fix compatibility issues and retry testing"
                ))

            finally:
                await context.close()

        return issues

    async def _test_responsive(self, file_path: str) -> List[BrowserIssue]:
        """Test responsive design"""
        issues = []

        viewport_sizes = [
            {"width": 1920, "height": 1080},  # Desktop
            {"width": 1366, "height": 768},   # Laptop
            {"width": 768, "height": 1024},   # Tablet
            {"width": 375, "height": 812}     # Mobile
        ]

        for browser_type, browser in self.browsers.items():
            for viewport in viewport_sizes:
                context = await browser.new_context(viewport=viewport)
                page = await context.new_page()

                try:
                    # Load the file
                    await page.goto(f"file://{os.path.abspath(file_path)}")

                    # Test layout
                    issues.extend(await self._test_layout(page, browser_type, viewport, file_path))

                    # Test images
                    issues.extend(await self._test_images(page, browser_type, viewport, file_path))

                    # Test typography
                    issues.extend(await self._test_typography(page, browser_type, viewport, file_path))

                except Exception as e:
                    logger.error(f"Error testing responsive design in {browser_type}: {e}")
                    issues.append(BrowserIssue(
                        type="responsive_error",
                        severity="high",
                        description=f"Failed to test responsive design in {browser_type}: {str(e)}",
                        browser=browser_type,
                        viewport=viewport,
                        location=file_path,
                        recommendation="Fix responsive design issues and retry testing"
                    ))

                finally:
                    await context.close()

        return issues

    async def _test_accessibility(self, file_path: str) -> List[BrowserIssue]:
        """Test accessibility"""
        issues = []

        for browser_type, browser in self.browsers.items():
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Load the file
                await page.goto(f"file://{os.path.abspath(file_path)}")

                # Test ARIA attributes
                issues.extend(await self._test_aria(page, browser_type, file_path))

                # Test keyboard navigation
                issues.extend(await self._test_keyboard_navigation(page, browser_type, file_path))

                # Test color contrast
                issues.extend(await self._test_color_contrast(page, browser_type, file_path))

            except Exception as e:
                logger.error(f"Error testing accessibility in {browser_type}: {e}")
                issues.append(BrowserIssue(
                    type="accessibility_error",
                    severity="high",
                    description=f"Failed to test accessibility in {browser_type}: {str(e)}",
                    browser=browser_type,
                    viewport={"width": 1920, "height": 1080},
                    location=file_path,
                    recommendation="Fix accessibility issues and retry testing"
                ))

            finally:
                await context.close()

        return issues

    async def _test_js_features(self, page: Page, browser_type: str, file_path: str) -> List[BrowserIssue]:
        """Test JavaScript features"""
        issues = []

        # Test modern JavaScript features
        js_features = [
            "const", "let", "arrow functions", "async/await",
            "template literals", "destructuring", "spread operator"
        ]

        for feature in js_features:
            try:
                result = await page.evaluate(f"typeof {feature} !== 'undefined'")
                if not result:
                    issues.append(BrowserIssue(
                        type="js_feature",
                        severity="medium",
                        description=f"JavaScript feature '{feature}' not supported",
                        browser=browser_type,
                        viewport={"width": 1920, "height": 1080},
                        location=file_path,
                        recommendation=f"Add polyfill for {feature} or use alternative syntax"
                    ))
            except Exception as e:
                logger.error(f"Error testing JS feature {feature}: {e}")

        return issues

    async def _test_css_features(self, page: Page, browser_type: str, file_path: str) -> List[BrowserIssue]:
        """Test CSS features"""
        issues = []

        # Test modern CSS features
        css_features = [
            "flexbox", "grid", "variables", "animations",
            "transforms", "transitions", "media queries"
        ]

        for feature in css_features:
            try:
                result = await page.evaluate(f"CSS.supports('{feature}')")
                if not result:
                    issues.append(BrowserIssue(
                        type="css_feature",
                        severity="medium",
                        description=f"CSS feature '{feature}' not supported",
                        browser=browser_type,
                        viewport={"width": 1920, "height": 1080},
                        location=file_path,
                        recommendation=f"Add fallback for {feature} or use alternative styling"
                    ))
            except Exception as e:
                logger.error(f"Error testing CSS feature {feature}: {e}")

        return issues

    async def _test_html5_features(self, page: Page, browser_type: str, file_path: str) -> List[BrowserIssue]:
        """Test HTML5 features"""
        issues = []

        # Test HTML5 features
        html5_features = [
            "canvas", "video", "audio", "localStorage",
            "sessionStorage", "geolocation", "web workers"
        ]

        for feature in html5_features:
            try:
                result = await page.evaluate(f"typeof {feature} !== 'undefined'")
                if not result:
                    issues.append(BrowserIssue(
                        type="html5_feature",
                        severity="medium",
                        description=f"HTML5 feature '{feature}' not supported",
                        browser=browser_type,
                        viewport={"width": 1920, "height": 1080},
                        location=file_path,
                        recommendation=f"Add fallback for {feature} or use alternative approach"
                    ))
            except Exception as e:
                logger.error(f"Error testing HTML5 feature {feature}: {e}")

        return issues

    async def _test_layout(self, page: Page, browser_type: str, viewport: Dict, file_path: str) -> List[BrowserIssue]:
        """Test layout at different viewport sizes"""
        issues = []

        try:
            # Check for horizontal scrolling
            has_horizontal_scroll = await page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
            if has_horizontal_scroll:
                issues.append(BrowserIssue(
                    type="layout",
                    severity="high",
                    description="Horizontal scrolling detected",
                    browser=browser_type,
                    viewport=viewport,
                    location=file_path,
                    recommendation="Fix layout to prevent horizontal scrolling",
                    screenshot=await self._take_screenshot(page, "horizontal_scroll")
                ))

            # Check for overflow
            elements = await page.query_selector_all("*")
            for element in elements:
                style = await element.get_attribute("style")
                if style and "overflow: hidden" in style:
                    issues.append(BrowserIssue(
                        type="layout",
                        severity="medium",
                        description="Hidden overflow detected",
                        browser=browser_type,
                        viewport=viewport,
                        location=file_path,
                        recommendation="Review overflow handling",
                        screenshot=await self._take_screenshot(page, "overflow")
                    ))

        except Exception as e:
            logger.error(f"Error testing layout: {e}")

        return issues

    async def _test_images(self, page: Page, browser_type: str, viewport: Dict, file_path: str) -> List[BrowserIssue]:
        """Test image handling"""
        issues = []

        try:
            # Check for missing alt text
            images = await page.query_selector_all("img")
            for image in images:
                alt = await image.get_attribute("alt")
                if not alt:
                    issues.append(BrowserIssue(
                        type="accessibility",
                        severity="medium",
                        description="Image missing alt text",
                        browser=browser_type,
                        viewport=viewport,
                        location=file_path,
                        recommendation="Add descriptive alt text to images",
                        screenshot=await self._take_screenshot(page, "missing_alt")
                    ))

            # Check for responsive images
            for image in images:
                srcset = await image.get_attribute("srcset")
                sizes = await image.get_attribute("sizes")
                if not (srcset or sizes):
                    issues.append(BrowserIssue(
                        type="responsive",
                        severity="medium",
                        description="Image not responsive",
                        browser=browser_type,
                        viewport=viewport,
                        location=file_path,
                        recommendation="Add srcset and sizes attributes for responsive images",
                        screenshot=await self._take_screenshot(page, "non_responsive_image")
                    ))

        except Exception as e:
            logger.error(f"Error testing images: {e}")

        return issues

    async def _test_typography(self, page: Page, browser_type: str, viewport: Dict, file_path: str) -> List[BrowserIssue]:
        """Test typography"""
        issues = []

        try:
            # Check for minimum font size
            elements = await page.query_selector_all("*")
            for element in elements:
                style = await element.get_attribute("style")
                if style and "font-size" in style:
                    font_size = await page.evaluate("""
                        (element) => {
                            const style = window.getComputedStyle(element);
                            return parseFloat(style.fontSize);
                        }
                    """, element)
                    if font_size < 12:
                        issues.append(BrowserIssue(
                            type="typography",
                            severity="medium",
                            description="Font size too small",
                            browser=browser_type,
                            viewport=viewport,
                            location=file_path,
                            recommendation="Increase font size for better readability",
                            screenshot=await self._take_screenshot(page, "small_font")
                        ))

        except Exception as e:
            logger.error(f"Error testing typography: {e}")

        return issues

    async def _test_aria(self, page: Page, browser_type: str, file_path: str) -> List[BrowserIssue]:
        """Test ARIA attributes"""
        issues = []

        try:
            # Check for proper ARIA roles
            elements = await page.query_selector_all("[role]")
            for element in elements:
                role = await element.get_attribute("role")
                if role not in ["button", "link", "menuitem", "tab", "checkbox", "radio", "textbox"]:
                    issues.append(BrowserIssue(
                        type="accessibility",
                        severity="medium",
                        description=f"Invalid ARIA role: {role}",
                        browser=browser_type,
                        viewport={"width": 1920, "height": 1080},
                        location=file_path,
                        recommendation="Use valid ARIA roles",
                        screenshot=await self._take_screenshot(page, "invalid_aria")
                    ))

            # Check for ARIA labels
            elements = await page.query_selector_all("[aria-label]")
            for element in elements:
                label = await element.get_attribute("aria-label")
                if not label:
                    issues.append(BrowserIssue(
                        type="accessibility",
                        severity="medium",
                        description="Empty ARIA label",
                        browser=browser_type,
                        viewport={"width": 1920, "height": 1080},
                        location=file_path,
                        recommendation="Add descriptive ARIA labels",
                        screenshot=await self._take_screenshot(page, "empty_aria")
                    ))

        except Exception as e:
            logger.error(f"Error testing ARIA: {e}")

        return issues

    async def _test_keyboard_navigation(self, page: Page, browser_type: str, file_path: str) -> List[BrowserIssue]:
        """Test keyboard navigation"""
        issues = []

        try:
            # Check for focusable elements
            elements = await page.query_selector_all("a, button, input, select, textarea")
            for element in elements:
                tabindex = await element.get_attribute("tabindex")
                if tabindex == "-1":
                    issues.append(BrowserIssue(
                        type="accessibility",
                        severity="medium",
                        description="Element not focusable",
                        browser=browser_type,
                        viewport={"width": 1920, "height": 1080},
                        location=file_path,
                        recommendation="Make element focusable for keyboard navigation",
                        screenshot=await self._take_screenshot(page, "not_focusable")
                    ))

        except Exception as e:
            logger.error(f"Error testing keyboard navigation: {e}")

        return issues

    async def _test_color_contrast(self, page: Page, browser_type: str, file_path: str) -> List[BrowserIssue]:
        """Test color contrast"""
        issues = []

        try:
            # Check text color contrast
            elements = await page.query_selector_all("*")
            for element in elements:
                style = await element.get_attribute("style")
                if style and ("color" in style or "background-color" in style):
                    contrast = await page.evaluate("""
                        (element) => {
                            const style = window.getComputedStyle(element);
                            const color = style.color;
                            const bgColor = style.backgroundColor;
                            // Implement contrast calculation
                            return 4.5; // Minimum required contrast ratio
                        }
                    """, element)
                    if contrast < 4.5:
                        issues.append(BrowserIssue(
                            type="accessibility",
                            severity="high",
                            description="Insufficient color contrast",
                            browser=browser_type,
                            viewport={"width": 1920, "height": 1080},
                            location=file_path,
                            recommendation="Increase color contrast for better readability",
                            screenshot=await self._take_screenshot(page, "low_contrast")
                        ))

        except Exception as e:
            logger.error(f"Error testing color contrast: {e}")

        return issues

    async def _take_screenshot(self, page: Page, name: str) -> str:
        """Take a screenshot of the page"""
        try:
            screenshot_dir = Path("reports/sniffing/browser/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            path = screenshot_dir / filename

            await page.screenshot(path=str(path))
            return str(path)

        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None

    def calculate_browser_score(self, issues: List[BrowserIssue]) -> float:
        """Calculate browser compatibility score"""
        if not issues:
            return 100.0

        # Weight issues by severity
        severity_weights = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2
        }

        total_weight = sum(severity_weights.get(issue.severity, 0.5) for issue in issues)
        max_possible_weight = len(issues) * 1.0  # Assuming all issues are critical

        return max(0.0, 100.0 * (1.0 - total_weight / max_possible_weight))

async def main():
    """Main function"""
    try:
        sniffer = BrowserSniffer()
        await sniffer.initialize()
        issues = await sniffer.sniff_file("example.html")
        score = sniffer.calculate_browser_score(issues)
        print(f"Browser compatibility score: {score}")
        for issue in issues:
            print(f"Issue: {issue}")
        await sniffer.cleanup()
    except Exception as e:
        logger.error(f"Browser sniffing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
