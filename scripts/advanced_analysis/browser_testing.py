#!/usr/bin/env python3
"""
Browser Testing Module
This module handles browser-based testing and validation
"""

import os
import sys
import logging
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page
from dataclasses import dataclass

from .config import ANALYSIS_CONFIG, REPORT_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('browser_testing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Data class for test results"""
    name: str
    status: str
    duration: float
    error: Optional[str] = None
    screenshots: List[str] = None
    metrics: Dict = None

class BrowserTester:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "overall_status": "pending"
        }
        self.browser = None
        self.page = None
        self.config = ANALYSIS_CONFIG["browser"]
        self.screenshots_dir = Path(self.config["report_dir"]) / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Initialize browser testing environment"""
        self.playwright = await async_playwright().start()
        self.browsers = {}
        for browser_type in self.config["browsers"]:
            self.browsers[browser_type] = await self._launch_browser(browser_type)

    async def _launch_browser(self, browser_type: str) -> Browser:
        """Launch a specific browser"""
        if browser_type == "chrome":
            return await self.playwright.chromium.launch(headless=True)
        elif browser_type == "firefox":
            return await self.playwright.firefox.launch(headless=True)
        elif browser_type == "webkit":
            return await self.playwright.webkit.launch(headless=True)
        raise ValueError(f"Unsupported browser type: {browser_type}")

    async def cleanup(self):
        """Clean up resources"""
        for browser in self.browsers.values():
            await browser.close()
        await self.playwright.stop()

    async def run_tests(self, base_url: str):
        """Run all browser tests"""
        logger.info("Starting browser tests")

        for browser_type, browser in self.browsers.items():
            self.results["tests"][browser_type] = {}

            for viewport in self.config["viewport_sizes"]:
                context = await browser.new_context(
                    viewport=viewport,
                    record_video_dir=str(Path(self.config["report_dir"]) / "videos")
                )
                page = await context.new_page()

                # Run different types of tests
                await self._run_accessibility_tests(page, base_url, browser_type, viewport)
                await self._run_performance_tests(page, base_url, browser_type, viewport)
                await self._run_compatibility_tests(page, base_url, browser_type, viewport)
                await self._run_responsive_tests(page, base_url, browser_type, viewport)
                await self._run_functional_tests(page, base_url, browser_type, viewport)

                await context.close()

        await self._generate_report()

    async def _run_accessibility_tests(self, page: Page, base_url: str, browser: str, viewport: Dict):
        """Run accessibility tests"""
        logger.info(f"Running accessibility tests on {browser} with viewport {viewport}")

        tests = [
            self._test_aria_labels,
            self._test_color_contrast,
            self._test_keyboard_navigation,
            self._test_screen_reader_compatibility
        ]

        results = []
        for test in tests:
            try:
                result = await test(page, base_url)
                results.append(result)
            except Exception as e:
                logger.error(f"Accessibility test failed: {e}")
                results.append(TestResult(
                    name=test.__name__,
                    status="error",
                    duration=0,
                    error=str(e)
                ))

        self._save_test_results("accessibility", browser, viewport, results)

    async def _run_performance_tests(self, page: Page, base_url: str, browser: str, viewport: Dict):
        """Run performance tests"""
        logger.info(f"Running performance tests on {browser} with viewport {viewport}")

        tests = [
            self._test_page_load_time,
            self._test_first_contentful_paint,
            self._test_time_to_interactive,
            self._test_resource_loading
        ]

        results = []
        for test in tests:
            try:
                result = await test(page, base_url)
                results.append(result)
            except Exception as e:
                logger.error(f"Performance test failed: {e}")
                results.append(TestResult(
                    name=test.__name__,
                    status="error",
                    duration=0,
                    error=str(e)
                ))

        self._save_test_results("performance", browser, viewport, results)

    async def _run_compatibility_tests(self, page: Page, base_url: str, browser: str, viewport: Dict):
        """Run compatibility tests"""
        logger.info(f"Running compatibility tests on {browser} with viewport {viewport}")

        tests = [
            self._test_js_features,
            self._test_css_features,
            self._test_html5_features,
            self._test_web_apis
        ]

        results = []
        for test in tests:
            try:
                result = await test(page, base_url)
                results.append(result)
            except Exception as e:
                logger.error(f"Compatibility test failed: {e}")
                results.append(TestResult(
                    name=test.__name__,
                    status="error",
                    duration=0,
                    error=str(e)
                ))

        self._save_test_results("compatibility", browser, viewport, results)

    async def _run_responsive_tests(self, page: Page, base_url: str, browser: str, viewport: Dict):
        """Run responsive design tests"""
        logger.info(f"Running responsive tests on {browser} with viewport {viewport}")

        tests = [
            self._test_layout_breakpoints,
            self._test_image_scaling,
            self._test_touch_targets,
            self._test_content_reflow
        ]

        results = []
        for test in tests:
            try:
                result = await test(page, base_url)
                results.append(result)
            except Exception as e:
                logger.error(f"Responsive test failed: {e}")
                results.append(TestResult(
                    name=test.__name__,
                    status="error",
                    duration=0,
                    error=str(e)
                ))

        self._save_test_results("responsive", browser, viewport, results)

    async def _run_functional_tests(self, page: Page, base_url: str, browser: str, viewport: Dict):
        """Run functional tests"""
        logger.info(f"Running functional tests on {browser} with viewport {viewport}")

        tests = [
            self._test_navigation,
            self._test_forms,
            self._test_user_interactions,
            self._test_error_handling
        ]

        results = []
        for test in tests:
            try:
                result = await test(page, base_url)
                results.append(result)
            except Exception as e:
                logger.error(f"Functional test failed: {e}")
                results.append(TestResult(
                    name=test.__name__,
                    status="error",
                    duration=0,
                    error=str(e)
                ))

        self._save_test_results("functional", browser, viewport, results)

    async def _test_page_load_time(self, page: Page, url: str) -> TestResult:
        """Test page load time"""
        start_time = datetime.now()
        response = await page.goto(url)
        load_time = (datetime.now() - start_time).total_seconds()

        metrics = await page.evaluate("""() => {
            const timing = window.performance.timing;
            return {
                navigationStart: timing.navigationStart,
                responseEnd: timing.responseEnd,
                domComplete: timing.domComplete,
                loadEventEnd: timing.loadEventEnd
            }
        }""")

        screenshot = await self._take_screenshot(page, "page_load")

        return TestResult(
            name="page_load_time",
            status="pass" if load_time < 3.0 else "fail",
            duration=load_time,
            screenshots=[screenshot],
            metrics=metrics
        )

    async def _test_navigation(self, page: Page, base_url: str) -> TestResult:
        """Test navigation functionality"""
        start_time = datetime.now()
        results = []

        # Test main navigation links
        nav_links = await page.query_selector_all("nav a")
        for link in nav_links:
            href = await link.get_attribute("href")
            if href and not href.startswith("#"):
                try:
                    await link.click()
                    await page.wait_for_load_state("networkidle")
                    results.append({
                        "link": href,
                        "status": "success",
                        "url": page.url
                    })
                except Exception as e:
                    results.append({
                        "link": href,
                        "status": "error",
                        "error": str(e)
                    })

        duration = (datetime.now() - start_time).total_seconds()
        screenshot = await self._take_screenshot(page, "navigation")

        return TestResult(
            name="navigation_test",
            status="pass" if all(r["status"] == "success" for r in results) else "fail",
            duration=duration,
            screenshots=[screenshot],
            metrics={"navigation_results": results}
        )

    async def _take_screenshot(self, page: Page, name: str) -> str:
        """Take a screenshot of the page"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        path = self.screenshots_dir / filename
        await page.screenshot(path=str(path))
        return str(path)

    def _save_test_results(self, test_type: str, browser: str, viewport: Dict, results: List[TestResult]):
        """Save test results"""
        if browser not in self.results["tests"]:
            self.results["tests"][browser] = {}

        viewport_key = f"{viewport['width']}x{viewport['height']}"
        if viewport_key not in self.results["tests"][browser]:
            self.results["tests"][browser][viewport_key] = {}

        self.results["tests"][browser][viewport_key][test_type] = [vars(result) for result in results]

    async def _generate_report(self):
        """Generate comprehensive test report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(),
            "details": self.results,
            "recommendations": self._generate_recommendations()
        }

        report_file = Path(self.config["report_dir"]) / f"browser_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

    def _generate_summary(self) -> Dict:
        """Generate test summary"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0

        for browser in self.results["tests"].values():
            for viewport in browser.values():
                for test_type in viewport.values():
                    for test in test_type:
                        total_tests += 1
                        if test["status"] == "pass":
                            passed_tests += 1
                        elif test["status"] == "fail":
                            failed_tests += 1
                        else:
                            error_tests += 1

        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }

    def _generate_recommendations(self) -> List[Dict]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Analyze performance issues
        performance_issues = self._analyze_performance_issues()
        if performance_issues:
            recommendations.extend(performance_issues)

        # Analyze compatibility issues
        compatibility_issues = self._analyze_compatibility_issues()
        if compatibility_issues:
            recommendations.extend(compatibility_issues)

        # Analyze accessibility issues
        accessibility_issues = self._analyze_accessibility_issues()
        if accessibility_issues:
            recommendations.extend(accessibility_issues)

        return recommendations

    def _analyze_performance_issues(self) -> List[Dict]:
        """Analyze performance issues"""
        issues = []
        for browser, viewports in self.results["tests"].items():
            for viewport, tests in viewports.items():
                if "performance" in tests:
                    for test in tests["performance"]:
                        if test["status"] == "fail":
                            issues.append({
                                "type": "performance",
                                "browser": browser,
                                "viewport": viewport,
                                "test": test["name"],
                                "recommendation": self._get_performance_recommendation(test)
                            })
        return issues

    def _get_performance_recommendation(self, test: Dict) -> str:
        """Get performance recommendation based on test results"""
        recommendations = {
            "page_load_time": "Optimize page load time by reducing resource size and implementing caching",
            "first_contentful_paint": "Improve FCP by optimizing critical rendering path",
            "time_to_interactive": "Reduce JavaScript execution time and implement code splitting",
            "resource_loading": "Optimize resource loading through lazy loading and compression"
        }
        return recommendations.get(test["name"], "Review performance metrics and implement optimizations")

async def main():
    """Main function"""
    try:
        tester = BrowserTester()
        await tester.initialize()
        await tester.run_tests("http://localhost:8000")
        await tester.cleanup()
    except Exception as e:
        logger.error(f"Browser testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
