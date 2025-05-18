"""
Unit runner for unit testing and coverage analysis.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from .base import BaseRunner
from ...server.config import ServerConfig

logger = logging.getLogger("unit_runner")

class UnitRunner(BaseRunner):
    """Runner for unit testing."""

    def __init__(self, config: ServerConfig):
        """Initialize unit runner.

        Args:
            config: Server configuration
        """
        super().__init__("unit", config)
        self.test_modules = self._load_test_modules()
        self.test_patterns = self._load_test_patterns()
        self.coverage_config = self._load_coverage_config()

    def _load_test_modules(self) -> Dict[str, Any]:
        """Load test modules.

        Returns:
            Dictionary of test modules
        """
        try:
            modules = self.runner_config.get("test_modules", {})
            if not modules:
                logger.warning("No test modules configured")
            return modules

        except Exception as e:
            logger.error(f"Error loading test modules: {e}")
            return {}

    def _load_test_patterns(self) -> Dict[str, Any]:
        """Load test patterns.

        Returns:
            Dictionary of test patterns
        """
        try:
            patterns = self.runner_config.get("test_patterns", {})
            if not patterns:
                logger.warning("No test patterns configured")
            return patterns

        except Exception as e:
            logger.error(f"Error loading test patterns: {e}")
            return {}

    def _load_coverage_config(self) -> Dict[str, Any]:
        """Load coverage configuration.

        Returns:
            Coverage configuration dictionary
        """
        try:
            config = self.runner_config.get("coverage", {})
            if not config:
                logger.warning("No coverage configuration")
            return config

        except Exception as e:
            logger.error(f"Error loading coverage config: {e}")
            return {}

    async def _run_tests(self, files: List[str]) -> Dict[str, Any]:
        """Run unit tests.

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

            # Set up coverage
            import coverage
            cov = coverage.Coverage(**self.coverage_config)
            cov.start()

            try:
                # Run tests
                test_results = await self._run_unit_tests(files)
                results["test_results"] = test_results

                # Stop coverage
                cov.stop()
                cov.save()

                # Get coverage data
                coverage_data = self._get_coverage_data(cov, files)
                results["coverage"] = coverage_data

                # Aggregate issues
                results["issues"].extend(test_results.get("issues", []))

                # Update status
                results["status"] = "completed"

            finally:
                # Clean up coverage
                cov.erase()

            return results

        except Exception as e:
            logger.error(f"Error running unit tests: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def _run_unit_tests(
        self,
        files: List[str]
    ) -> Dict[str, Any]:
        """Run unit tests.

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
                "issues": []
            }

            # Import pytest
            import pytest

            # Run tests for each file
            for file in files:
                # Get test modules for file
                modules = self._get_file_test_modules(file)
                if not modules:
                    continue

                # Run file tests
                file_results = await self._run_file_tests(
                    file,
                    modules
                )
                results["issues"].extend(file_results.get("issues", []))

            # Update status
            results["status"] = "completed"

            return results

        except Exception as e:
            logger.error(f"Error running unit tests: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now()
            }

    def _get_file_test_modules(
        self,
        file: str
    ) -> Dict[str, Any]:
        """Get test modules for file.

        Args:
            file: File to get test modules for

        Returns:
            Dictionary of test modules
        """
        try:
            modules = {}
            for module_id, module in self.test_modules.items():
                if file in module.get("files", []):
                    modules[module_id] = module
            return modules

        except Exception as e:
            logger.error(f"Error getting test modules for {file}: {e}")
            return {}

    async def _run_file_tests(
        self,
        file: str,
        modules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run tests for file.

        Args:
            file: File to test
            modules: Test modules to run

        Returns:
            Test results
        """
        try:
            results = {
                "file": file,
                "issues": []
            }

            for module_id, module in modules.items():
                # Run module tests
                module_results = await self._run_module_tests(
                    module_id,
                    module,
                    file
                )
                if module_results.get("issues"):
                    results["issues"].extend([
                        {
                            "id": f"TST-{module_id}-{i}",
                            "type": "test",
                            "module": module_id,
                            "severity": module.get("severity", "medium"),
                            "description": issue.get("description", ""),
                            "test": issue.get("test"),
                            "error": issue.get("error")
                        }
                        for i, issue in enumerate(module_results["issues"])
                    ])

            return results

        except Exception as e:
            logger.error(f"Error running tests for {file}: {e}")
            return {
                "file": file,
                "error": str(e)
            }

    async def _run_module_tests(
        self,
        module_id: str,
        module: Dict[str, Any],
        file: str
    ) -> Dict[str, Any]:
        """Run module tests.

        Args:
            module_id: Module identifier
            module: Module configuration
            file: File being tested

        Returns:
            Module test results
        """
        try:
            results = {
                "module": module_id,
                "issues": []
            }

            # Import test module
            test_module = __import__(
                module["module"],
                fromlist=[module["class"]]
            )

            # Get test class
            test_class = getattr(test_module, module["class"])

            # Create test instance
            instance = test_class(file=file)

            # Run tests
            for test_name in dir(instance):
                if test_name.startswith("test_"):
                    test_func = getattr(instance, test_name)
                    try:
                        await test_func()
                    except Exception as e:
                        results["issues"].append({
                            "test": test_name,
                            "description": str(e),
                            "error": {
                                "type": e.__class__.__name__,
                                "message": str(e),
                                "traceback": e.__traceback__
                            }
                        })

            return results

        except Exception as e:
            logger.error(f"Error running module {module_id}: {e}")
            return {
                "module": module_id,
                "error": str(e)
            }

    def _get_coverage_data(
        self,
        cov: Any,
        files: List[str]
    ) -> Dict[str, Any]:
        """Get coverage data.

        Args:
            cov: Coverage instance
            files: Files tested

        Returns:
            Coverage data dictionary
        """
        try:
            # Get coverage data
            data = cov.get_data()
            total_statements = 0
            covered_statements = 0

            # Calculate coverage for each file
            file_coverage = {}
            for file in files:
                file_data = data.get_file_data(file)
                if file_data:
                    statements = file_data.get("statements", set())
                    missing = file_data.get("missing", set())
                    covered = statements - missing
                    total_statements += len(statements)
                    covered_statements += len(covered)
                    file_coverage[file] = {
                        "total_statements": len(statements),
                        "covered_statements": len(covered),
                        "coverage_percent": (
                            len(covered) / len(statements) * 100
                            if statements else 0
                        )
                    }

            return {
                "total_statements": total_statements,
                "covered_statements": covered_statements,
                "coverage_percent": (
                    covered_statements / total_statements * 100
                    if total_statements > 0 else 0
                ),
                "file_coverage": file_coverage
            }

        except Exception as e:
            logger.error(f"Error getting coverage data: {e}")
            return {
                "total_statements": 0,
                "covered_statements": 0,
                "coverage_percent": 0,
                "file_coverage": {}
            }
