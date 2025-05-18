#!/usr/bin/env python3

import argparse
import json
import os
import sys
from datetime import datetime
from xml.etree import ElementTree

def parse_coverage_report(coverage_file):
    """Parse coverage XML report and return coverage metrics."""
    tree = ElementTree.parse(coverage_file)
    root = tree.getroot()

    coverage_data = {
        'line_coverage': 0,
        'branch_coverage': 0,
        'function_coverage': 0,
        'covered_lines': 0,
        'total_lines': 0
    }

    for package in root.findall('.//package'):
        for file in package.findall('file'):
            coverage_data['covered_lines'] += int(file.get('line-rate', 0) * int(file.get('lines-valid', 0)))
            coverage_data['total_lines'] += int(file.get('lines-valid', 0))

    if coverage_data['total_lines'] > 0:
        coverage_data['line_coverage'] = (coverage_data['covered_lines'] / coverage_data['total_lines']) * 100

    return coverage_data

def parse_test_report(test_report_file):
    """Parse pytest HTML report and return test results."""
    with open(test_report_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract test results using basic parsing
    passed = content.count('passed')
    failed = content.count('failed')
    skipped = content.count('skipped')
    total = passed + failed + skipped

    return {
        'total_tests': total,
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'pass_rate': (passed / total * 100) if total > 0 else 0
    }

def generate_verification_report(test_report, coverage_report, output_file):
    """Generate a comprehensive verification report."""
    test_results = parse_test_report(test_report)
    coverage_data = parse_coverage_report(coverage_report)

    verification_report = {
        'timestamp': datetime.now().isoformat(),
        'test_results': test_results,
        'coverage_data': coverage_data,
        'verification_status': {
            'passed': test_results['failed'] == 0,
            'coverage_adequate': coverage_data['line_coverage'] >= 90,
            'all_tests_executed': test_results['skipped'] == 0
        },
        'requirements_met': {
            'test_coverage': coverage_data['line_coverage'] >= 90,
            'test_pass_rate': test_results['pass_rate'] == 100,
            'no_skipped_tests': test_results['skipped'] == 0
        }
    }

    # Write verification report
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(verification_report, f, indent=2)

    return verification_report

def main():
    parser = argparse.ArgumentParser(description='Generate verification report from test results')
    parser.add_argument('--test-report', required=True, help='Path to test report HTML file')
    parser.add_argument('--coverage-report', required=True, help='Path to coverage XML report')
    parser.add_argument('--output', required=True, help='Output JSON file path')

    args = parser.parse_args()

    try:
        report = generate_verification_report(
            args.test_report,
            args.coverage_report,
            args.output
        )

        # Print summary
        print("\nVerification Report Summary:")
        print(f"Tests: {report['test_results']['total_tests']} total, "
              f"{report['test_results']['passed']} passed, "
              f"{report['test_results']['failed']} failed, "
              f"{report['test_results']['skipped']} skipped")
        print(f"Coverage: {report['coverage_data']['line_coverage']:.2f}%")
        print(f"Verification Status: {'PASSED' if report['verification_status']['passed'] else 'FAILED'}")

        if not report['verification_status']['passed']:
            sys.exit(1)

    except Exception as e:
        print(f"Error generating verification report: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
