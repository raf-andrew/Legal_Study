"""
Browser runner for UI/UX testing and cross-browser compatibility.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .base import BaseRunner
from ...server.config import ServerConfig

logger = logging.getLogger("browser_runner")

class BrowserRunner(BaseRunner):
    """Runner for browser testing."""

    def __init__(self, config: ServerConfig):
        """Initialize browser runner.

        Args:
            config: Server configuration
        """
        super().__init__("browser", config)
        self.browsers = self._load_browsers()
        self.test_scenarios = self._load_test_scenarios()
        self.compatibility_rules = self._load_compatibility_rules()

    def _load_browsers(self) -> Dict[str, Any]:
        """Load browser configurations.

        Returns:
            Dictionary of browser configurations
        """
        try:
            browsers = self.runner_config.get("browsers", {})
            if not browsers:
                logger.warning("No browsers configured")
            return browsers

        except Exception as e:
            logger.error(f"Error loading browsers: {e}")
            return {}

    def _load_test_scenarios(self) -> Dict[str, Any]:
        """Load test scenarios.

        Returns:
            Dictionary of test scenarios
        """
        try:
            scenarios = self.runner_config.get("test_scenarios", {})
            if not scenarios:
                logger.warning("No test scenarios configured")
            return scenarios

        except Exception as e:
            logger.error(f"Error loading test scenarios: {e}")
            return {}

    def _load_compatibility_rules(self) -> Dict[str, Any]:
        """Load compatibility rules.

        Returns:
            Dictionary of compatibility rules
        """
        try:
            rules = self.runner_config.get("compatibility_rules", {})
            if not rules:
                logger.warning("No compatibility rules configured")
            return rules

        except Exception as e:
            logger.error(f"Error loading compatibility rules: {e}")
            return {}

    async def _run_tests(self, files: List[str]) -> Dict[str, Any]:
        """Run browser tests.

        Args:
            files: Files to test

        Returns:
            Test results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": [],
                "coverage": {}
            }

            # Run browser tests
            browser_results = await self._run_browser_tests(files)
            results["browser_tests"] = browser_results

            # Check compatibility
            compatibility_results = await self._check_compatibility(files)
            results["compatibility"] = compatibility_results

            # Run scenarios
            scenario_results = await self._run_scenarios(files)
            results["scenarios"] = scenario_results

            # Calculate coverage
            coverage = await self._calculate_browser_coverage(
                files,
                browser_results,
                compatibility_results,
                scenario_results
            )
            results["coverage"] = coverage

            # Aggregate issues
            issues = []
            issues.extend(browser_results.get("issues", []))
            issues.extend(compatibility_results.get("issues", []))
            issues.extend(scenario_results.get("issues", []))
            results["issues"] = issues

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error running browser tests: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_browser_tests(
        self,
        files: List[str]
    ) -> Dict[str, Any]:
        """Run tests in different browsers.

        Args:
            files: Files to test

        Returns:
            Browser test results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": []
            }

            for browser_id, browser in self.browsers.items():
                # Run browser tests
                browser_results = await self._run_browser_file_tests(
                    files,
                    browser_id,
                    browser
                )
                results["issues"].extend(browser_results.get("issues", []))

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error running browser tests: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_browser_file_tests(
        self,
        files: List[str],
        browser_id: str,
        browser: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run tests for files in a browser.

        Args:
            files: Files to test
            browser_id: Browser identifier
            browser: Browser configuration

        Returns:
            Browser test results
        """
        try:
            results = {
                "browser": browser_id,
                "issues": []
            }

            # Import Selenium
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            # Create driver
            driver = getattr(webdriver, browser["driver"])()

            try:
                for file in files:
                    # Run file tests
                    file_results = await self._run_browser_file_test(
                        file,
                        browser_id,
                        driver
                    )
                    results["issues"].extend(file_results.get("issues", []))

            finally:
                # Close driver
                driver.quit()

            return results

        except Exception as e:
            logger.error(f"Error running {browser_id} tests: {e}")
            return {
                "browser": browser_id,
                "error": str(e)
            }

    async def _run_browser_file_test(
        self,
        file: str,
        browser_id: str,
        driver: Any
    ) -> Dict[str, Any]:
        """Run tests for a file in a browser.

        Args:
            file: File to test
            browser_id: Browser identifier
            driver: Browser driver

        Returns:
            File test results
        """
        try:
            results = {
                "file": file,
                "browser": browser_id,
                "issues": []
            }

            # Load file
            driver.get(f"file://{file}")

            # Check rendering
            rendering_issues = await self._check_rendering(driver)
            results["issues"].extend(rendering_issues)

            # Check interactions
            interaction_issues = await self._check_interactions(driver)
            results["issues"].extend(interaction_issues)

            # Check performance
            performance_issues = await self._check_performance(driver)
            results["issues"].extend(performance_issues)

            return results

        except Exception as e:
            logger.error(f"Error testing {file} in {browser_id}: {e}")
            return {
                "file": file,
                "browser": browser_id,
                "error": str(e)
            }

    async def _check_rendering(self, driver: Any) -> List[Dict[str, Any]]:
        """Check page rendering.

        Args:
            driver: Browser driver

        Returns:
            List of rendering issues
        """
        try:
            issues = []

            # Check visibility
            elements = driver.find_elements(By.CSS_SELECTOR, "*")
            for element in elements:
                if not element.is_displayed():
                    issues.append({
                        "type": "rendering",
                        "severity": "medium",
                        "description": "Element not visible",
                        "element": element.tag_name,
                        "location": element.location
                    })

            # Check layout
            viewport = driver.get_window_size()
            for element in elements:
                rect = element.rect
                if (
                    rect["x"] < 0 or
                    rect["y"] < 0 or
                    rect["x"] + rect["width"] > viewport["width"] or
                    rect["y"] + rect["height"] > viewport["height"]
                ):
                    issues.append({
                        "type": "rendering",
                        "severity": "medium",
                        "description": "Element outside viewport",
                        "element": element.tag_name,
                        "location": element.location
                    })

            return issues

        except Exception as e:
            logger.error(f"Error checking rendering: {e}")
            return []

    async def _check_interactions(self, driver: Any) -> List[Dict[str, Any]]:
        """Check page interactions.

        Args:
            driver: Browser driver

        Returns:
            List of interaction issues
        """
        try:
            issues = []

            # Check clickable elements
            elements = driver.find_elements(
                By.CSS_SELECTOR,
                "button, a, input[type='submit']"
            )
            for element in elements:
                if not element.is_enabled():
                    issues.append({
                        "type": "interaction",
                        "severity": "high",
                        "description": "Element not clickable",
                        "element": element.tag_name,
                        "location": element.location
                    })

            # Check form elements
            forms = driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                inputs = form.find_elements(By.TAG_NAME, "input")
                for input_element in inputs:
                    if not input_element.is_enabled():
                        issues.append({
                            "type": "interaction",
                            "severity": "high",
                            "description": "Form input not interactive",
                            "element": input_element.get_attribute("name"),
                            "location": input_element.location
                        })

            return issues

        except Exception as e:
            logger.error(f"Error checking interactions: {e}")
            return []

    async def _check_performance(self, driver: Any) -> List[Dict[str, Any]]:
        """Check page performance.

        Args:
            driver: Browser driver

        Returns:
            List of performance issues
        """
        try:
            issues = []

            # Get performance metrics
            metrics = driver.execute_script("""
                const performance = window.performance;
                const timing = performance.timing;
                return {
                    loadTime: timing.loadEventEnd - timing.navigationStart,
                    domReady: timing.domComplete - timing.domLoading,
                    firstPaint: performance.getEntriesByType('paint')[0].startTime
                };
            """)

            # Check load time
            if metrics["loadTime"] > 3000:  # 3 seconds
                issues.append({
                    "type": "performance",
                    "severity": "medium",
                    "description": "Slow page load",
                    "metric": "loadTime",
                    "value": metrics["loadTime"]
                })

            # Check DOM ready time
            if metrics["domReady"] > 1000:  # 1 second
                issues.append({
                    "type": "performance",
                    "severity": "medium",
                    "description": "Slow DOM ready",
                    "metric": "domReady",
                    "value": metrics["domReady"]
                })

            # Check first paint
            if metrics["firstPaint"] > 1000:  # 1 second
                issues.append({
                    "type": "performance",
                    "severity": "medium",
                    "description": "Slow first paint",
                    "metric": "firstPaint",
                    "value": metrics["firstPaint"]
                })

            return issues

        except Exception as e:
            logger.error(f"Error checking performance: {e}")
            return []

    async def _check_compatibility(
        self,
        files: List[str]
    ) -> Dict[str, Any]:
        """Check browser compatibility.

        Args:
            files: Files to check

        Returns:
            Compatibility check results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": []
            }

            for file in files:
                # Check file
                file_results = await self._check_file_compatibility(file)
                results["issues"].extend(file_results.get("issues", []))

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error checking compatibility: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _check_file_compatibility(
        self,
        file: str
    ) -> Dict[str, Any]:
        """Check file compatibility.

        Args:
            file: File to check

        Returns:
            File compatibility results
        """
        try:
            results = {
                "file": file,
                "issues": []
            }

            # Read file content
            with open(file, "r") as f:
                content = f.read()

            # Check each rule
            for rule_id, rule in self.compatibility_rules.items():
                violations = await self._check_compatibility_rule(
                    content,
                    rule
                )
                if violations:
                    results["issues"].extend([
                        {
                            "id": f"COM-{rule_id}-{i}",
                            "type": "compatibility",
                            "rule": rule_id,
                            "severity": rule.get("severity", "medium"),
                            "description": rule.get("description", ""),
                            "browsers": rule.get("browsers", []),
                            "line": violation.get("line"),
                            "code": violation.get("code"),
                            "fix": rule.get("fix", "")
                        }
                        for i, violation in enumerate(violations)
                    ])

            return results

        except Exception as e:
            logger.error(f"Error checking file {file}: {e}")
            return {
                "file": file,
                "error": str(e)
            }

    async def _check_compatibility_rule(
        self,
        content: str,
        rule: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Check content for compatibility rule.

        Args:
            content: Content to check
            rule: Rule to check for

        Returns:
            List of rule violations
        """
        try:
            violations = []
            lines = content.split("\n")

            for i, line in enumerate(lines):
                if rule.get("regex"):
                    # Use regex pattern
                    import re
                    if re.search(rule["regex"], line):
                        violations.append({
                            "line": i + 1,
                            "code": line.strip()
                        })

            return violations

        except Exception as e:
            logger.error(f"Error checking rule: {e}")
            return []

    async def _run_scenarios(
        self,
        files: List[str]
    ) -> Dict[str, Any]:
        """Run test scenarios.

        Args:
            files: Files to test

        Returns:
            Scenario test results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": []
            }

            for file in files:
                # Run scenarios
                file_results = await self._run_file_scenarios(file)
                results["issues"].extend(file_results.get("issues", []))

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error running scenarios: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_file_scenarios(
        self,
        file: str
    ) -> Dict[str, Any]:
        """Run test scenarios for file.

        Args:
            file: File to test

        Returns:
            File scenario results
        """
        try:
            results = {
                "file": file,
                "issues": []
            }

            # Import Selenium
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            # Run scenarios in each browser
            for browser_id, browser in self.browsers.items():
                # Create driver
                driver = getattr(webdriver, browser["driver"])()

                try:
                    # Load file
                    driver.get(f"file://{file}")

                    # Run each scenario
                    for scenario_id, scenario in self.test_scenarios.items():
                        scenario_results = await self._run_scenario(
                            scenario_id,
                            scenario,
                            driver
                        )
                        if scenario_results.get("issues"):
                            results["issues"].extend([
                                {
                                    "id": f"SCN-{scenario_id}-{i}",
                                    "type": "scenario",
                                    "scenario": scenario_id,
                                    "browser": browser_id,
                                    "severity": scenario.get("severity", "medium"),
                                    "description": issue.get("description", ""),
                                    "element": issue.get("element"),
                                    "action": issue.get("action"),
                                    "expected": issue.get("expected"),
                                    "actual": issue.get("actual")
                                }
                                for i, issue in enumerate(scenario_results["issues"])
                            ])

                finally:
                    # Close driver
                    driver.quit()

            return results

        except Exception as e:
            logger.error(f"Error running scenarios for {file}: {e}")
            return {
                "file": file,
                "error": str(e)
            }

    async def _run_scenario(
        self,
        scenario_id: str,
        scenario: Dict[str, Any],
        driver: Any
    ) -> Dict[str, Any]:
        """Run test scenario.

        Args:
            scenario_id: Scenario identifier
            scenario: Scenario configuration
            driver: Browser driver

        Returns:
            Scenario results
        """
        try:
            results = {
                "scenario": scenario_id,
                "issues": []
            }

            # Run each step
            for step in scenario.get("steps", []):
                step_result = await self._run_scenario_step(step, driver)
                if not step_result.get("success"):
                    results["issues"].append({
                        "description": step_result.get("error"),
                        "element": step.get("element"),
                        "action": step.get("action"),
                        "expected": step.get("expected"),
                        "actual": step_result.get("actual")
                    })

            return results

        except Exception as e:
            logger.error(f"Error running scenario {scenario_id}: {e}")
            return {
                "scenario": scenario_id,
                "error": str(e)
            }

    async def _run_scenario_step(
        self,
        step: Dict[str, Any],
        driver: Any
    ) -> Dict[str, Any]:
        """Run scenario step.

        Args:
            step: Step configuration
            driver: Browser driver

        Returns:
            Step results
        """
        try:
            # Find element
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    getattr(By, step["by"].upper()),
                    step["selector"]
                ))
            )

            # Perform action
            action = step["action"].lower()
            if action == "click":
                element.click()
            elif action == "type":
                element.send_keys(step["value"])
            elif action == "clear":
                element.clear()
            elif action == "submit":
                element.submit()

            # Check expectation
            if step.get("expected"):
                actual = None
                if step["expected"].get("visible"):
                    actual = element.is_displayed()
                elif step["expected"].get("text"):
                    actual = element.text
                elif step["expected"].get("value"):
                    actual = element.get_attribute("value")

                if actual != step["expected"].get("value"):
                    return {
                        "success": False,
                        "error": "Expectation not met",
                        "actual": actual
                    }

            return {
                "success": True
            }

        except Exception as e:
            logger.error(f"Error running step: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _calculate_browser_coverage(
        self,
        files: List[str],
        browser_results: Dict[str, Any],
        compatibility_results: Dict[str, Any],
        scenario_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate browser coverage.

        Args:
            files: Files tested
            browser_results: Browser test results
            compatibility_results: Compatibility check results
            scenario_results: Scenario test results

        Returns:
            Coverage metrics
        """
        try:
            # Count total elements
            total_elements = 0
            for file in files:
                with open(file, "r") as f:
                    content = f.read()
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(content, "html.parser")
                    total_elements += len(soup.find_all())

            # Count tested elements
            tested_elements = set()
            for results in [
                browser_results,
                compatibility_results,
                scenario_results
            ]:
                for issue in results.get("issues", []):
                    if "element" in issue:
                        tested_elements.add(issue["element"])

            return {
                "total_elements": total_elements,
                "tested_elements": len(tested_elements),
                "coverage_percent": (
                    len(tested_elements) / total_elements * 100
                    if total_elements > 0 else 0
                )
            }

        except Exception as e:
            logger.error(f"Error calculating coverage: {e}")
            return {
                "total_elements": 0,
                "tested_elements": 0,
                "coverage_percent": 0
            }
