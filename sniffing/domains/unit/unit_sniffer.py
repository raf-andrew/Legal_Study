"""
Enhanced unit sniffer for coverage analysis, test quality metrics, and performance benchmarking.
"""
import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ...core.base.base_sniffer import BaseSniffer
from ...core.utils.result import SniffingResult

logger = logging.getLogger("unit_sniffer")

class UnitSniffer(BaseSniffer):
    """Enhanced sniffer for unit testing and code quality analysis."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize unit sniffer.

        Args:
            config: Configuration dictionary for the sniffer
        """
        super().__init__(config)
        self.coverage_checks = self._load_coverage_checks()
        self.quality_checks = self._load_quality_checks()
        self.benchmark_checks = self._load_benchmark_checks()
        self.ai_unit_model = self._load_ai_unit_model()

    def get_sniffer_type(self) -> str:
        """Return the type of this sniffer."""
        return "unit"

    def _load_coverage_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load coverage check patterns."""
        return {
            "test_function": {
                "pattern": r"def\s+test_\w+\s*\([^)]*\):",
                "severity": "high",
                "description": "Test function definition",
                "fix_template": "Add test function for untested code"
            },
            "assertion": {
                "pattern": r"assert\s+|self\.assert\w+|pytest\.assert\w+",
                "severity": "high",
                "description": "Test assertion",
                "fix_template": "Add assertions to verify behavior"
            },
            "mock": {
                "pattern": r"@mock\.|mock\.|MagicMock|patch",
                "severity": "medium",
                "description": "Test mock usage",
                "fix_template": "Add mocks for external dependencies"
            },
            "fixture": {
                "pattern": r"@pytest\.fixture|@fixture",
                "severity": "medium",
                "description": "Test fixture definition",
                "fix_template": "Add fixtures for test setup"
            },
            "parametrize": {
                "pattern": r"@pytest\.mark\.parametrize",
                "severity": "medium",
                "description": "Test parametrization",
                "fix_template": "Add parametrized tests for edge cases"
            }
        }

    def _load_quality_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load test quality check patterns."""
        return {
            "test_isolation": {
                "pattern": r"global\s+|nonlocal\s+",
                "severity": "high",
                "description": "Test isolation issue",
                "fix_template": "Ensure test isolation"
            },
            "test_naming": {
                "pattern": r"def\s+test_\w+\s*\([^)]*\):",
                "severity": "medium",
                "description": "Test naming convention",
                "fix_template": "Follow test naming conventions"
            },
            "test_size": {
                "pattern": r"def\s+test_\w+[\s\S]*?(?=def|\Z)",
                "severity": "medium",
                "description": "Test function size",
                "fix_template": "Break down large test functions"
            },
            "assertion_message": {
                "pattern": r"assert\s+[^,]+(?!,)",
                "severity": "medium",
                "description": "Missing assertion message",
                "fix_template": "Add descriptive assertion messages"
            },
            "test_documentation": {
                "pattern": r'def\s+test_\w+\s*\([^)]*\):\s*(?![\s\n]*["\']))',
                "severity": "medium",
                "description": "Missing test documentation",
                "fix_template": "Add test function documentation"
            }
        }

    def _load_benchmark_checks(self) -> Dict[str, Dict[str, Any]]:
        """Load benchmark check patterns."""
        return {
            "performance_test": {
                "pattern": r"@pytest\.mark\.benchmark|benchmark\(",
                "severity": "medium",
                "description": "Performance benchmark",
                "fix_template": "Add performance benchmarks"
            },
            "memory_test": {
                "pattern": r"@pytest\.mark\.memory|memory_profiler",
                "severity": "medium",
                "description": "Memory usage test",
                "fix_template": "Add memory usage tests"
            },
            "timing": {
                "pattern": r"time\.|timeit\.|perf_counter",
                "severity": "medium",
                "description": "Timing measurement",
                "fix_template": "Add timing measurements"
            },
            "resource_cleanup": {
                "pattern": r"@pytest\.fixture\s*\([^)]*autouse=True",
                "severity": "medium",
                "description": "Resource cleanup",
                "fix_template": "Add automatic resource cleanup"
            }
        }

    def _load_ai_unit_model(self) -> Any:
        """Load AI unit testing analysis model."""
        try:
            return self.ai_analyzer.load_unit_model()
        except Exception as e:
            logger.error(f"Error loading AI unit model: {e}")
            return None

    async def _sniff_file_impl(self, file: str) -> SniffingResult:
        """Implementation of file sniffing logic.

        Args:
            file: Path to the file to sniff.

        Returns:
            SniffingResult object
        """
        try:
            # Create result
            result = SniffingResult(file, self.get_sniffer_type())

            # Read file content
            with open(file, "r") as f:
                content = f.read()

            # Run unit test checks
            await self._check_coverage(content, result)
            await self._check_quality(content, result)
            await self._check_benchmarks(content, result)
            await self._run_ai_unit_analysis(content, result)

            # Update status
            result.status = not result.has_critical_issues()

            return result

        except Exception as e:
            logger.error(f"Error sniffing file {file}: {e}")
            return SniffingResult(file, self.get_sniffer_type(), status=False)

    async def _check_coverage(self, content: str, result: SniffingResult) -> None:
        """Check test coverage.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            # Parse code into AST
            tree = ast.parse(content)

            # Find all functions and classes
            functions = [
                node for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            classes = [
                node for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
            ]

            # Check coverage patterns
            for check_type, check_info in self.coverage_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                matches = list(matches)

                # Add coverage metrics
                result.update_metrics({
                    f"coverage_{check_type}_count": len(matches)
                })

                # Calculate coverage ratios
                if check_type == "test_function":
                    test_functions = len(matches)
                    total_functions = len(functions)
                    if total_functions > 0:
                        coverage_ratio = test_functions / total_functions
                        result.update_metrics({
                            "function_coverage_ratio": coverage_ratio
                        })
                        if coverage_ratio < 0.8:  # 80% coverage threshold
                            result.add_issue({
                                "type": "coverage",
                                "subtype": "low_function_coverage",
                                "severity": "high",
                                "description": "Low function test coverage",
                                "coverage": coverage_ratio,
                                "fix_suggestion": check_info["fix_template"]
                            })

                elif check_type == "assertion":
                    assertions = len(matches)
                    if test_functions > 0:
                        assertion_ratio = assertions / test_functions
                        result.update_metrics({
                            "assertion_density": assertion_ratio
                        })
                        if assertion_ratio < 2:  # At least 2 assertions per test
                            result.add_issue({
                                "type": "coverage",
                                "subtype": "low_assertion_density",
                                "severity": "medium",
                                "description": "Low assertion density",
                                "density": assertion_ratio,
                                "fix_suggestion": check_info["fix_template"]
                            })

            # Run AI coverage analysis
            if self.ai_unit_model:
                ai_issues = await self.ai_analyzer.check_coverage(
                    content,
                    self.ai_unit_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking coverage: {e}")

    async def _check_quality(self, content: str, result: SniffingResult) -> None:
        """Check test quality.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for check_type, check_info in self.quality_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    # Get matched code and context
                    line_num = content.count("\n", 0, match.start()) + 1
                    matched_code = match.group(0).strip()

                    # Check specific quality issues
                    if check_type == "test_size":
                        # Check test function size
                        test_code = matched_code.split("\n")
                        if len(test_code) > 50:  # Test too long
                            result.add_issue({
                                "type": "quality",
                                "subtype": "test_size",
                                "severity": check_info["severity"],
                                "description": "Test function too long",
                                "line": line_num,
                                "code": matched_code[:100] + "...",
                                "size": len(test_code),
                                "fix_suggestion": check_info["fix_template"]
                            })

                    elif check_type == "test_isolation":
                        # Found potential isolation issue
                        result.add_issue({
                            "type": "quality",
                            "subtype": "test_isolation",
                            "severity": check_info["severity"],
                            "description": "Potential test isolation issue",
                            "line": line_num,
                            "code": matched_code,
                            "fix_suggestion": check_info["fix_template"]
                        })

                    elif check_type == "assertion_message":
                        # Missing assertion message
                        result.add_issue({
                            "type": "quality",
                            "subtype": "assertion_message",
                            "severity": check_info["severity"],
                            "description": "Missing assertion message",
                            "line": line_num,
                            "code": matched_code,
                            "fix_suggestion": check_info["fix_template"]
                        })

            # Run AI quality analysis
            if self.ai_unit_model:
                ai_issues = await self.ai_analyzer.check_quality(
                    content,
                    self.ai_unit_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking quality: {e}")

    async def _check_benchmarks(self, content: str, result: SniffingResult) -> None:
        """Check performance benchmarks.

        Args:
            content: File content to check
            result: SniffingResult to update
        """
        try:
            for check_type, check_info in self.benchmark_checks.items():
                matches = re.finditer(check_info["pattern"], content, re.MULTILINE)
                for match in matches:
                    # Get matched code and context
                    line_num = content.count("\n", 0, match.start()) + 1
                    matched_code = match.group(0).strip()

                    # Add benchmark metrics
                    result.update_metrics({
                        f"benchmark_{check_type}_count": 1
                    })

                    # Check for specific benchmark issues
                    if check_type == "performance_test":
                        # Check benchmark configuration
                        if "min_rounds" not in matched_code:
                            result.add_issue({
                                "type": "benchmark",
                                "subtype": "performance_config",
                                "severity": check_info["severity"],
                                "description": "Missing benchmark configuration",
                                "line": line_num,
                                "code": matched_code,
                                "fix_suggestion": "Add min_rounds to benchmark configuration"
                            })

                    elif check_type == "memory_test":
                        # Check memory profiling configuration
                        if "max_memory" not in matched_code:
                            result.add_issue({
                                "type": "benchmark",
                                "subtype": "memory_config",
                                "severity": check_info["severity"],
                                "description": "Missing memory limit configuration",
                                "line": line_num,
                                "code": matched_code,
                                "fix_suggestion": "Add max_memory to test configuration"
                            })

            # Run AI benchmark analysis
            if self.ai_unit_model:
                ai_issues = await self.ai_analyzer.check_benchmarks(
                    content,
                    self.ai_unit_model
                )
                for issue in ai_issues:
                    result.add_issue(issue)

        except Exception as e:
            logger.error(f"Error checking benchmarks: {e}")

    async def _run_ai_unit_analysis(self, content: str, result: SniffingResult) -> None:
        """Run AI-powered unit test analysis.

        Args:
            content: File content to analyze
            result: SniffingResult to update
        """
        try:
            if self.ai_unit_model:
                # Run comprehensive AI analysis
                analysis = await self.ai_analyzer.analyze_unit_tests(
                    content,
                    self.ai_unit_model
                )

                # Add issues from AI analysis
                for issue in analysis.get("issues", []):
                    result.add_issue(issue)

                # Update metrics
                result.update_metrics({
                    "ai_unit_analysis": {
                        "coverage_score": analysis.get("coverage_score", 0.0),
                        "quality_score": analysis.get("quality_score", 0.0),
                        "performance_score": analysis.get("performance_score", 0.0)
                    }
                })

        except Exception as e:
            logger.error(f"Error running AI unit analysis: {e}")

    async def _apply_fixes(self, suggestions: List[Dict[str, Any]]) -> bool:
        """Apply fix suggestions to issues.

        Args:
            suggestions: List of fix suggestions from AI

        Returns:
            True if all fixes were applied successfully, False otherwise
        """
        try:
            success = True
            for suggestion in suggestions:
                # Get file content
                with open(suggestion["file"], "r") as f:
                    content = f.read()

                # Apply fix
                if suggestion.get("fix_type") == "replace":
                    content = content.replace(
                        suggestion["old_code"],
                        suggestion["new_code"]
                    )
                elif suggestion.get("fix_type") == "insert":
                    lines = content.splitlines()
                    lines.insert(
                        suggestion["line"] - 1,
                        suggestion["code"]
                    )
                    content = "\n".join(lines)
                else:
                    logger.warning(f"Unknown fix type: {suggestion.get('fix_type')}")
                    success = False
                    continue

                # Write fixed content
                with open(suggestion["file"], "w") as f:
                    f.write(content)

                # Validate fix
                if not await self._validate_fix(suggestion, content):
                    success = False

            return success

        except Exception as e:
            logger.error(f"Error applying fixes: {e}")
            return False

    async def _validate_fix(self, suggestion: Dict[str, Any], content: str) -> bool:
        """Validate that a fix was successful.

        Args:
            suggestion: Fix suggestion that was applied
            content: Updated file content

        Returns:
            True if fix was successful, False otherwise
        """
        try:
            # Create temporary result
            result = SniffingResult(suggestion["file"], self.get_sniffer_type())

            # Run unit test checks on updated content
            await self._check_coverage(content, result)
            await self._check_quality(content, result)
            await self._check_benchmarks(content, result)

            # Check if original issue was fixed
            for issue in result.issues:
                if (
                    issue["type"] == suggestion.get("issue_type") and
                    issue["subtype"] == suggestion.get("issue_subtype")
                ):
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating fix: {e}")
            return False
