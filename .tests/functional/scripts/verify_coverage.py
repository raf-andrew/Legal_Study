#!/usr/bin/env python3
"""
Verify test coverage and generate certification reports.
"""
import os
import sys
import json
import yaml
from datetime import datetime
from pathlib import Path
import logging
from typing import Dict, List, Optional

from test_config import (
    TEST_CATEGORIES,
    TEST_DIRS,
    CERTIFICATION_REQUIREMENTS,
    get_test_category,
    get_required_coverage
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CoverageVerifier:
    """Verifies test coverage and generates certification reports."""

    def __init__(self):
        self.config_path = Path(__file__).parent.parent / 'config'
        self.reports_path = Path(__file__).parent.parent / 'reports'
        self.evidence_path = Path(__file__).parent.parent / 'evidence'

        # Load configuration
        with open(self.config_path / 'test_categories.yaml') as f:
            self.config = yaml.safe_load(f)

    def verify_coverage(self, category: str) -> Dict:
        """Verify coverage for a specific category."""
        test_category = get_test_category(category)
        required_coverage = test_category.min_coverage

        # Load coverage report
        coverage_file = self.reports_path / 'coverage' / category / 'coverage.json'
        if not coverage_file.exists():
            logger.error(f"No coverage report found for {category}")
            return {
                'status': 'failed',
                'message': 'No coverage report found',
                'required_coverage': required_coverage,
                'actual_coverage': 0.0
            }

        with open(coverage_file) as f:
            coverage_data = json.load(f)

        # Calculate coverage
        total_lines = coverage_data['totals']['num_statements']
        covered_lines = coverage_data['totals']['covered_statements']
        actual_coverage = (covered_lines / total_lines) * 100 if total_lines > 0 else 0

        return {
            'status': 'passed' if actual_coverage >= required_coverage else 'failed',
            'required_coverage': required_coverage,
            'actual_coverage': actual_coverage,
            'total_lines': total_lines,
            'covered_lines': covered_lines
        }

    def verify_evidence(self, category: str) -> Dict:
        """Verify evidence collection for a category."""
        test_category = get_test_category(category)
        required_evidence = test_category.required_evidence

        # Check evidence files
        evidence_dir = self.evidence_path / category
        if not evidence_dir.exists():
            logger.error(f"No evidence directory found for {category}")
            return {
                'status': 'failed',
                'message': 'No evidence directory found',
                'required_evidence': required_evidence,
                'collected_evidence': []
            }

        collected_evidence = []
        for evidence_type in required_evidence:
            evidence_file = evidence_dir / f"{evidence_type}.json"
            if evidence_file.exists():
                collected_evidence.append(evidence_type)

        return {
            'status': 'passed' if len(collected_evidence) == len(required_evidence) else 'failed',
            'required_evidence': required_evidence,
            'collected_evidence': collected_evidence
        }

    def verify_steps(self, category: str) -> Dict:
        """Verify required steps for a category."""
        test_category = get_test_category(category)
        required_steps = test_category.required_steps

        # Load test results
        results_file = self.reports_path / 'verification' / f"{category}_results.json"
        if not results_file.exists():
            logger.error(f"No test results found for {category}")
            return {
                'status': 'failed',
                'message': 'No test results found',
                'required_steps': required_steps,
                'completed_steps': []
            }

        with open(results_file) as f:
            results = json.load(f)

        completed_steps = [
            step['name']
            for step in results.get('steps', [])
            if step['status'] == 'passed'
        ]

        return {
            'status': 'passed' if len(completed_steps) == len(required_steps) else 'failed',
            'required_steps': required_steps,
            'completed_steps': completed_steps
        }

    def generate_certification(self, category: str) -> Dict:
        """Generate certification report for a category."""
        coverage_result = self.verify_coverage(category)
        evidence_result = self.verify_evidence(category)
        steps_result = self.verify_steps(category)

        certification = {
            'category': category,
            'timestamp': datetime.now().isoformat(),
            'coverage_verification': coverage_result,
            'evidence_verification': evidence_result,
            'steps_verification': steps_result,
            'overall_status': 'passed' if all(
                result['status'] == 'passed'
                for result in [coverage_result, evidence_result, steps_result]
            ) else 'failed'
        }

        # Save certification
        cert_file = self.reports_path / 'certification' / f"{category}_certification.json"
        cert_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cert_file, 'w') as f:
            json.dump(certification, f, indent=2)

        logger.info(f"Generated certification for {category}")
        return certification

    def verify_all(self):
        """Verify all categories and generate summary report."""
        results = {}
        for category in TEST_CATEGORIES:
            results[category] = self.generate_certification(category)

        # Generate summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'categories': results,
            'overall_status': 'passed' if all(
                result['overall_status'] == 'passed'
                for result in results.values()
            ) else 'failed'
        }

        # Save summary
        summary_file = self.reports_path / 'certification' / 'certification_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Generated certification summary")
        return summary

def main():
    """Main entry point for coverage verification."""
    try:
        verifier = CoverageVerifier()
        summary = verifier.verify_all()

        if summary['overall_status'] == 'passed':
            logger.info("All categories passed verification")
            return 0
        else:
            logger.error("Some categories failed verification")
            return 1

    except Exception as e:
        logger.error(f"Error verifying coverage: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
