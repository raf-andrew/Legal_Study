"""
Systematic functional test runner with medical-grade verification and reporting.
"""
import os
import json
import logging
import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

@dataclass
class TestResult:
    """Represents a single test result with verification steps."""
    test_id: str
    test_name: str
    status: str
    start_time: str
    end_time: str
    duration: float
    coverage: float
    verification_steps: List[Dict]
    checklist_items: List[str]
    evidence_files: List[str]
    certifier: Optional[str] = None
    certification_time: Optional[str] = None

class FunctionalTestRunner:
    """Handles execution and reporting of functional tests with medical-grade verification."""

    def __init__(self, report_dir: str = "reports/functional_tests"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.current_test = None
        self.test_results = []

        # Setup logging
        self.log_dir = self.report_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            filename=self.log_dir / f"test_run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def start_test(self, test_id: str, test_name: str, checklist_items: List[str]):
        """Start a new test session."""
        self.current_test = TestResult(
            test_id=test_id,
            test_name=test_name,
            status="running",
            start_time=datetime.datetime.now().isoformat(),
            end_time="",
            duration=0.0,
            coverage=0.0,
            verification_steps=[],
            checklist_items=checklist_items,
            evidence_files=[]
        )
        logging.info(f"Starting test: {test_name} (ID: {test_id})")

    def add_verification_step(self, step_name: str, status: str, details: str):
        """Add a verification step to the current test."""
        if not self.current_test:
            raise RuntimeError("No active test session")

        step = {
            "name": step_name,
            "status": status,
            "details": details,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.current_test.verification_steps.append(step)
        logging.info(f"Verification step: {step_name} - {status}")

    def add_evidence_file(self, file_path: str):
        """Add an evidence file to the current test."""
        if not self.current_test:
            raise RuntimeError("No active test session")

        evidence_dir = self.report_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)

        # Copy evidence file to report directory
        source_path = Path(file_path)
        dest_path = evidence_dir / source_path.name
        if source_path.exists():
            import shutil
            shutil.copy2(source_path, dest_path)
            self.current_test.evidence_files.append(str(dest_path))
            logging.info(f"Added evidence file: {file_path}")

    def complete_test(self, status: str, coverage: float):
        """Complete the current test session."""
        if not self.current_test:
            raise RuntimeError("No active test session")

        end_time = datetime.datetime.now()
        start_time = datetime.datetime.fromisoformat(self.current_test.start_time)
        duration = (end_time - start_time).total_seconds()

        self.current_test.status = status
        self.current_test.end_time = end_time.isoformat()
        self.current_test.duration = duration
        self.current_test.coverage = coverage

        # Save individual test report
        test_report_path = self.report_dir / f"test_{self.current_test.test_id}.json"
        with open(test_report_path, 'w') as f:
            json.dump(asdict(self.current_test), f, indent=2)

        self.test_results.append(self.current_test)
        logging.info(f"Completed test: {self.current_test.test_name} - Status: {status}")
        self.current_test = None

    def certify_test(self, test_id: str, certifier: str):
        """Certify a completed test."""
        test = next((t for t in self.test_results if t.test_id == test_id), None)
        if not test:
            raise ValueError(f"Test {test_id} not found")

        test.certifier = certifier
        test.certification_time = datetime.datetime.now().isoformat()

        # Update test report
        test_report_path = self.report_dir / f"test_{test_id}.json"
        with open(test_report_path, 'w') as f:
            json.dump(asdict(test), f, indent=2)

        logging.info(f"Test {test_id} certified by {certifier}")

    def generate_summary_report(self):
        """Generate a summary report of all tests."""
        summary = {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "passed_tests": sum(1 for t in self.test_results if t.status == "passed"),
            "failed_tests": sum(1 for t in self.test_results if t.status == "failed"),
            "average_coverage": sum(t.coverage for t in self.test_results) / len(self.test_results) if self.test_results else 0,
            "tests": [asdict(t) for t in self.test_results]
        }

        summary_path = self.report_dir / "summary_report.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        logging.info("Generated summary report")
        return summary
