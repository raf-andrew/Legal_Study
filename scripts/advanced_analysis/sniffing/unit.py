#!/usr/bin/env python3
"""
Unit Testing Sniffing Module
This module implements unit testing analysis and validation capabilities
"""

import os
import sys
import logging
import asyncio
import json
import pytest
import coverage
import ast
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from dataclasses import dataclass

from ..config import SNIFFING_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sniffing/unit.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class UnitTestIssue:
    """Data class for unit testing issues"""
    type: str
    severity: str
    description: str
    location: str
    test_name: str
    coverage_type: Optional[str]
    current_coverage: Optional[float]
    required_coverage: Optional[float]
    recommendation: str
    stack_trace: Optional[str] = None

class UnitSniffer:
    """Implements unit testing analysis capabilities"""

    def __init__(self):
        self.config = SNIFFING_CONFIG["domains"]["unit"]
        self.thresholds = self.config["thresholds"]
        self.coverage_types = self.config["coverage_types"]
        self.report_dir = Path("reports/sniffing/unit")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.cov = coverage.Coverage()

    async def sniff_file(self, file_path: str) -> Dict:
        """Perform unit testing sniffing on a file"""
        logger.info(f"Starting unit testing sniffing for file: {file_path}")

        issues = []
        metrics = {}
        coverage_data = {}

        try:
            # Find test files
            test_files = self._find_test_files(file_path)

            # Analyze test quality
            test_quality_issues = await self._analyze_test_quality(file_path, test_files)
            issues.extend(test_quality_issues)

            # Run tests and collect coverage
            test_results = await self._run_tests_with_coverage(file_path, test_files)
            issues.extend(test_results["issues"])
            metrics.update(test_results["metrics"])
            coverage_data.update(test_results["coverage"])

            # Calculate scores
            scores = self._calculate_scores(issues, metrics, coverage_data)

            return {
                "file_path": file_path,
                "domain": "unit",
                "status": "pass" if not issues else "fail",
                "issues": [vars(issue) for issue in issues],
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
                "coverage": self._calculate_total_coverage(coverage_data),
                "scores": scores,
                "audit_info": self._generate_audit_info(file_path, issues, metrics, coverage_data)
            }

        except Exception as e:
            logger.error(f"Error in unit testing sniffing: {e}")
            return self._generate_error_result(file_path, str(e))

    def _find_test_files(self, file_path: str) -> List[str]:
        """Find corresponding test files for a given implementation file"""
        path = Path(file_path)
        potential_test_files = [
            path.parent / f"test_{path.name}",
            path.parent / f"{path.stem}_test{path.suffix}",
            path.parent / "tests" / f"test_{path.name}",
            path.parent.parent / "tests" / f"test_{path.name}"
        ]
        return [str(f) for f in potential_test_files if f.exists()]

    async def _analyze_test_quality(self, file_path: str, test_files: List[str]) -> List[UnitTestIssue]:
        """Analyze the quality of unit tests"""
        issues = []

        for test_file in test_files:
            try:
                with open(test_file, 'r') as f:
                    tree = ast.parse(f.read())

                # Check test structure
                test_visitor = TestAnalysisVisitor(test_file)
                test_visitor.visit(tree)
                issues.extend(test_visitor.issues)

                # Check test coverage requirements
                coverage_issues = self._check_coverage_requirements(test_file)
                issues.extend(coverage_issues)

                # Check test assertions
                assertion_issues = self._check_test_assertions(test_file)
                issues.extend(assertion_issues)

            except Exception as e:
                logger.error(f"Error analyzing test quality for {test_file}: {e}")
                issues.append(UnitTestIssue(
                    type="test_analysis_error",
                    severity="high",
                    description=f"Error analyzing test quality: {str(e)}",
                    location=test_file,
                    test_name="test_quality_analysis",
                    coverage_type=None,
                    current_coverage=None,
                    required_coverage=None,
                    recommendation="Fix test analysis errors",
                    stack_trace=str(e)
                ))

        return issues

    async def _run_tests_with_coverage(self, file_path: str, test_files: List[str]) -> Dict:
        """Run tests and collect coverage information"""
        issues = []
        metrics = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "execution_time": 0.0
        }
        coverage_data = {
            "line": 0.0,
            "branch": 0.0,
            "function": 0.0,
            "statement": 0.0
        }

        try:
            # Start coverage collection
            self.cov.start()

            # Run tests
            for test_file in test_files:
                result = pytest.main(["-v", test_file])

                if result == 0:
                    metrics["passed_tests"] += 1
                else:
                    issues.append(UnitTestIssue(
                        type="test_failure",
                        severity="high",
                        description=f"Unit tests failed in {test_file}",
                        location=test_file,
                        test_name="pytest_execution",
                        coverage_type=None,
                        current_coverage=None,
                        required_coverage=None,
                        recommendation="Fix failing unit tests"
                    ))
                    metrics["failed_tests"] += 1

            # Stop coverage collection
            self.cov.stop()
            self.cov.save()

            # Analyze coverage data
            coverage_data = self._analyze_coverage(file_path)

            # Check coverage thresholds
            coverage_issues = self._check_coverage_thresholds(coverage_data)
            issues.extend(coverage_issues)

        except Exception as e:
            logger.error(f"Error running tests with coverage: {e}")
            issues.append(UnitTestIssue(
                type="coverage_error",
                severity="high",
                description=f"Error collecting coverage: {str(e)}",
                location=file_path,
                test_name="coverage_collection",
                coverage_type=None,
                current_coverage=None,
                required_coverage=None,
                recommendation="Fix coverage collection errors",
                stack_trace=str(e)
            ))

        return {
            "issues": issues,
            "metrics": metrics,
            "coverage": coverage_data
        }

    def _analyze_coverage(self, file_path: str) -> Dict[str, float]:
        """Analyze coverage data"""
        coverage_data = {}

        try:
            # Get coverage analysis
            analysis = self.cov.analysis(file_path)

            # Calculate different types of coverage
            total_lines = len(analysis[1]) + len(analysis[2])
            covered_lines = len(analysis[1])

            coverage_data["line"] = (covered_lines / total_lines * 100) if total_lines > 0 else 0.0
            coverage_data["branch"] = self.cov.get_branch_coverage() or 0.0
            coverage_data["function"] = self._calculate_function_coverage(file_path) or 0.0
            coverage_data["statement"] = self.cov.get_statement_coverage() or 0.0

        except Exception as e:
            logger.error(f"Error analyzing coverage: {e}")

        return coverage_data

    def _check_coverage_thresholds(self, coverage_data: Dict[str, float]) -> List[UnitTestIssue]:
        """Check if coverage meets thresholds"""
        issues = []

        for coverage_type, coverage in coverage_data.items():
            threshold = self.thresholds.get(f"min_{coverage_type}_coverage",
                                          self.thresholds["min_coverage"])

            if coverage < threshold:
                issues.append(UnitTestIssue(
                    type="coverage_threshold",
                    severity="high",
                    description=f"{coverage_type.capitalize()} coverage below threshold",
                    location="coverage_report",
                    test_name="coverage_analysis",
                    coverage_type=coverage_type,
                    current_coverage=coverage,
                    required_coverage=threshold,
                    recommendation=f"Increase {coverage_type} coverage to meet threshold"
                ))

        return issues

    def _calculate_function_coverage(self, file_path: str) -> float:
        """Calculate function coverage"""
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())

            function_visitor = FunctionVisitor()
            function_visitor.visit(tree)

            total_functions = len(function_visitor.functions)
            covered_functions = sum(1 for func in function_visitor.functions
                                 if self.cov.analysis(file_path)[1] & func.lineno)

            return (covered_functions / total_functions * 100) if total_functions > 0 else 0.0

        except Exception as e:
            logger.error(f"Error calculating function coverage: {e}")
            return 0.0

    def _check_test_assertions(self, test_file: str) -> List[UnitTestIssue]:
        """Check test assertions"""
        issues = []

        try:
            with open(test_file, 'r') as f:
                tree = ast.parse(f.read())

            assertion_visitor = AssertionVisitor(test_file)
            assertion_visitor.visit(tree)
            issues.extend(assertion_visitor.issues)

        except Exception as e:
            logger.error(f"Error checking test assertions: {e}")

        return issues

    def _calculate_scores(self, issues: List[UnitTestIssue], metrics: Dict,
                         coverage_data: Dict[str, float]) -> Dict[str, float]:
        """Calculate unit testing scores"""
        scores = {
            "unit": 100.0,
            "coverage": sum(coverage_data.values()) / len(coverage_data) if coverage_data else 0.0,
            "quality": 100.0
        }

        # Reduce scores based on issues
        for issue in issues:
            if issue.severity == "critical":
                scores["unit"] -= 20.0
            elif issue.severity == "high":
                scores["unit"] -= 10.0
            elif issue.severity == "medium":
                scores["unit"] -= 5.0
            elif issue.severity == "low":
                scores["unit"] -= 2.0

        # Adjust quality score based on metrics
        if metrics:
            total_tests = metrics["total_tests"]
            if total_tests > 0:
                scores["quality"] = (metrics["passed_tests"] / total_tests) * 100.0

        # Ensure scores don't go below 0
        return {k: max(0.0, v) for k, v in scores.items()}

    def _calculate_total_coverage(self, coverage_data: Dict[str, float]) -> float:
        """Calculate total coverage score"""
        if not coverage_data:
            return 0.0
        return sum(coverage_data.values()) / len(coverage_data)

    def _generate_audit_info(self, file_path: str, issues: List[UnitTestIssue],
                           metrics: Dict, coverage_data: Dict[str, float]) -> Dict:
        """Generate audit information"""
        return {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "coverage_types_analyzed": list(coverage_data.keys()),
            "total_issues": len(issues),
            "metrics": metrics,
            "coverage_data": coverage_data,
            "compliance": {
                "coverage_threshold_met": all(
                    cov >= self.thresholds["min_coverage"]
                    for cov in coverage_data.values()
                ),
                "test_quality_met": len([i for i in issues if i.severity in ["critical", "high"]]) == 0
            }
        }

    def _generate_error_result(self, file_path: str, error: str) -> Dict:
        """Generate error result"""
        return {
            "file_path": file_path,
            "domain": "unit",
            "status": "error",
            "issues": [{
                "type": "sniffing_error",
                "severity": "critical",
                "description": f"Error during unit testing sniffing: {error}",
                "location": file_path,
                "recommendation": "Fix sniffing execution errors"
            }],
            "metrics": {},
            "timestamp": datetime.now().isoformat(),
            "coverage": 0.0,
            "scores": {"unit": 0.0},
            "audit_info": {
                "timestamp": datetime.now().isoformat(),
                "error": error
            }
        }

class TestAnalysisVisitor(ast.NodeVisitor):
    """AST visitor for analyzing test structure"""

    def __init__(self, file_path: str):
        self.issues = []
        self.file_path = file_path
        self.current_class = None
        self.current_function = None

    def visit_ClassDef(self, node):
        self.current_class = node.name
        if not node.name.startswith('Test'):
            self.issues.append(UnitTestIssue(
                type="test_naming",
                severity="low",
                description="Test class should start with 'Test'",
                location=f"{self.file_path}:{node.lineno}",
                test_name=node.name,
                coverage_type=None,
                current_coverage=None,
                required_coverage=None,
                recommendation="Rename class to start with 'Test'"
            ))
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        self.current_function = node.name
        if self.current_class and not node.name.startswith('test_'):
            self.issues.append(UnitTestIssue(
                type="test_naming",
                severity="low",
                description="Test method should start with 'test_'",
                location=f"{self.file_path}:{node.lineno}",
                test_name=node.name,
                coverage_type=None,
                current_coverage=None,
                required_coverage=None,
                recommendation="Rename method to start with 'test_'"
            ))
        self.generic_visit(node)
        self.current_function = None

class FunctionVisitor(ast.NodeVisitor):
    """AST visitor for collecting function information"""

    def __init__(self):
        self.functions = set()

    def visit_FunctionDef(self, node):
        self.functions.add(node)
        self.generic_visit(node)

class AssertionVisitor(ast.NodeVisitor):
    """AST visitor for analyzing test assertions"""

    def __init__(self, file_path: str):
        self.issues = []
        self.file_path = file_path
        self.assertions = set()

    def visit_Assert(self, node):
        self.assertions.add(node)
        if isinstance(node.test, ast.Compare) and len(node.test.ops) == 1:
            if isinstance(node.test.ops[0], ast.Eq):
                self.issues.append(UnitTestIssue(
                    type="assertion_quality",
                    severity="low",
                    description="Consider using assertEqual instead of plain assert",
                    location=f"{self.file_path}:{node.lineno}",
                    test_name="assertion_analysis",
                    coverage_type=None,
                    current_coverage=None,
                    required_coverage=None,
                    recommendation="Use assertEqual for better error messages"
                ))
        self.generic_visit(node)

async def main():
    """Main function"""
    try:
        sniffer = UnitSniffer()
        result = await sniffer.sniff_file("example.py")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Unit testing sniffing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
