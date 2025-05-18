#!/usr/bin/env python3
"""
Functional Sniffing Module
This module implements functional testing and validation capabilities
"""

import os
import sys
import logging
import asyncio
import json
import pytest
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from ..config import SNIFFING_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sniffing/functional.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class FunctionalIssue:
    """Data class for functional testing issues"""
    type: str
    severity: str
    description: str
    location: str
    test_name: str
    expected: Any
    actual: Any
    recommendation: str
    stack_trace: Optional[str] = None

class FunctionalSniffer:
    """Implements functional testing capabilities"""

    def __init__(self):
        self.config = SNIFFING_CONFIG["domains"]["functional"]
        self.thresholds = self.config["thresholds"]
        self.test_types = self.config["test_types"]
        self.report_dir = Path("reports/sniffing/functional")
        self.report_dir.mkdir(parents=True, exist_ok=True)

    async def sniff_file(self, file_path: str) -> Dict:
        """Perform functional sniffing on a file"""
        logger.info(f"Starting functional sniffing for file: {file_path}")

        issues = []
        metrics = {}
        coverage = 0.0

        try:
            # Identify test files and implementation files
            test_files = self._find_test_files(file_path)

            # Run different types of tests
            for test_type in self.test_types:
                test_results = await self._run_tests(test_type, file_path, test_files)
                issues.extend(test_results["issues"])
                metrics.update(test_results["metrics"])
                coverage += test_results["coverage"] / len(self.test_types)

            # Calculate scores
            scores = self._calculate_scores(issues, metrics)

            return {
                "file_path": file_path,
                "domain": "functional",
                "status": "pass" if not issues else "fail",
                "issues": [vars(issue) for issue in issues],
                "metrics": metrics,
                "timestamp": datetime.now().isoformat(),
                "coverage": coverage,
                "scores": scores,
                "audit_info": self._generate_audit_info(file_path, issues, metrics)
            }

        except Exception as e:
            logger.error(f"Error in functional sniffing: {e}")
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

    async def _run_tests(self, test_type: str, file_path: str, test_files: List[str]) -> Dict:
        """Run specific type of tests"""
        issues = []
        metrics = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "execution_time": 0.0
        }

        if test_type == "unit":
            result = await self._run_unit_tests(test_files)
        elif test_type == "integration":
            result = await self._run_integration_tests(file_path)
        elif test_type == "e2e":
            result = await self._run_e2e_tests(file_path)
        elif test_type == "regression":
            result = await self._run_regression_tests(file_path)
        else:
            logger.warning(f"Unknown test type: {test_type}")
            return {"issues": [], "metrics": metrics, "coverage": 0.0}

        issues.extend(result["issues"])
        metrics.update(result["metrics"])

        return {
            "issues": issues,
            "metrics": metrics,
            "coverage": self._calculate_coverage(metrics)
        }

    async def _run_unit_tests(self, test_files: List[str]) -> Dict:
        """Run unit tests"""
        issues = []
        metrics = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "execution_time": 0.0
        }

        for test_file in test_files:
            try:
                # Run pytest programmatically
                result = pytest.main(["-v", test_file])

                # Process test results
                if result == 0:  # All tests passed
                    metrics["passed_tests"] += 1
                else:
                    issues.append(FunctionalIssue(
                        type="unit_test",
                        severity="high",
                        description=f"Unit tests failed in {test_file}",
                        location=test_file,
                        test_name="unit_tests",
                        expected="All tests to pass",
                        actual=f"Failed with exit code {result}",
                        recommendation="Fix failing unit tests"
                    ))
                    metrics["failed_tests"] += 1

            except Exception as e:
                logger.error(f"Error running unit tests: {e}")
                issues.append(FunctionalIssue(
                    type="unit_test_error",
                    severity="high",
                    description=f"Error running unit tests: {str(e)}",
                    location=test_file,
                    test_name="unit_tests",
                    expected="Tests to run successfully",
                    actual=str(e),
                    recommendation="Fix test execution errors",
                    stack_trace=str(e)
                ))

        return {"issues": issues, "metrics": metrics}

    async def _run_integration_tests(self, file_path: str) -> Dict:
        """Run integration tests"""
        # Implementation would run integration tests
        return {"issues": [], "metrics": {}}

    async def _run_e2e_tests(self, file_path: str) -> Dict:
        """Run end-to-end tests"""
        # Implementation would run e2e tests
        return {"issues": [], "metrics": {}}

    async def _run_regression_tests(self, file_path: str) -> Dict:
        """Run regression tests"""
        # Implementation would run regression tests
        return {"issues": [], "metrics": {}}

    def _calculate_coverage(self, metrics: Dict) -> float:
        """Calculate test coverage"""
        if metrics["total_tests"] == 0:
            return 0.0
        return (metrics["passed_tests"] / metrics["total_tests"]) * 100.0

    def _calculate_scores(self, issues: List[FunctionalIssue], metrics: Dict) -> Dict[str, float]:
        """Calculate functional testing scores"""
        scores = {
            "functional": 100.0,
            "coverage": self._calculate_coverage(metrics),
            "reliability": 100.0
        }

        # Reduce scores based on issues
        for issue in issues:
            if issue.severity == "critical":
                scores["functional"] -= 20.0
            elif issue.severity == "high":
                scores["functional"] -= 10.0
            elif issue.severity == "medium":
                scores["functional"] -= 5.0
            elif issue.severity == "low":
                scores["functional"] -= 2.0

        # Ensure scores don't go below 0
        return {k: max(0.0, v) for k, v in scores.items()}

    def _generate_audit_info(self, file_path: str, issues: List[FunctionalIssue], metrics: Dict) -> Dict:
        """Generate audit information"""
        return {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "test_types_executed": self.test_types,
            "total_issues": len(issues),
            "metrics": metrics,
            "compliance": {
                "functional_requirements_met": len(issues) == 0,
                "coverage_threshold_met": metrics.get("coverage", 0) >= self.thresholds["min_functional_score"]
            }
        }

    def _generate_error_result(self, file_path: str, error: str) -> Dict:
        """Generate error result"""
        return {
            "file_path": file_path,
            "domain": "functional",
            "status": "error",
            "issues": [{
                "type": "sniffing_error",
                "severity": "critical",
                "description": f"Error during functional sniffing: {error}",
                "location": file_path,
                "recommendation": "Fix sniffing execution errors"
            }],
            "metrics": {},
            "timestamp": datetime.now().isoformat(),
            "coverage": 0.0,
            "scores": {"functional": 0.0},
            "audit_info": {
                "timestamp": datetime.now().isoformat(),
                "error": error
            }
        }

async def main():
    """Main function"""
    try:
        sniffer = FunctionalSniffer()
        result = await sniffer.sniff_file("example.py")
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Functional sniffing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
