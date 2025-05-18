"""
Functional runner for integration and end-to-end testing.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .base import BaseRunner
from ...server.config import ServerConfig

logger = logging.getLogger("functional_runner")

class FunctionalRunner(BaseRunner):
    """Runner for functional testing."""

    def __init__(self, config: ServerConfig):
        """Initialize functional runner.

        Args:
            config: Server configuration
        """
        super().__init__("functional", config)
        self.test_cases = self._load_test_cases()
        self.test_data = self._load_test_data()
        self.test_fixtures = self._load_test_fixtures()

    def _load_test_cases(self) -> Dict[str, Any]:
        """Load test cases.

        Returns:
            Dictionary of test cases
        """
        try:
            cases = self.runner_config.get("test_cases", {})
            if not cases:
                logger.warning("No test cases configured")
            return cases

        except Exception as e:
            logger.error(f"Error loading test cases: {e}")
            return {}

    def _load_test_data(self) -> Dict[str, Any]:
        """Load test data.

        Returns:
            Dictionary of test data
        """
        try:
            data = self.runner_config.get("test_data", {})
            if not data:
                logger.warning("No test data configured")
            return data

        except Exception as e:
            logger.error(f"Error loading test data: {e}")
            return {}

    def _load_test_fixtures(self) -> Dict[str, Any]:
        """Load test fixtures.

        Returns:
            Dictionary of test fixtures
        """
        try:
            fixtures = self.runner_config.get("test_fixtures", {})
            if not fixtures:
                logger.warning("No test fixtures configured")
            return fixtures

        except Exception as e:
            logger.error(f"Error loading test fixtures: {e}")
            return {}

    async def _run_tests(self, files: List[str]) -> Dict[str, Any]:
        """Run functional tests.

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

            # Set up test environment
            await self._setup_test_environment()

            try:
                # Run test cases
                test_results = await self._run_test_cases(files)
                results["test_results"] = test_results

                # Calculate coverage
                coverage = await self._calculate_functional_coverage(
                    files,
                    test_results
                )
                results["coverage"] = coverage

                # Aggregate issues
                results["issues"].extend(test_results.get("issues", []))

                # Update status
                results["status"] = "completed"

            finally:
                # Clean up test environment
                await self._cleanup_test_environment()

            return results

        except Exception as e:
            logger.error(f"Error running functional tests: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _setup_test_environment(self) -> None:
        """Set up test environment."""
        try:
            logger.info("Setting up test environment...")

            # Set up fixtures
            for fixture_id, fixture in self.test_fixtures.items():
                await self._setup_fixture(fixture_id, fixture)

            logger.info("Test environment set up successfully")

        except Exception as e:
            logger.error(f"Error setting up test environment: {e}")
            raise

    async def _cleanup_test_environment(self) -> None:
        """Clean up test environment."""
        try:
            logger.info("Cleaning up test environment...")

            # Clean up fixtures
            for fixture_id, fixture in self.test_fixtures.items():
                await self._cleanup_fixture(fixture_id, fixture)

            logger.info("Test environment cleaned up successfully")

        except Exception as e:
            logger.error(f"Error cleaning up test environment: {e}")
            raise

    async def _setup_fixture(
        self,
        fixture_id: str,
        fixture: Dict[str, Any]
    ) -> None:
        """Set up test fixture.

        Args:
            fixture_id: Fixture identifier
            fixture: Fixture configuration
        """
        try:
            logger.info(f"Setting up fixture {fixture_id}...")

            # Import fixture module
            module = __import__(
                fixture["module"],
                fromlist=[fixture["class"]]
            )

            # Get fixture class
            fixture_class = getattr(module, fixture["class"])

            # Create fixture instance
            instance = fixture_class(**fixture.get("args", {}))

            # Set up fixture
            await instance.setup()

            # Store fixture
            self.test_fixtures[fixture_id]["instance"] = instance

            logger.info(f"Fixture {fixture_id} set up successfully")

        except Exception as e:
            logger.error(f"Error setting up fixture {fixture_id}: {e}")
            raise

    async def _cleanup_fixture(
        self,
        fixture_id: str,
        fixture: Dict[str, Any]
    ) -> None:
        """Clean up test fixture.

        Args:
            fixture_id: Fixture identifier
            fixture: Fixture configuration
        """
        try:
            logger.info(f"Cleaning up fixture {fixture_id}...")

            # Get fixture instance
            instance = fixture.get("instance")
            if instance:
                # Clean up fixture
                await instance.cleanup()

                # Remove fixture
                del self.test_fixtures[fixture_id]["instance"]

            logger.info(f"Fixture {fixture_id} cleaned up successfully")

        except Exception as e:
            logger.error(f"Error cleaning up fixture {fixture_id}: {e}")
            raise

    async def _run_test_cases(
        self,
        files: List[str]
    ) -> Dict[str, Any]:
        """Run test cases.

        Args:
            files: Files to test

        Returns:
            Test case results
        """
        try:
            results = {
                "status": "running",
                "timestamp": datetime.now(),
                "files": files,
                "issues": []
            }

            for file in files:
                # Get test cases for file
                file_cases = self._get_file_test_cases(file)
                if not file_cases:
                    continue

                # Run file test cases
                file_results = await self._run_file_test_cases(
                    file,
                    file_cases
                )
                results["issues"].extend(file_results.get("issues", []))

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error running test cases: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    def _get_file_test_cases(
        self,
        file: str
    ) -> Dict[str, Any]:
        """Get test cases for file.

        Args:
            file: File to get test cases for

        Returns:
            Dictionary of test cases
        """
        try:
            cases = {}
            for case_id, case in self.test_cases.items():
                if file in case.get("files", []):
                    cases[case_id] = case
            return cases

        except Exception as e:
            logger.error(f"Error getting test cases for {file}: {e}")
            return {}

    async def _run_file_test_cases(
        self,
        file: str,
        cases: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run test cases for file.

        Args:
            file: File to test
            cases: Test cases to run

        Returns:
            Test case results
        """
        try:
            results = {
                "file": file,
                "issues": []
            }

            for case_id, case in cases.items():
                # Run test case
                case_results = await self._run_test_case(
                    case_id,
                    case,
                    file
                )
                if case_results.get("issues"):
                    results["issues"].extend([
                        {
                            "id": f"TST-{case_id}-{i}",
                            "type": "test",
                            "case": case_id,
                            "severity": case.get("severity", "medium"),
                            "description": issue.get("description", ""),
                            "step": issue.get("step"),
                            "expected": issue.get("expected"),
                            "actual": issue.get("actual")
                        }
                        for i, issue in enumerate(case_results["issues"])
                    ])

            return results

        except Exception as e:
            logger.error(f"Error running test cases for {file}: {e}")
            return {
                "file": file,
                "error": str(e)
            }

    async def _run_test_case(
        self,
        case_id: str,
        case: Dict[str, Any],
        file: str
    ) -> Dict[str, Any]:
        """Run test case.

        Args:
            case_id: Test case identifier
            case: Test case configuration
            file: File being tested

        Returns:
            Test case results
        """
        try:
            results = {
                "case": case_id,
                "issues": []
            }

            # Get test data
            data = self._get_test_data(case)

            # Run test steps
            for step in case.get("steps", []):
                step_result = await self._run_test_step(
                    step,
                    data,
                    file
                )
                if not step_result.get("success"):
                    results["issues"].append({
                        "description": step_result.get("error"),
                        "step": step.get("name"),
                        "expected": step.get("expected"),
                        "actual": step_result.get("actual")
                    })

            return results

        except Exception as e:
            logger.error(f"Error running test case {case_id}: {e}")
            return {
                "case": case_id,
                "error": str(e)
            }

    def _get_test_data(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """Get test data for case.

        Args:
            case: Test case configuration

        Returns:
            Test data dictionary
        """
        try:
            data = {}
            for data_id in case.get("data", []):
                if data_id in self.test_data:
                    data.update(self.test_data[data_id])
            return data

        except Exception as e:
            logger.error(f"Error getting test data: {e}")
            return {}

    async def _run_test_step(
        self,
        step: Dict[str, Any],
        data: Dict[str, Any],
        file: str
    ) -> Dict[str, Any]:
        """Run test step.

        Args:
            step: Step configuration
            data: Test data
            file: File being tested

        Returns:
            Step results
        """
        try:
            # Import step module
            module = __import__(
                step["module"],
                fromlist=[step["function"]]
            )

            # Get step function
            function = getattr(module, step["function"])

            # Run step
            result = await function(
                file=file,
                data=data,
                **step.get("args", {})
            )

            # Check result
            if step.get("expected"):
                if result != step["expected"]:
                    return {
                        "success": False,
                        "error": "Expectation not met",
                        "actual": result
                    }

            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error running step: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _calculate_functional_coverage(
        self,
        files: List[str],
        test_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate functional coverage.

        Args:
            files: Files tested
            test_results: Test results

        Returns:
            Coverage metrics
        """
        try:
            # Count total functions
            total_functions = 0
            for file in files:
                with open(file, "r") as f:
                    content = f.read()
                    import ast
                    tree = ast.parse(content)
                    total_functions += len([
                        node for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef)
                    ])

            # Count tested functions
            tested_functions = set()
            for issue in test_results.get("issues", []):
                if "step" in issue:
                    tested_functions.add(issue["step"])

            return {
                "total_functions": total_functions,
                "tested_functions": len(tested_functions),
                "coverage_percent": (
                    len(tested_functions) / total_functions * 100
                    if total_functions > 0 else 0
                )
            }

        except Exception as e:
            logger.error(f"Error calculating coverage: {e}")
            return {
                "total_functions": 0,
                "tested_functions": 0,
                "coverage_percent": 0
            }
